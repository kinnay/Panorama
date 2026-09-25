
from PyQt6.QtWidgets import *
from jungle.errors import ParseError
from jungle.lms import msbp
import colors
import nodes
import plugins
import properties
import qtawesome


class MSBPWidget(properties.PropertyView):
	def __init__(self, file: msbp.MSBPFile):
		super().__init__()

		props: properties.PropertyDict = {}

		if file.colors is not None:
			colors = {}
			for name, color in file.colors.items():
				colors[name] = str(color)
			props["Colors"] = colors

		if file.attributes is not None:
			attributes = {}
			for name, attribute in file.attributes.items():
				info = {
					"Type": attribute.type.name,
					"Offset": attribute.offset
				}
				if attribute.type == msbp.ValueType.Enum:
					info["Labels"] = attribute.labels
				attributes[name] = info
			props["Attributes"] = attributes

		if file.tag_groups is not None:
			tag_groups = {}
			for id, group in file.tag_groups.items():
				tags = []
				for tag in group.tags:
					parameters = []
					for parameter in tag.parameters:
						info = {
							"Name": parameter.name,
							"Type": parameter.type.name
						}
						if parameter.type == msbp.ValueType.Enum:
							info["Labels"] = parameter.labels
						parameters.append(info)
	
					tags.append({
						"Name": tag.name,
						"Parameters": parameters
					})
					
				tag_groups[id] = {
					"Name": group.name,
					"Tags": tags
				}
			props["Tag Groups"] = tag_groups

		if file.styles is not None:
			styles = {}
			for name, style in file.styles.items():
				styles[name] = {
					"Region width": style.region_width,
					"Line num": style.line_num,
					"Font index": style.font_index,
					"Base color index": style.base_color_index
				}
			props["Styles"] = styles

		if file.filenames is not None:
			props["Source files"] = file.filenames

		self.setProperties(props)


class MSBPNode(nodes.File):
	_file: msbp.MSBPFile | None

	def __init__(self, reader: nodes.Reader):
		super().__init__(reader)
		self._file = msbp.MSBPFile()
		try:
			self._file.parse(reader.read())
		except ParseError:
			self._file = None

		self.setText(0, reader.filename())
		self.setIcon(
			0, qtawesome.icon("fa6s.file-pen", color=colors.TEXT)
		)

	def createWidgets(self) -> dict[str, QWidget]:
		widgets: dict[str, QWidget] = {}
		if self._file:
			widgets["MSBP"] = MSBPWidget(self._file)
		return widgets


class MSBPPlugin:
	def analyze(self, data: bytes) -> bool:
		return data[:8] == b"MsgPrjBn"

	def create(
		self, plugins: plugins.Plugins, reader: nodes.Reader
	) -> MSBPNode:
		return MSBPNode(reader)
