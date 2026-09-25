
from PyQt6.QtWidgets import *
from jungle.errors import ParseError
from jungle.lms import msbt
from properties import PropertyView, PropertyDict
import colors
import nodes
import plugins
import properties
import qtawesome


class MSBTWidget(PropertyView):
	def __init__(self, file: msbt.MSBTFile):
		super().__init__()

		properties = {}
		for name, message in file.messages.items():
			info: PropertyDict = {}

			text = []
			for component in message.content:
				if isinstance(component, str):
					text.append(component)
				else:
					tag = {
						"Group id": component.group,
						"Tag id": component.tag,
						"Parameters": component.parameters.hex()
					}
					text.append(tag)

			if len(text) == 1 and isinstance(text[0], str):
				info["Text"] = text[0]
			else:
				info["Text"] = text

			info["Attributes"] = message.attributes.hex()

			if message.style is not None:
				info["Style"] = message.style
			
			properties[name] = info

		self.setProperties(properties)


class MSBTNode(nodes.File):
	_file: msbt.MSBTFile | None

	def __init__(self, reader: nodes.Reader):
		super().__init__(reader)
		self._file = msbt.MSBTFile()
		try:
			self._file.parse(reader.read())
		except ParseError:
			self._file = None

		self.setText(0, reader.filename())
		self.setIcon(
			0, qtawesome.icon("fa6s.file-lines", color=colors.TEXT)
		)

	def createWidgets(self) -> dict[str, QWidget]:
		widgets: dict[str, QWidget] = {}
		if self._file:
			widgets["MSBT"] = MSBTWidget(self._file)
		return widgets


class MSBTPlugin:
	def analyze(self, data: bytes) -> bool:
		return data[:8] == b"MsgStdBn"

	def create(
		self, plugins: plugins.Plugins, reader: nodes.Reader
	) -> MSBTNode:
		return MSBTNode(reader)
