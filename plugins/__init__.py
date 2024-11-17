
from plugins.aal import bameta, bars, barslist
from plugins.agl import pmaa
from plugins.common import byaml
from plugins.nw import bfwav
from plugins.sead import sarc, yaz0
from plugins import zstd
import nodes
import qtawesome


class DefaultNode(nodes.File):
	def __init__(self, reader):
		super().__init__(reader)
		self.setText(0, reader.text())
		self.setIcon(0, qtawesome.icon("fa5s.file"))


class DefaultPlugin:
	def analyze(self):
		return True
	
	def create(self, plugins, reader):
		return DefaultNode(reader)


class Plugins:
	def __init__(self):
		self.plugins = [
			bameta.BAMETAPlugin(),
			bars.BARSPlugin(),
			barslist.BARSLISTPlugin(),
			bfwav.BFWAVPlugin(),
			byaml.BYAMLPlugin(),
			pmaa.PMAAPlugin(),
			sarc.SARCPlugin(),
			yaz0.Yaz0Plugin(),
			zstd.ZstdPlugin()
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
