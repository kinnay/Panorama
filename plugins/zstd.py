
import colors
import nodes
import properties
import qtawesome
import zstd


class ZstdWidget(properties.PropertyView):
	def __init__(self, compressed, decompressed):
		super().__init__()

		self.setProperties({
			"Decompressed size": len(decompressed),
			"Compressed size": "%i (%i%%)" %(len(compressed), len(compressed) / len(decompressed) * 100)
		})


class ZstdNode(nodes.File):
	def __init__(self, plugins, reader):
		super().__init__(reader)
		self.plugins = plugins

		self.setText(0, self.reader.text())
		self.setIcon(0, qtawesome.icon("fa5s.box", color=colors.COMPRESSION))

		self.error = False
		self.compressed = None
		self.decompressed = None

		self.showIndicator(True)
	
	def decompress(self):
		if self.decompressed is None and not self.error:
			self.compressed = self.reader.read()
			try:
				self.decompressed = zstd.decompress(bytes(self.compressed))
			except zstd.Error:
				self.error = True

	def createChildren(self):
		self.decompress()

		if not self.error:
			reader = nodes.MemoryReader("Content", self.decompressed)
			self.addChild(self.plugins.create(reader))
	
	def createWidgets(self):
		self.decompress()
		if not self.error:
			return {"Zstd": ZstdWidget(self.compressed, self.decompressed)}
		return {}


class ZstdPlugin:
	def analyze(self, data):
		return data[:4] == b"\x28\xB5\x2F\xFD"

	def create(self, plugins, reader):
		return ZstdNode(plugins, reader)
