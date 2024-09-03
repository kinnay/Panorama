
from jungle.errors import ParseError
from jungle.aal import barslist
import nodes
import properties
import qtawesome


class BARSLISTWidget(properties.PropertyView):
	def __init__(self, file):
		super().__init__()

		props = {
			"Endianness": "Big" if file.endianness == ">" else "Little",
			"Version": file.version,
			"Name": file.name,
			"Resources": file.resources
		}
		self.setProperties(props)


class BARSLISTNode(nodes.File):
	def __init__(self, plugins, reader):
		super().__init__(reader)
		self.plugins = plugins

		self.file = barslist.BARSLISTFile()
		try:
			self.file.parse(reader.read())
		except ParseError:
			self.file = None

		self.setText(0, reader.text())
		self.setIcon(0, qtawesome.icon("fa5s.file", color="#c00"))

	def createWidgets(self):
		widgets = {}
		if self.file:
			widgets["BARSLIST"] = BARSLISTWidget(self.file)
		return widgets


class BARSLISTPlugin:
	def analyze(self, data):
		return data[:4] == b"ARSL"

	def create(self, plugins, reader):
		return BARSLISTNode(plugins, reader)
