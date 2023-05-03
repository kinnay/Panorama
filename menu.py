
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


class Action(QAction):
	def __init__(self, text, shortcut=None):
		super().__init__(text)
		if shortcut:
			self.setShortcut(shortcut)


class FileMenu(QMenu):
	def __init__(self):
		super().__init__("File")
		self.importFile = Action("Import File", "Ctrl+O")
		self.importFolder = Action("Import Folder", "Ctrl+Shift+O")

		self.addAction(self.importFile)
		self.addAction(self.importFolder)


class MenuBar(QMenuBar):
	def __init__(self):
		super().__init__()
		self.file = FileMenu()
        
		self.addMenu(self.file)
