
from PyQt6.QtWidgets import *

from jungle.errors import ParseError
from jungle.sead import yaz0
from ninty.yaz0 import decompress

import colors
import nodes
import plugins
import properties
import qtawesome


class Yaz0Widget(properties.PropertyView):
	def __init__(self, file: yaz0.Yaz0File):
		super().__init__()

		ratio = len(file.data) / file.size * 100

		self.setProperties({
			"Alignment": file.alignment,
			"Decompressed size": file.size,
			"Compressed size": f"{len(file.data)} ({ratio}%)"
		})


class Yaz0Reader(nodes.Reader):
	_decompressed: bytes

	def __init__(self, file: yaz0.Yaz0File):
		self._decompressed = decompress(file.data, file.size)
	
	def filename(self) -> str:
		return "Content"
	
	def read(self) -> bytes:
		return self._decompressed


class Yaz0Node(nodes.File):
	_plugins: plugins.Plugins

	_error: bool
	_file: yaz0.Yaz0File | None

	def __init__(self, plugins: plugins.Plugins, reader: nodes.Reader):
		super().__init__(reader)
		self._plugins = plugins

		self.setText(0, self._reader.filename())
		self.setIcon(0, qtawesome.icon("fa5s.box", color=colors.COMPRESSION))

		self._error = False
		self._file = None

		self.showIndicator(True)

	def createChildren(self) -> None:
		self._loadFile()

		if self._file:
			reader = Yaz0Reader(self._file)
			self.addChild(self._plugins.create(reader))
	
	def createWidgets(self) -> dict[str, QWidget]:
		self._loadFile()
		if self._file:
			return {"Yaz0": Yaz0Widget(self._file)}
		return {}

	def _loadFile(self) -> None:
		if self._file is None and not self._error:
			try:
				self._file = yaz0.Yaz0File()
				self._file.parse(self._reader.read())
			except ParseError:
				self._file = None
				self._error = True


class Yaz0Plugin:
	def analyze(self, data: bytes) -> bool:
		return data[:4] == b"Yaz0"

	def create(
		self, plugins: plugins.Plugins, reader: nodes.Reader
	) -> Yaz0Node:
		return Yaz0Node(plugins, reader)
