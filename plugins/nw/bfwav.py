
from PyQt6.QtCore import *
from PyQt6.QtMultimedia import *
from PyQt6.QtWidgets import *
from jungle.errors import ParseError
from jungle.nw import bfwav
from ninty import audio
import colors
import nodes
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


def formatTime(time):
	hundreds = time % 100
	seconds = (time // 100) % 60
	minutes = time // 6000
	return "%i:%02i.%02i" %(minutes, seconds, hundreds)


def decodeChannel(file, channel):
	if file.sample_format == bfwav.SampleFormat.PCM_8:
		return audio.decode_pcm8(channel.data)
	elif file.sample_format == bfwav.SampleFormat.ADPCM:
		return audio.decode_adpcm(channel.data, file.num_samples, channel.adpcm_info.coefs)
	return channel.data


class AudioBuffer(QIODevice):
	def __init__(self, data):
		super().__init__()
		self.data = data
		self.loopPos = None
		self.loopSize = None
	
	def setLoopPos(self, pos):
		self.loopPos = pos
		
		self.loopSize = None
		if self.loopPos is not None:
			self.loopSize = len(self.data) - self.loopPos
		
	def readData(self, maxSize):
		pos = self.pos()
		if self.loopPos is None:
			data = self.data[pos : pos + maxSize]
		else:
			if pos >= len(self.data):
				pos = self.loopPos + (pos - len(self.data)) % self.loopSize
			
			data = self.data[pos : pos + maxSize]
			maxSize -= len(data)
			while maxSize > 0:
				data += self.data[self.loopPos : self.loopPos + maxSize]
				maxSize -= self.loopSize
		return data


class AudioChannel:
	def __init__(self, format, data):
		self.stopped = signals.Signal()
	
		self.buffer = AudioBuffer(data)
		self.buffer.open(QIODevice.OpenModeFlag.ReadOnly)
		
		self.sink = QAudioSink(QMediaDevices.defaultAudioOutput(), format)
		self.sink.stateChanged.connect(self.handleStateChanged)
		
		self.initialSample = 0
		
		self.sampleRate = 32000
		self.numSamples = len(data) // 2
		
		self.loopPos = None
		self.loopSize = None
		self.muted = False
		self.volume = 100
		
	def handleStateChanged(self, state):
		if state == QAudio.State.IdleState:
			self.stopped.emit()
	
	def currentSample(self):
		elapsedSamples = int(self.sink.elapsedUSecs() * self.sampleRate / 1000000)
		totalSamples = self.initialSample + elapsedSamples
		if totalSamples >= self.numSamples and self.loopPos is not None:
			totalSamples = self.loopPos + (totalSamples - self.numSamples) % self.loopSize
		return totalSamples
		
	def updateVolume(self):
		if self.muted:
			self.sink.setVolume(0)
		else:
			base = 20 ** (1 / 100)
			self.sink.setVolume((base ** self.volume - 1) / 19)
	
	def setFormat(self, format):
		self.sampleRate = format.sampleRate()
		self.numSamples = len(self.buffer.data) // 2
		
		self.sink.reset()
		
		self.sink = QAudioSink(QMediaDevices.defaultAudioOutput(), format)
		self.sink.stateChanged.connect(self.handleStateChanged)
			
	def setLoopPos(self, pos):
		self.loopPos = pos
		
		self.loopSize = None
		if self.loopPos is not None:
			self.loopSize = self.numSamples - pos
			self.buffer.setLoopPos(pos * 2)
		else:
			self.buffer.setLoopPos(None)
		
	def setMuted(self, muted):
		self.muted = muted
		self.updateVolume()
		
	def setVolume(self, volume):
		self.volume = volume
		self.updateVolume()
	
	def start(self, sample):
		self.initialSample = sample
		self.buffer.seek(sample * 2)
		self.sink.start(self.buffer)
	
	def stop(self):
		self.sink.reset()


class AudioPlayer:
	def __init__(self):
		self.format = QAudioFormat()
		self.format.setChannelCount(1)
		self.format.setSampleRate(32000)
		self.format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
		
		self.channels = []
		self.playing = False
		self.loopPos = None
		self.pos = 0
	
	def setSampleRate(self, rate):
		if rate != self.format.sampleRate():
			self.format.setSampleRate(rate)
			for channel in self.channels:
				channel.setFormat(self.format)
	
	def addChannel(self, data):
		channel = AudioChannel(self.format, data)
		channel.setLoopPos(self.loopPos)
		channel.stopped.connect(self.stop)
		self.channels.append(channel)
	
	def setLoopPos(self, pos):
		self.loopPos = pos
		for channel in self.channels:
			channel.setLoopPos(pos)
	
	def setVolume(self, volume):
		for channel in self.channels:
			channel.setVolume(volume)
	
	def setChannelMuted(self, index, muted):
		self.channels[index].setMuted(muted)
	
	def currentSample(self):
		if self.channels and self.playing:
			return self.channels[0].currentSample()
		return self.pos
		
	def currentTime(self):
		return self.currentSample() / self.format.sampleRate()
		
	def setCurrentSample(self, sample):
		self.pos = sample
	
	def setCurrentTime(self, time):
		self.setCurrentSample(int(time * self.format.sampleRate()))
	
	def play(self):
		if not self.playing:
			for channel in self.channels:
				channel.start(self.pos)
			self.playing = True
	
	def pause(self):
		if self.playing:
			self.pos = self.currentSample()
			for channel in self.channels:
				channel.stop()
			self.playing = False
			
	def stop(self):
		self.pos = 0
		if self.playing:
			for channel in self.channels:
				channel.stop()
			self.playing = False


class BFWAVPlayer(QWidget):
	def __init__(self, file):
		super().__init__()
		totalTime = int(file.num_samples / file.sample_rate * 100)

		self.player = AudioPlayer()
		self.player.setSampleRate(file.sample_rate)
		for channel in file.channels:
			data = decodeChannel(file, channel)
			self.player.addChannel(data)

		self.sliding = False
		self.playing = False

		self.slider = QSlider(Qt.Orientation.Horizontal)
		self.slider.setPageStep(0)
		self.slider.setRange(0, totalTime)
		self.slider.valueChanged.connect(self.updateTimeLabel)
		self.slider.sliderPressed.connect(self.handleSliderPressed)
		self.slider.sliderReleased.connect(self.handleSliderReleased)

		self.currentTimeLabel = QLabel("0:00.00")
		self.currentTimeLabel.setFixedWidth(60)
		self.currentTimeLabel.setAlignment(Qt.AlignmentFlag.AlignRight)

		totalTimeLabel = QLabel()
		totalTimeLabel.setText(formatTime(totalTime))

		playButton = QPushButton()
		playButton.setIcon(qtawesome.icon("fa5s.play"))
		playButton.clicked.connect(self.player.play)

		pauseButton = QPushButton()
		pauseButton.setIcon(qtawesome.icon("fa5s.pause"))
		pauseButton.clicked.connect(self.player.pause)

		stopButton = QPushButton()
		stopButton.setIcon(qtawesome.icon("fa5s.stop"))
		stopButton.clicked.connect(self.player.stop)
		
		volumeSlider = QSlider(Qt.Orientation.Horizontal)
		volumeSlider.setRange(0, 100)
		volumeSlider.setValue(100)
		volumeSlider.valueChanged.connect(self.handleVolumeChanged)

		self.volumeLabel = QLabel("100%")

		sliderLayout = QHBoxLayout()
		sliderLayout.addWidget(self.slider)
		sliderLayout.addWidget(self.currentTimeLabel)
		sliderLayout.addWidget(QLabel("/"))
		sliderLayout.addWidget(totalTimeLabel)

		buttonLayout = QHBoxLayout()
		buttonLayout.addWidget(playButton)
		buttonLayout.addWidget(pauseButton)
		buttonLayout.addWidget(stopButton)
		buttonLayout.addWidget(QLabel("Volume:"))
		buttonLayout.addWidget(volumeSlider)
		buttonLayout.addWidget(self.volumeLabel)

		channelLayout = QHBoxLayout()
		for i in range(len(file.channels)):
			box = QCheckBox()
			box.setChecked(True)
			box.setText("Channel %i" %(i + 1))
			box.toggled.connect(lambda state, i=i: self.handleChannelState(i, state))
			channelLayout.addWidget(box)

		layout = QVBoxLayout(self)
		layout.addLayout(sliderLayout)
		layout.addLayout(buttonLayout)
		layout.addLayout(channelLayout)

		self.timer = QTimer()
		self.timer.setInterval(50)
		self.timer.timeout.connect(self.updateTime)
		self.timer.start()
	
	def handleSliderPressed(self):
		self.playing = self.player.playing
		self.player.pause()
		self.sliding = True
	
	def handleSliderReleased(self):
		self.sliding = False
		self.player.setCurrentTime(self.slider.value() / 100)
		if self.playing:
			self.player.play()
	
	def handleVolumeChanged(self, volume):
		self.volumeLabel.setText("%i%%" %volume)
		self.player.setVolume(volume)
	
	def handleChannelState(self, index, enabled):
		self.player.setChannelMuted(index, not enabled)

	def updateTime(self):
		if not self.sliding:
			self.slider.setValue(int(self.player.currentTime() * 100))

	def updateTimeLabel(self, value):
		self.currentTimeLabel.setText(formatTime(value))



class BFWAVProperties(properties.PropertyView):
	def __init__(self, file):
		super().__init__()
		self.setProperties(self.makeProperties(file))
	
	def makeProperties(self, file):
		props = {
			"Endianness": Endianness[file.endianness],
			"Version": "0x%X" %file.version,
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
				channels.append(self.makeChannel(file, channel))
			props["Channels"] = channels
		
		return props
	
	def makeChannel(self, file, channel):
		props = {
			"ADPCM coefficients": channel.adpcm_info.coefs
		}

		if file.is_looped:
			props["ADPCM context (main)"] = self.makeAdpcmContext(channel.adpcm_info.main_context)
			props["ADPCM context (loop)"] = self.makeAdpcmContext(channel.adpcm_info.loop_context)
		else:
			props["ADPCM context"] = self.makeAdpcmContext(channel.adpcm_info.main_context)
		return props
	
	def makeAdpcmContext(self, context):
		return {
			"Initial header byte": context.header,
			"Initial history byte 1": context.hist1,
			"Initial history byte 2": context.hist2
		}


class BFWAVWidget(QWidget):
	def __init__(self, file):
		super().__init__()
		self.file = file

		self.properties = BFWAVProperties(file)
		self.player = BFWAVPlayer(file)

		self.layout = QVBoxLayout(self)
		self.layout.addWidget(self.properties)
		self.layout.addWidget(self.player)


class BFWAVNode(nodes.File):
	def __init__(self, plugins, reader):
		super().__init__(reader)
		self.plugins = plugins

		self.file = bfwav.BFWAVFile()
		try:
			self.file.parse(reader.read())
		except ParseError:
			self.file = None

		self.setText(0, reader.text())
		self.setIcon(0, qtawesome.icon("fa5s.volume-up", color=colors.AUDIO))
	
	def createWidgets(self):
		widgets = {}
		if self.file:
			widgets["BFWAV"] = BFWAVWidget(self.file)
		return widgets


class BFWAVPlugin:
	def analyze(self, data):
		return data[:4] == b"FWAV"

	def create(self, plugins, reader):
		return BFWAVNode(plugins, reader)
