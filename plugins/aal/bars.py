
from jungle.errors import ParseError
from jungle.aal import bars, bameta
import colors
import nodes
import properties
import qtawesome


class BARSWidget(properties.PropertyView):
	def __init__(self, file):
		super().__init__()

		props = {
			"Endianness": "Big" if file.endianness == ">" else "Little",
			"File format version": "%i.%i" %(file.version >> 8, file.version & 0xFF),
			"Number of assets": len(file.assets)
		}
		self.setProperties(props)


class BARSAssetNode(nodes.Node):
	def __init__(self, plugins, hash, asset):
		super().__init__()

		metadata = bameta.BAMETAFile()
		try:
			metadata.parse(asset.metadata)
		except ParseError:
			self.setText(0, "%08x" %hash)
		else:
			self.setText(0, metadata.name)

		reader = nodes.MemoryReader("Metadata", asset.metadata)
		self.addChild(plugins.create(reader))

		if asset.data:
			reader = nodes.MemoryReader("Data", asset.data)
			self.addChild(plugins.create(reader))


class BARSNode(nodes.File):
	def __init__(self, plugins, reader):
		super().__init__(reader)
		self.plugins = plugins

		self.setText(0, reader.text())
		self.setIcon(0, qtawesome.icon("fa5s.box", color=colors.AUDIO))

		self.file = bars.BARSFile()
		try:
			self.file.parse(reader.read())
		except ParseError:
			return

		for hash, asset in self.file.assets.items():
			self.addChild(BARSAssetNode(self.plugins, hash, asset))
	
	def createWidgets(self):
		widgets = {}
		if self.file:
			widgets["BARS"] = BARSWidget(self.file)
		return widgets
	

class BARSPlugin:
	def analyze(self, data):
		return data[:4] == b"BARS"

	def create(self, plugins, reader):
		return BARSNode(plugins, reader)
