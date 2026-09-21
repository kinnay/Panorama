
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


class Action(QAction):
	def __init__(self, text: str, shortcut: str | None = None):
		super().__init__(text)
		if shortcut:
			self.setShortcut(shortcut)


class FileMenu(QMenu):
	importFile: Action
	importfolder: Action
	reloadWorkspace: Action

	def __init__(self):
		super().__init__("File")
		self.importFile = Action("Import File", "Ctrl+O")
		self.importFolder = Action("Import Folder", "Ctrl+Shift+O")
		self.reloadWorkspace = Action("Reload Workspace", "Ctrl+F5")

		self.addAction(self.importFile)
		self.addAction(self.importFolder)
		self.addAction(self.reloadWorkspace)


class MenuBar(QMenuBar):
	file: FileMenu

	def __init__(self):
		super().__init__()
		self.file = FileMenu()
        
		self.addMenu(self.file)
