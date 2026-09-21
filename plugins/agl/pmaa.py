
from PyQt6.QtWidgets import *
from jungle.errors import ParseError
from jungle.agl import pmaa
from jungle.db import hashes
import colors
import nodes
import plugins
import properties
import qtawesome


class PMAAWidget(properties.PropertyView):
	def __init__(self, file: pmaa.PMAAFile):
		super().__init__()
		
		self.setProperties({
			self._makeName(file.root.hash): self._makeList(file.root)
		})
	
	def _makeName(self, hash: int) -> str:
		name = hashes.crc32(hash)
		if name is None:
			return f"{hash:08x}"
		return name

	def _makeList(self, list: pmaa.ParameterList) -> properties.PropertyDict:
		props: properties.PropertyDict = {}
		for child in list.children:
			props[self._makeName(child.hash)] = self._makeList(child)
		for object in list.objects:
			objectName = self._makeName(object.hash)
			typeName = self._makeName(object.type_hash)			
			props[f"{objectName} ({typeName})"] = self._makeObject(object)
		return props

	def _makeObject(
		self, object: pmaa.ParameterObject
	) -> properties.PropertyDict:
		props = {}
		for parameter in object.parameters:
			props[self._makeName(parameter.hash)] = parameter.value
		return props


class PMAANode(nodes.File):
	_file: pmaa.PMAAFile | None

	def __init__(self, reader: nodes.Reader):
		super().__init__(reader)
		self._file = pmaa.PMAAFile()
		try:
			self._file.parse(reader.read())
		except ParseError:
			self._file = None

		self.setText(0, reader.filename())
		self.setIcon(
			0, qtawesome.icon("ri.landscape-fill", color=colors.PROPERTIES)
		)

	def createWidgets(self) -> dict[str, QWidget]:
		widgets: dict[str, QWidget] = {}
		if self._file:
			widgets["Parameters"] = PMAAWidget(self._file)
		return widgets


class PMAAPlugin:
	def analyze(self, data: bytes) -> bool:
		return data[:4] in [b"PMAA", b"AAMP"]

	def create(
		self, plugins: plugins.Plugins, reader: nodes.Reader
	) -> PMAANode:
		return PMAANode(reader)
