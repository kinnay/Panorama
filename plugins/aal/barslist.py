
from PyQt6.QtWidgets import *
from jungle.errors import ParseError
from jungle.aal import barslist
import colors
import nodes
import plugins
import properties
import qtawesome


class BARSLISTWidget(properties.PropertyView):
	def __init__(self, file: barslist.BARSLISTFile):
		super().__init__()

		props = {
			"Endianness": "Big" if file.endianness == ">" else "Little",
			"Version": file.version,
			"Name": file.name,
			"Resources": file.resources
		}
		self.setProperties(props)


class BARSLISTNode(nodes.File):
	_file: barslist.BARSLISTFile | None

	def __init__(self, reader: nodes.Reader):
		super().__init__(reader)
		self._file = barslist.BARSLISTFile()
		try:
			self._file.parse(reader.read())
		except ParseError:
			self._file = None

		self.setText(0, reader.filename())
		self.setIcon(0, qtawesome.icon("fa5s.file", color=colors.AUDIO))

	def createWidgets(self) -> dict[str, QWidget]:
		widgets: dict[str, QWidget] = {}
		if self._file:
			widgets["BARSLIST"] = BARSLISTWidget(self._file)
		return widgets


class BARSLISTPlugin:
	def analyze(self, data: bytes) -> bool:
		return data[:4] == b"ARSL"

	def create(
		self, plugins: plugins.Plugins, reader: nodes.Reader
	) -> BARSLISTNode:
		return BARSLISTNode(reader)
