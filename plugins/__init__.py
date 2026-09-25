
from plugins.aal import bameta, bars, barslist
from plugins.agl import pmaa
from plugins.common import byaml
from plugins.lms import msbp, msbt
from plugins.nw import bfwav
from plugins.sead import sarc, yaz0
from plugins import zstd

import nodes
import qtawesome
import typing


class PluginType(typing.Protocol):
	def analyze(self, data: bytes) -> bool:
		...

	def create(self, plugins: Plugins, reader: nodes.Reader) -> nodes.Node:
		...


class DefaultNode(nodes.File):
	def __init__(self, reader: nodes.Reader):
		super().__init__(reader)
		self.setText(0, reader.filename())
		self.setIcon(0, qtawesome.icon("fa5s.file"))


class DefaultPlugin:
	"""
	This plugin is used when no other plugin is available for the file format.
	"""

	def analyze(self, data: bytes) -> bool:
		return True
	
	def create(self, plugins: Plugins, reader: nodes.Reader):
		return DefaultNode(reader)


class Plugins:
	_plugins: list[PluginType]
	_default: DefaultPlugin

	def __init__(self):
		self._plugins = [
			bameta.BAMETAPlugin(),
			bars.BARSPlugin(),
			barslist.BARSLISTPlugin(),
			bfwav.BFWAVPlugin(),
			byaml.BYAMLPlugin(),
			msbp.MSBPPlugin(),
			msbt.MSBTPlugin(),
			pmaa.PMAAPlugin(),
			sarc.SARCPlugin(),
			yaz0.Yaz0Plugin(),
			zstd.ZstdPlugin()
		]
		self._default = DefaultPlugin()
	
	def analyze(self, data: bytes) -> PluginType:
		for plugin in self._plugins:
			if plugin.analyze(data):
				return plugin
		return self._default
	
	def create(self, reader: nodes.Reader) -> nodes.Node:
		plugin = self.analyze(reader.read())
		return plugin.create(self, reader)
