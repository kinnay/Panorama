
from PyQt6.QtCore import *
from PyQt6.QtMultimedia import *
from PyQt6.QtWidgets import *
from jungle.errors import ParseError
from jungle.nw import bfwav
from ninty import audio
import colors
import nodes
import plugins
import properties
import qtawesome
import signals


Endianness = {
	">": "Big",
	"<": "Little"
}

SampleFormat = {
	bfwav.SampleFormat.PCM_8: "PCM-8",
	bfwav.SampleFormat.PCM_16: "PCM-16",
	bfwav.SampleFormat.ADPCM: "ADPCM"
}


def formatTime(time: int) -> str:
	hundreds = time % 100
	seconds = (time // 100) % 60
	minutes = time // 6000
	return f"{minutes}:{seconds:02}.{hundreds:02}"


def decodeChannel(file: bfwav.BFWAVFile, channel: bfwav.BFWAVChannel) -> bytes:
	if file.sample_format == bfwav.SampleFormat.PCM_8:
		return audio.decode_pcm8(channel.data)
	elif file.sample_format == bfwav.SampleFormat.ADPCM:
		return audio.decode_adpcm(
			channel.data, file.num_samples, channel.adpcm_info.coefs
		)
	return channel.data


class AudioBuffer(QIODevice):
	_data: bytes
	_loopPos: int | None
	_loopSize: int | None

	def __init__(self, data: bytes):
		super().__init__()
		self._data = data
		self._loopPos = None
		self._loopSize = None
	
	def size(self) -> int:
		return len(self._data)
	
	def setLoopPos(self, pos: int) -> None:
		self._loopPos = pos
		
		self._loopSize = None
		if self._loopPos is not None:
			self._loopSize = len(self._data) - self._loopPos
		
	def readData(self, maxSize: int) -> bytes:
		pos = self.pos()
		if self._loopPos is None or self._loopSize is None:
			data = self._data[pos : pos + maxSize]
		else:
			if pos >= len(self._data):
				pos = self._loopPos + (pos - len(self._data)) % self._loopSize
			
			data = self._data[pos : pos + maxSize]
			maxSize -= len(data)
			while maxSize > 0:
				data += self._data[self._loopPos : self._loopPos + maxSize]
				maxSize -= self._loopSize
		return data


class AudioChannel:
	stopped: signals.Signal

	_buffer: AudioBuffer
	_sink: QAudioSink

	_initialSample: int
	"""The sample at which audio play back was started."""

	_sampleRate: int
	_numSamples: int
	_loopPos: int | None
	_loopSize: int | None

	_muted: bool
	_volume: int

	def __init__(self, format: QAudioFormat, data: bytes):
		self.stopped = signals.Signal()
	
		self._buffer = AudioBuffer(data)
		self._buffer.open(QIODevice.OpenModeFlag.ReadOnly)
		
		self._sink = QAudioSink(QMediaDevices.defaultAudioOutput(), format)
		self._sink.stateChanged.connect(self._handleStateChanged)
		
		self._initialSample = 0
		
		self._sampleRate = 48000
		self._numSamples = len(data) // 2
		
		self._loopPos = None
		self._loopSize = None
		self._muted = False
		self._volume = 100
	
	def currentSample(self) -> int:
		"""Returns the current sample within the audio stream."""

		elapsedSamples = int(
			self._sink.elapsedUSecs() * self._sampleRate / 1000000
		)

		totalSamples = self._initialSample + elapsedSamples
		if totalSamples >= self._numSamples and self._loopPos is not None and \
		   self._loopSize is not None:
			totalSamples = self._loopPos + (totalSamples - self._numSamples) \
				% self._loopSize
		return totalSamples
	
	def setFormat(self, format: QAudioFormat) -> None:
		self._sampleRate = format.sampleRate()
		self._numSamples = self._buffer.size() // 2
		
		self._sink.reset()
		
		self._sink = QAudioSink(QMediaDevices.defaultAudioOutput(), format)
		self._sink.stateChanged.connect(self._handleStateChanged)
			
	def setLoopPos(self, pos: int) -> None:
		self._loopPos = pos
		
		self._loopSize = None
		if self._loopPos is not None:
			self._loopSize = self._numSamples - pos
			self._buffer.setLoopPos(pos * 2)
		else:
			self._buffer.setLoopPos(None)
		
	def setMuted(self, muted: bool) -> None:
		self._muted = muted
		self._updateVolume()
		
	def setVolume(self, volume: int) -> None:
		self._volume = volume
		self._updateVolume()
	
	def start(self, sample: int) -> None:
		self._initialSample = sample
		self._buffer.seek(sample * 2)
		self._sink.start(self._buffer)
	
	def stop(self) -> None:
		self._sink.reset()

	def _handleStateChanged(self, state: QAudio.State) -> None:
		if state == QAudio.State.IdleState:
			self.stopped.emit()
		
	def _updateVolume(self) -> None:
		if self._muted:
			self._sink.setVolume(0)
		else:
			base = 20 ** (1 / 100)
			self._sink.setVolume((base ** self._volume - 1) / 19)


class AudioPlayer:
	_format: QAudioFormat

	_channels: list[AudioChannel]
	_playing: bool
	_loopPos: int | None
	_pos: int

	def __init__(self):
		self._format = QAudioFormat()
		self._format.setChannelCount(1)
		self._format.setSampleRate(48000)
		self._format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
		
		self._channels = []
		self._playing = False
		self._loopPos = None
		self._pos = 0
	
	def setSampleRate(self, rate: int) -> None:
		if rate != self._format.sampleRate():
			self._format.setSampleRate(rate)
			for channel in self._channels:
				channel.setFormat(self._format)
	
	def addChannel(self, data: bytes) -> None:
		channel = AudioChannel(self._format, data)
		channel.setLoopPos(self._loopPos)
		channel.stopped.connect(self.stop)
		self._channels.append(channel)
	
	def setLoopPos(self, pos: int) -> None:
		self._loopPos = pos
		for channel in self._channels:
			channel.setLoopPos(pos)
	
	def setVolume(self, volume: int) -> None:
		for channel in self._channels:
			channel.setVolume(volume)
	
	def setChannelMuted(self, index: int, muted: bool) -> None:
		self._channels[index].setMuted(muted)
	
	def currentSample(self) -> int:
		if self._channels and self._playing:
			return self._channels[0].currentSample()
		return self._pos
		
	def currentTime(self) -> float:
		return self.currentSample() / self._format.sampleRate()
		
	def setCurrentSample(self, sample: int) -> None:
		self._pos = sample
	
	def setCurrentTime(self, time: float) -> None:
		self.setCurrentSample(int(time * self._format.sampleRate()))
	
	def playing(self) -> bool:
		return self._playing
	
	def play(self) -> None:
		if not self._playing:
			for channel in self._channels:
				channel.start(self._pos)
			self._playing = True
	
	def pause(self) -> None:
		if self._playing:
			self._pos = self.currentSample()
			for channel in self._channels:
				channel.stop()
			self._playing = False
			
	def stop(self) -> None:
		self._pos = 0
		if self._playing:
			for channel in self._channels:
				channel.stop()
			self._playing = False


class BFWAVPlayer(QWidget):
	_player: AudioPlayer

	_sliding: bool
	_playing: bool

	_slider: QSlider
	_currentTimeLabel: QLabel
	_volumeLabel: QLabel
	_timer: QTimer

	def __init__(self, file: bfwav.BFWAVFile):
		super().__init__()
		totalTime = int(file.num_samples / file.sample_rate * 100)

		self._player = AudioPlayer()
		self._player.setSampleRate(file.sample_rate)
		for channel in file.channels:
			data = decodeChannel(file, channel)
			self._player.addChannel(data)

		self._sliding = False
		self._playing = False

		self._slider = QSlider(Qt.Orientation.Horizontal)
		self._slider.setPageStep(0)
		self._slider.setRange(0, totalTime)
		self._slider.valueChanged.connect(self._updateTimeLabel)
		self._slider.sliderPressed.connect(self._handleSliderPressed)
		self._slider.sliderReleased.connect(self._handleSliderReleased)

		self._currentTimeLabel = QLabel("0:00.00")
		self._currentTimeLabel.setFixedWidth(60)
		self._currentTimeLabel.setAlignment(Qt.AlignmentFlag.AlignRight)

		totalTimeLabel = QLabel()
		totalTimeLabel.setText(formatTime(totalTime))

		playButton = QPushButton()
		playButton.setIcon(qtawesome.icon("fa5s.play"))
		playButton.clicked.connect(self._player.play)

		pauseButton = QPushButton()
		pauseButton.setIcon(qtawesome.icon("fa5s.pause"))
		pauseButton.clicked.connect(self._player.pause)

		stopButton = QPushButton()
		stopButton.setIcon(qtawesome.icon("fa5s.stop"))
		stopButton.clicked.connect(self._player.stop)
		
		volumeSlider = QSlider(Qt.Orientation.Horizontal)
		volumeSlider.setRange(0, 100)
		volumeSlider.setValue(100)
		volumeSlider.valueChanged.connect(self._handleVolumeChanged)

		self._volumeLabel = QLabel("100%")

		sliderLayout = QHBoxLayout()
		sliderLayout.addWidget(self._slider)
		sliderLayout.addWidget(self._currentTimeLabel)
		sliderLayout.addWidget(QLabel("/"))
		sliderLayout.addWidget(totalTimeLabel)

		buttonLayout = QHBoxLayout()
		buttonLayout.addWidget(playButton)
		buttonLayout.addWidget(pauseButton)
		buttonLayout.addWidget(stopButton)
		buttonLayout.addWidget(QLabel("Volume:"))
		buttonLayout.addWidget(volumeSlider)
		buttonLayout.addWidget(self._volumeLabel)

		channelLayout = QHBoxLayout()
		for i in range(len(file.channels)):
			box = QCheckBox()
			box.setChecked(True)
			box.setText("Channel %i" %(i + 1))
			box.toggled.connect(
				lambda state, i=i: self._handleChannelState(i, state)
			)
			channelLayout.addWidget(box)

		layout = QVBoxLayout(self)
		layout.addLayout(sliderLayout)
		layout.addLayout(buttonLayout)
		layout.addLayout(channelLayout)

		self._timer = QTimer()
		self._timer.setInterval(50)
		self._timer.timeout.connect(self._updateTime)
		self._timer.start()
	
	def _handleSliderPressed(self) -> None:
		self._playing = self._player.playing()
		self._player.pause()
		self._sliding = True
	
	def _handleSliderReleased(self) -> None:
		self._sliding = False
		self._player.setCurrentTime(self._slider.value() / 100)
		if self._playing:
			self._player.play()
	
	def _handleVolumeChanged(self, volume: int) -> None:
		self._volumeLabel.setText(f"{volume}%")
		self._player.setVolume(volume)
	
	def _handleChannelState(self, index: int, enabled: bool) -> None:
		self._player.setChannelMuted(index, not enabled)

	def _updateTime(self) -> None:
		if not self._sliding:
			self._slider.setValue(int(self._player.currentTime() * 100))

	def _updateTimeLabel(self, value: int) -> None:
		self._currentTimeLabel.setText(formatTime(value))


class BFWAVProperties(properties.PropertyView):
	def __init__(self, file: bfwav.BFWAVFile):
		super().__init__()
		self.setProperties(self._makeProperties(file))
	
	def _makeProperties(
		self, file: bfwav.BFWAVFile
	) -> properties.PropertyDict:
		props = {
			"Endianness": Endianness[file.endianness],
			"Version": f"0x{file.version:X}",
			"Sample format": SampleFormat[file.sample_format],
			"Sample rate": file.sample_rate,
			"Number of samples": file.num_samples,
			"Is looped": "Yes" if file.is_looped else "No"
		}

		if file.is_looped:
			props["Loop start sample"] = file.loop_start
			if file.version == 0x10200:
				props["Adjusted loop start sample"] = file.adjusted_loop_start
		
		if file.sample_format == bfwav.SampleFormat.ADPCM:
			channels = []
			for i, channel in enumerate(file.channels):
				channels.append(self._makeChannel(file, channel))
			props["Channels"] = channels
		
		return props
	
	def _makeChannel(
		self, file: bfwav.BFWAVFile, channel: bfwav.BFWAVChannel
	) -> properties.PropertyDict:
		props = {
			"ADPCM coefficients": channel.adpcm_info.coefs
		}

		if file.is_looped:
			props["ADPCM context (main)"] = \
				self._makeAdpcmContext(channel.adpcm_info.main_context)
			props["ADPCM context (loop)"] = \
				self._makeAdpcmContext(channel.adpcm_info.loop_context)
		else:
			props["ADPCM context"] = \
				self._makeAdpcmContext(channel.adpcm_info.main_context)
		
		return props
	
	def _makeAdpcmContext(
		self, context: bfwav.ADPCMContext
	) -> properties.PropertyDict:
		return {
			"Initial header byte": context.header,
			"Initial history byte 1": context.hist1,
			"Initial history byte 2": context.hist2
		}


class BFWAVWidget(QWidget):
	def __init__(self, file: bfwav.BFWAVFile):
		super().__init__()
		properties = BFWAVProperties(file)
		player = BFWAVPlayer(file)

		layout = QVBoxLayout(self)
		layout.addWidget(properties)
		layout.addWidget(player)


class BFWAVNode(nodes.File):
	_file: bfwav.BFWAVFile | None

	def __init__(self, reader: nodes.Reader):
		super().__init__(reader)

		self._file = bfwav.BFWAVFile()
		try:
			self._file.parse(reader.read())
		except ParseError:
			self._file = None

		self.setText(0, reader.filename())
		self.setIcon(0, qtawesome.icon("fa5s.volume-up", color=colors.AUDIO))
	
	def createWidgets(self) -> dict[str, QWidget]:
		widgets: dict[str, QWidget] = {}
		if self._file:
			widgets["BFWAV"] = BFWAVWidget(self._file)
		return widgets


class BFWAVPlugin:
	def analyze(self, data: bytes) -> bool:
		return data[:4] == b"FWAV"

	def create(
		self, plugins: plugins.Plugins, reader: nodes.Reader
	) -> BFWAVNode:
		return BFWAVNode(reader)
