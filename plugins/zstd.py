
from PyQt6.QtWidgets import *

import colors
import nodes
import plugins
import properties
import qtawesome
import zstd


class ZstdWidget(properties.PropertyView):
	def __init__(self, compressed: bytes, decompressed: bytes):
		super().__init__()

		ratio = len(compressed) / len(decompressed) * 100

		self.setProperties({
			"Decompressed size": len(decompressed),
			"Compressed size": f"{len(compressed)} ({ratio}%)"
		})


class ZstdNode(nodes.File):
	_plugins: plugins.Plugins

	_error: bool
	_compressed: bytes | None
	_decompressed: bytes | None

	def __init__(self, plugins: plugins.Plugins, reader: nodes.Reader):
		super().__init__(reader)
		self._plugins = plugins

		self.setText(0, self._reader.filename())
		self.setIcon(0, qtawesome.icon("fa5s.box", color=colors.COMPRESSION))

		self._error = False
		self._compressed = None
		self._decompressed = None

		self.showIndicator(True)

	def createChildren(self) -> None:
		self._decompress()

		if self._decompressed is not None:
			reader = nodes.MemoryReader("Content", self._decompressed)
			self.addChild(self._plugins.create(reader))
	
	def createWidgets(self) -> dict[str, QWidget]:
		self._decompress()
		if self._compressed is not None and self._decompressed is not None:
			return {"Zstd": ZstdWidget(self._compressed, self._decompressed)}
		return {}

	def _decompress(self) -> None:
		if self._decompressed is None and not self._error:
			self._compressed = bytes(self._reader.read())
			try:
				self._decompressed = zstd.decompress(self._compressed)
			except zstd.Error:
				self._error = True


class ZstdPlugin:
	def analyze(self, data: bytes) -> bool:
		return data[:4] == b"\x28\xB5\x2F\xFD"

	def create(
		self, plugins: plugins.Plugins, reader: nodes.Reader
	) -> ZstdNode:
		return ZstdNode(plugins, reader)
