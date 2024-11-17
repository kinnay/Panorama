
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import widgets


class PropertyView(widgets.ScaledTreeWidget):
	def __init__(self, props=None):
		super().__init__()
		self.setHeaderLabels(["Field", "Value"])
		self.setAlternatingRowColors(True)

		self.setRatios([.5, .5])

		if props is not None:
			self.setProperties(props)

	def setProperties(self, props):
		self.clear()
		if isinstance(props, list):
			self.addList(props, self)
		else:
			self.addDict(props, self)
	
	def addList(self, props, parent):
		for i, value in enumerate(props):
			self.addProperty(parent, str(i), value)
	
	def addDict(self, props, parent):
		for key, value in props.items():
			self.addProperty(parent, key, value)
	
	def addProperty(self, parent, key, value):
		if isinstance(value, list):
			item = QTreeWidgetItem(parent, [key, "# %i" %len(value)])
			self.addList(value, item)
		elif isinstance(value, dict):
			item = QTreeWidgetItem(parent, [key])
			self.addDict(value, item)
		else:
			QTreeWidgetItem(parent, [key, str(value)])
