
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from jungle.common import byaml
from jungle.errors import ParseError
import colors
import nodes
import qtawesome
import widgets


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
	def __init__(self, file):
		super().__init__()
		self.setHeaderLabels(["Field", "Value", "Type"])

		endianness = "Big" if file.endianness == ">" else "Little"
		QTreeWidgetItem(self, ["Endianness", endianness, ""])
		QTreeWidgetItem(self, ["Version", str(file.version), ""])
		self.createItem(self, "Root", file.root)

		self.setRatios([.4, .4, .2])
	
	def addArray(self, parent, node):
		for index, value in enumerate(node.value):
			self.createItem(parent, str(index), value)
	
	def addDictionary(self, parent, node):
		for key, value in node.value.items():
			self.createItem(parent, key, value)
	
	def addHashMap(self, parent, node):
		for key, value in node.value.items():
			self.createItem(parent, f"{key:08X}", value)
	
	def createItem(self, parent, key, node):
		if isinstance(node, byaml.BYAMLArray):
			item = QTreeWidgetItem(parent, [key, "", TypeNames[node.type()]])
			self.addArray(item, node)
		elif isinstance(node, byaml.BYAMLDict):
			item = QTreeWidgetItem(parent, [key, "", TypeNames[node.type()]])
			self.addDictionary(item, node)
		elif isinstance(node, byaml.BYAMLHashmap):
			item = QTreeWidgetItem(parent, [key, "", TypeNames[node.type()]])
			self.addHashMap(item, node)
		else:
			item = QTreeWidgetItem(
				parent, [key, str(node.value), TypeNames[node.type()]]
			)


class BYAMLNode(nodes.File):
	def __init__(self, plugins, reader):
		super().__init__(reader)
		self.plugins = plugins

		self.file = byaml.BYAMLFile()
		try:
			self.file.parse(reader.read())
		except ParseError:
			self.file = None

		self.setText(0, reader.text())
		self.setIcon(0, qtawesome.icon("fa5s.file", color=colors.PROPERTIES))

	def createWidgets(self):
		widgets = {}
		if self.file:
			widgets["BYAML"] = BYAMLWidget(self.file)
		return widgets


class BYAMLPlugin:
	def analyze(self, data):
		return data[:2] == b"BY" or data[:2] == b"YB"

	def create(self, plugins, reader):
		return BYAMLNode(plugins, reader)
