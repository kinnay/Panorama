
from jungle.sead import yaz0
from ninty.yaz0 import decompress
import nodes
import qtawesome


class Yaz0Reader(nodes.Reader):
	def __init__(self, file):
		self.decompressed = decompress(file.data, file.size)
	
	def text(self):
		return "Content"
	
	def read(self):
		return self.decompressed


class Yaz0Node(nodes.File):
	def __init__(self, plugins, reader):
		super().__init__()
		self.plugins = plugins
		self.reader = reader

		self.setText(0, self.reader.text())
		self.setIcon(0, qtawesome.icon("fa5s.box", color="#888"))

		self.showIndicator(True)
	
	def read(self):
		return self.reader.read()

	def createChildren(self):
		file = yaz0.Yaz0File()
		file.parse(self.reader.read())
		reader = Yaz0Reader(file)
		self.addChild(self.plugins.create(reader))


class Yaz0Plugin:
	def analyze(self, data):
		return data[:4] == b"Yaz0"

	def create(self, plugins, reader):
		return Yaz0Node(plugins, reader)
