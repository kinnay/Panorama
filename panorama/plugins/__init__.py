
from panorama import nodes
from panorama.plugins import image, zstd
from panorama.plugins.aal import baatn, bameta, baroc, bars, barslist
from panorama.plugins.agl import pmaa
from panorama.plugins.common import byaml
from panorama.plugins.dkctf import genp, pak, txtr
from panorama.plugins.gfd import gfx2
from panorama.plugins.lms import msbp, msbt
from panorama.plugins.nw import bflim, bfwav
from panorama.plugins.sead import sarc, yaz0
from panorama.plugins.switch import bdf

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
			baatn.BAATNPlugin(),
			bameta.BAMETAPlugin(),
			baroc.BAROCPlugin(),
			bars.BARSPlugin(),
			barslist.BARSLISTPlugin(),
			bdf.BDFPlugin(),
			bflim.BFLIMPlugin(),
			bfwav.BFWAVPlugin(),
			byaml.BYAMLPlugin(),
			gfx2.Gfx2Plugin(),
			msbp.MSBPPlugin(),
			msbt.MSBTPlugin(),
			pmaa.PMAAPlugin(),
			sarc.SARCPlugin(),
			yaz0.Yaz0Plugin(),
			zstd.ZstdPlugin(),

			genp.GENPPlugin(),
			pak.PAKPlugin(),
			txtr.TXTRPlugin(),

			image.ImagePlugin(),
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
