
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from plugins import Plugins
from typing import Callable

import filesystem
import nodes
import os
import qtawesome
import signals


class InvalidItem(nodes.Node):
	"""
	This item represents a file or folder in the workspace that no longer
	exists. This happens if the file or folder was deleted, moved, or its
	storage device is no longer available.
	"""

	_path: str

	def __init__(self, path: str):
		super().__init__()
		self._path = path

		self.setText(0, os.path.basename(path))
		self.setIcon(0, qtawesome.icon("fa5s.ban", color="red"))

	def path(self) -> str:
		return self._path


class Action(QAction):
	def __init__(self, text: str, callback: Callable[[], None]):
		super().__init__(text)
		self.triggered.connect(callback)


class WorkspaceView(QTreeWidget):
	"""The workspace tree."""

	itemRemoved: signals.Signal[str]

	_plugins: Plugins
	_settings: QSettings

	def __init__(self, plugins: Plugins, settings: QSettings):
		super().__init__()
		self._plugins = plugins
		self._settings = settings

		self.setHeaderHidden(True)
		self.setSortingEnabled(True)
		self.sortByColumn(0, Qt.SortOrder.AscendingOrder)

		self.itemExpanded.connect(self._handleItemExpanded)

		self.itemRemoved = signals.Signal()

	def contextMenuEvent(self, e: QContextMenuEvent) -> None:
		menu = QMenu(self)

		item = self.itemAt(e.pos())

		if item and item.parent() is None:
			remove = Action("Remove", lambda: self.handleRemove(item))
			menu.addAction(remove)
		
		if isinstance(item, nodes.File):
			extract = Action("Extract", lambda: self.handleExtract(item))
			menu.addAction(extract)

		if not menu.isEmpty():
			menu.exec(e.globalPos())

	def addPath(self, path: str) -> None:
		if os.path.isdir(path):
			self.addTopLevelItem(filesystem.Folder(self._plugins, path))
		elif os.path.isfile(path):
			reader = filesystem.FileReader(path)
			self.addTopLevelItem(self._plugins.create(reader))
		elif os.path.exists(path):
			self.addTopLevelItem(filesystem.Other(path))
		else:
			self.addTopLevelItem(InvalidItem(path))

	def _handleItemExpanded(self, item: nodes.Node) -> None:
		# In case the item creates its children lazily, create them now.
		item.expand()
	
	def handleRemove(self, item: QTreeWidgetItem) -> None:
		index = self.indexOfTopLevelItem(item)
		self.takeTopLevelItem(index)

		if isinstance(item, filesystem.Folder):
			self.itemRemoved.emit(item.path())
		elif isinstance(item, nodes.File):
			reader = item.reader()
			if isinstance(reader, filesystem.FileReader):
				self.itemRemoved.emit(reader.path())
		elif isinstance(item, filesystem.Other):
			self.itemRemoved.emit(item.path())
		elif isinstance(item, InvalidItem):
			self.itemRemoved.emit(item.path())

	def handleExtract(self, item: nodes.File) -> None:
		default = os.path.join(
			self._settings.value("filesystem.extract_path", ""), item.text(0)
		)
		
		path, filter = QFileDialog.getSaveFileName(
			self, "Extract file", default, "All files (*.*)"
		)
		if path:
			self._settings.setValue(
				"filesystem.extract_path", os.path.dirname(path)
			)
			with open(path, "wb") as f:
				f.write(item.read())
