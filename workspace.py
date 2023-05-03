
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
import filesystem
import nodes
import os
import qtawesome


class InvalidItem(nodes.Node):
	def __init__(self, path):
		super().__init__()
		self.path = path
		self.setText(0, os.path.basename(path))
		self.setIcon(0, qtawesome.icon("fa5s.ban", color="red"))


class WorkspaceView(QTreeWidget):
	"""The workspace tree."""

	def __init__(self, plugins):
		super().__init__()
		self.plugins = plugins

		self.setHeaderHidden(True)
		self.setSortingEnabled(True)
		self.sortByColumn(0, Qt.SortOrder.AscendingOrder)

		self.itemExpanded.connect(self.handleItemExpanded)
	
	def addPath(self, path):
		if os.path.isdir(path):
			self.addTopLevelItem(filesystem.Folder(self.plugins, path))
		elif os.path.isfile(path):
			reader = filesystem.FileReader(path)
			self.addTopLevelItem(self.plugins.create(reader))
		elif os.path.exists(path):
			self.addTopLevelItem(filesystem.Other(path))
		else:
			self.addTopLevelItem(InvalidItem(path))

	def handleItemExpanded(self, item):
		# In case the item creates its children lazily,
		# create them now.
		item.expand()
