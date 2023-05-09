
from plugins import bamta, bars, bfwav, pmaa, sarc, yaz0
import nodes
import qtawesome


class DefaultNode(nodes.File):
	def __init__(self, reader):
		super().__init__()
		self.reader = reader

		self.setText(0, reader.text())
		self.setIcon(0, qtawesome.icon("fa5s.file"))
	
	def read(self):
		return self.reader.read()


class DefaultPlugin:
	def analyze(self):
		return True
	
	def create(self, plugins, reader):
		return DefaultNode(reader)


class Plugins:
	def __init__(self):
		self.plugins = [
			bamta.BAMTAPlugin(),
			bars.BARSPlugin(),
			bfwav.BFWAVPlugin(),
			pmaa.PMAAPlugin(),
			sarc.SARCPlugin(),
			yaz0.Yaz0Plugin()
		]
		self.default = DefaultPlugin()
	
	def analyze(self, data):
		for plugin in self.plugins:
			if plugin.analyze(data):
				return plugin
		return self.default
	
	def create(self, reader):
		plugin = self.analyze(reader.read())
		return plugin.create(self, reader)
