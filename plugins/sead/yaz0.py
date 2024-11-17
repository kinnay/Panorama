
from jungle.errors import ParseError
from jungle.sead import yaz0
from ninty.yaz0 import decompress
import colors
import nodes
import properties
import qtawesome


class Yaz0Widget(properties.PropertyView):
	def __init__(self, file):
		super().__init__()

		self.setProperties({
			"Alignment": file.alignment,
			"Decompressed size": file.size,
			"Compressed size": "%i (%i%%)" %(len(file.data), len(file.data) / file.size * 100),
		})


class Yaz0Reader(nodes.Reader):
	def __init__(self, file):
		self.decompressed = decompress(file.data, file.size)
	
	def text(self):
		return "Content"
	
	def read(self):
		return self.decompressed


class Yaz0Node(nodes.File):
	def __init__(self, plugins, reader):
		super().__init__(reader)
		self.plugins = plugins

		self.setText(0, self.reader.text())
		self.setIcon(0, qtawesome.icon("fa5s.box", color=colors.COMPRESSION))

		self.error = False
		self.file = None

		self.showIndicator(True)
	
	def loadFile(self):
		if self.file is None and not self.error:
			try:
				self.file = yaz0.Yaz0File()
				self.file.parse(self.reader.read())
			except ParseError:
				self.file = None
				self.error = True

	def createChildren(self):
		self.loadFile()

		if self.file:
			reader = Yaz0Reader(self.file)
			self.addChild(self.plugins.create(reader))
	
	def createWidgets(self):
		self.loadFile()
		if self.file:
			return {"Yaz0": Yaz0Widget(self.file)}
		return {}


class Yaz0Plugin:
	def analyze(self, data):
		return data[:4] == b"Yaz0"

	def create(self, plugins, reader):
		return Yaz0Node(plugins, reader)
