
from PyQt6.QtCore import *
from PyQt6.QtGui import *
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


class Action(QAction):
	def __init__(self, text, callback):
		super().__init__(text)
		self.triggered.connect(callback)


class WorkspaceView(QTreeWidget):
	"""The workspace tree."""

	def __init__(self, plugins, settings):
		super().__init__()
		self.plugins = plugins
		self.settings = settings

		self.setHeaderHidden(True)
		self.setSortingEnabled(True)
		self.sortByColumn(0, Qt.SortOrder.AscendingOrder)

		self.itemExpanded.connect(self.handleItemExpanded)

	def contextMenuEvent(self, e):
		menu = QMenu(self)

		item = self.itemAt(e.pos())
		if isinstance(item, nodes.File):
			extract = Action("Extract", lambda: self.handleExtract(item))
			menu.addAction(extract)

		if not menu.isEmpty():
			menu.exec(e.globalPos())

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
	
	def handleExtract(self, item):
		default = os.path.join(self.settings.value("filesystem.extract_path"), item.text(0))
		print(default)

		path, filter = QFileDialog.getSaveFileName(
			self, "Extract file", default, "All files (*.*)"
		)
		if path:
			self.settings.setValue("filesystem.extract_path", os.path.dirname(path))
			with open(path, "wb") as f:
				f.write(item.read())
