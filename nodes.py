
from PyQt6.QtWidgets import *


class Node(QTreeWidgetItem):
	def __init__(self):
		super().__init__()
		self.childrenCreated = False
	
	def __lt__(self, other):
		if self.priority() < other.priority():
			return True
		if self.priority() > other.priority():
			return False
		return super().__lt__(other)

	def priority(self):
		return 0

	def showIndicator(self, shown):
		if shown:
			self.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
		else:
			self.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicatorWhenChildless)

	def expand(self):
		if not self.childrenCreated:
			self.createChildren()
			self.childrenCreated = True
	
	def createChildren(self):
		pass

	def createWidgets(self):
		return {}


class File(Node):
	def __init__(self, reader):
		super().__init__()
		self.reader = reader

	def read(self):
		return self.reader.read()


class Reader:
	def text(self):
		return ""
	
	def read(self):
		return b""


class MemoryReader(Reader):
	def __init__(self, text, data):
		self._text = text
		self._data = data
	
	def text(self):
		return self._text

	def read(self):
		return self._data
