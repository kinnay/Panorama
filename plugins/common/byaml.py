
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from jungle.common import byaml
from jungle.errors import ParseError
import colors
import nodes
import qtawesome
import widgets


TypeNames = {
	byaml.NodeType.HASHMAP: "Hash",
	byaml.NodeType.STRING: "String",
	byaml.NodeType.BINARY: "Binary",
	byaml.NodeType.ARRAY: "Array",
	byaml.NodeType.DICT: "Dict",
	byaml.NodeType.BOOL: "Bool",
	byaml.NodeType.INT: "Int",
	byaml.NodeType.FLOAT: "Float",
	byaml.NodeType.UINT: "UInt",
	byaml.NodeType.INT64: "Int64",
	byaml.NodeType.UINT64: "UInt64",
	byaml.NodeType.DOUBLE: "Double",
	byaml.NodeType.NULL: "Null"
}


class BYAMLWidget(widgets.ScaledTreeWidget):
	def __init__(self, file):
		super().__init__()
		self.setHeaderLabels(["Field", "Value", "Type"])

		QTreeWidgetItem(self, ["Endianness", "Big" if file.endianness == ">" else "Little", ""])
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
			self.createItem(parent, "%08x" %key, value)
	
	def createItem(self, parent, key, node):
		if node.type == byaml.NodeType.ARRAY:
			item = QTreeWidgetItem(parent, [key, "", TypeNames[node.type]])
			self.addArray(item, node)
		elif node.type == byaml.NodeType.DICT:
			item = QTreeWidgetItem(parent, [key, "", TypeNames[node.type]])
			self.addDictionary(item, node)
		elif node.type == byaml.NodeType.HASHMAP:
			item = QTreeWidgetItem(parent, [key, "", TypeNames[node.type]])
			self.addHashMap(item, node)
		else:
			item = QTreeWidgetItem(parent, [key, str(node.value), TypeNames[node.type]])


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
