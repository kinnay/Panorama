
from jungle.errors import ParseError
from jungle.aal import bameta
import colors
import nodes
import properties
import qtawesome


AssetTypes = {
	bameta.AssetType.WAVE: "Wave",
	bameta.AssetType.STREAM: "Stream"
}


class BAMETAWidget(properties.PropertyView):
	def __init__(self, file):
		super().__init__()

		self.ext = []

		props = {
			"Endianness": "Big" if file.endianness == ">" else "Little",
			"Version": "0x%X" %file.version,
			"Name": file.name,
			"Type:": AssetTypes[file.type],
			"Number of channels": file.num_channels,
			"Number of samples": file.num_samples,
			"Number of samples (48000 Hz)": file.num_output_samples,
			"Sample rate": file.sample_rate,
			"Is looped": "Yes" if file.flags & bameta.Flags.LOOPED else "No"
		}

		if file.flags & bameta.Flags.LOOPED:
			props["Loop start sample"] = file.loop_start
		
		props["Unknown flag 1"] = "Yes" if file.flags & 1 else "No"
		props["Unknown flag 2"] = "Yes" if file.flags & 2 else "No"
		props["Unknown flag 8"] = "Yes" if file.flags & 8 else "No"
		props["Unknown flag 16"] = "Yes" if file.flags & 16 else "No"

		props["Unknown"] = file.unk2
		props["Volume (decibel)"] = file.decibel
		props["Amplitude peak"] = file.amplitude_peak

		if file.stream_tracks:
			tracks = []
			for track in file.stream_tracks:
				tracks.append({
					"Number of channels": track.channels,
					"Volume": track.volume
				})
			props["Stream tracks"] = tracks
		
		markers = []
		for marker in file.markers:
			markers.append({
				"Id": marker.id,
				"Name": marker.name,
				"Start sample": marker.start,
				"Length": marker.length
			})
		props["Markers"] = markers

		exts = []
		for ext in file.ext:
			exts.append({
				"Name": ext.name,
				"Value": ext.value
			})
		props["Ext"] = exts

		self.setProperties(props)


class BAMETANode(nodes.File):
	def __init__(self, plugins, reader):
		super().__init__(reader)
		self.plugins = plugins

		self.file = bameta.BAMETAFile()
		try:
			self.file.parse(reader.read())
		except ParseError:
			self.file = None

		self.setText(0, reader.text())
		self.setIcon(0, qtawesome.icon("fa5s.file", color=colors.AUDIO))

	def createWidgets(self):
		widgets = {}
		if self.file:
			widgets["Metadata"] = BAMETAWidget(self.file)
		return widgets


class BAMETAPlugin:
	def analyze(self, data):
		return data[:4] == b"AMTA"

	def create(self, plugins, reader):
		return BAMETANode(plugins, reader)
