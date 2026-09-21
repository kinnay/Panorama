
from PyQt6.QtWidgets import *

from jungle.errors import ParseError
from jungle.aal import bars, bameta

import colors
import nodes
import plugins
import properties
import qtawesome


class BARSWidget(properties.PropertyView):
	def __init__(self, file: bars.BARSFile):
		super().__init__()

		props: properties.PropertyDict = {
			"Endianness": "Big" if file.endianness == ">" else "Little",
			"File format version": f"{file.version >> 8}.{file.version & 0xFF}",
			"Number of assets": len(file.assets)
		}
		self.setProperties(props)


class BARSAssetNode(nodes.Node):
	def __init__(self, plugins: plugins.Plugins, hash: int, asset: bars.Asset):
		super().__init__()

		metadata = bameta.BAMETAFile()
		try:
			metadata.parse(asset.metadata)
		except ParseError:
			self.setText(0, f"{hash:08x}")
		else:
			self.setText(0, metadata.name)

		reader = nodes.MemoryReader("Metadata", asset.metadata)
		self.addChild(plugins.create(reader))

		if asset.data:
			reader = nodes.MemoryReader("Data", asset.data)
			self.addChild(plugins.create(reader))


class BARSNode(nodes.File):
	_file: bars.BARSFile | None

	def __init__(self, plugins, reader):
		super().__init__(reader)
		self.setText(0, reader.filename())
		self.setIcon(0, qtawesome.icon("fa5s.box", color=colors.AUDIO))

		self._file = bars.BARSFile()
		try:
			self._file.parse(reader.read())
		except ParseError:
			self._file = None
			return

		for hash, asset in self._file.assets.items():
			self.addChild(BARSAssetNode(plugins, hash, asset))
	
	def createWidgets(self) -> dict[str, QWidget]:
		widgets: dict[str, QWidget] = {}
		if self._file:
			widgets["BARS"] = BARSWidget(self._file)
		return widgets
	

class BARSPlugin:
	def analyze(self, data: bytes) -> bool:
		return data[:4] == b"BARS"

	def create(
		self, plugins: plugins.Plugins, reader: nodes.Reader
	) -> BARSNode:
		return BARSNode(plugins, reader)
