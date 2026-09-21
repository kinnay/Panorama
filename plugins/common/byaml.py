
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from jungle.common import byaml
from jungle.errors import ParseError
import colors
import nodes
import plugins
import qtawesome
import widgets


type ParentItem = QTreeWidget | QTreeWidgetItem


TypeNames = {
	byaml.BYAMLNodeType.HASHMAP: "Hash",
	byaml.BYAMLNodeType.STRING: "String",
	byaml.BYAMLNodeType.BINARY: "Binary",
	byaml.BYAMLNodeType.ARRAY: "Array",
	byaml.BYAMLNodeType.DICT: "Dict",
	byaml.BYAMLNodeType.BOOL: "Bool",
	byaml.BYAMLNodeType.INT: "Int",
	byaml.BYAMLNodeType.FLOAT: "Float",
	byaml.BYAMLNodeType.UINT: "UInt",
	byaml.BYAMLNodeType.INT64: "Int64",
	byaml.BYAMLNodeType.UINT64: "UInt64",
	byaml.BYAMLNodeType.DOUBLE: "Double",
	byaml.BYAMLNodeType.NULL: "Null"
}


class BYAMLWidget(widgets.ScaledTreeWidget):
	def __init__(self, file: byaml.BYAMLFile):
		super().__init__()
		self.setHeaderLabels(["Field", "Value", "Type"])

		endianness = "Big" if file.endianness == ">" else "Little"
		QTreeWidgetItem(self, ["Endianness", endianness, ""])
		QTreeWidgetItem(self, ["Version", str(file.version), ""])
		self._createItem(self, "Root", file.root)

		self.setRatios([.4, .4, .2])
	
	def _addArray(self, parent: ParentItem, node: byaml.BYAMLArray) -> None:
		for index, value in enumerate(node.value):
			self._createItem(parent, str(index), value)
	
	def _addDictionary(self, parent: ParentItem, node: byaml.BYAMLDict) -> None:
		for key, value in node.value.items():
			self._createItem(parent, key, value)
	
	def _addHashMap(self, parent: ParentItem, node: byaml.BYAMLHashmap) -> None:
		for key, value in node.value.items():
			self._createItem(parent, f"{key:08X}", value)
	
	def _createItem(
		self, parent: ParentItem, key: str, node: byaml.BYAMLNode
	) -> None:
		typename = TypeNames[node.type()]
		if isinstance(node, byaml.BYAMLArray):
			item = QTreeWidgetItem(parent, [key, "", typename])
			self._addArray(item, node)
		elif isinstance(node, byaml.BYAMLDict):
			item = QTreeWidgetItem(parent, [key, "", typename])
			self._addDictionary(item, node)
		elif isinstance(node, byaml.BYAMLHashmap):
			item = QTreeWidgetItem(parent, [key, "", typename])
			self._addHashMap(item, node)
		elif isinstance(node, (
			byaml.BYAMLNone, byaml.BYAMLBool, byaml.BYAMLInt, byaml.BYAMLUint,
			byaml.BYAMLInt64, byaml.BYAMLUint64, byaml.BYAMLFloat,
			byaml.BYAMLDouble, byaml.BYAMLString
		)):
			item = QTreeWidgetItem(parent, [key, str(node.value), typename])
		else:
			raise TypeError(f"Unsupported BYAML node type: {typename}")


class BYAMLNode(nodes.File):
	_file: byaml.BYAMLFile | None

	def __init__(self, reader: nodes.Reader):
		super().__init__(reader)
		self._file = byaml.BYAMLFile()
		try:
			self._file.parse(reader.read())
		except ParseError:
			self._file = None

		self.setText(0, reader.filename())
		self.setIcon(0, qtawesome.icon("fa5s.file", color=colors.PROPERTIES))

	def createWidgets(self) -> dict[str, QWidget]:
		widgets: dict[str, QWidget] = {}
		if self._file:
			widgets["BYAML"] = BYAMLWidget(self._file)
		return widgets


class BYAMLPlugin:
	def analyze(self, data: bytes) -> bool:
		return data[:2] == b"BY" or data[:2] == b"YB"

	def create(
		self, plugins: plugins.Plugins, reader: nodes.Reader
	) -> BYAMLNode:
		return BYAMLNode(reader)
