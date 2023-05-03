
from PyQt6.QtWidgets import *


class Node(QTreeWidgetItem):
	def __init__(self):
		super().__init__()
		self.childrenCreated = False
	
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
	def read(self):
		return b""


class Reader:
	def text(self):
		return ""
	
	def read(self):
		return b""
