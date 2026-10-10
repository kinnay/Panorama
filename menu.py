
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


class FileMenu(QMenu):
    importFile: QAction
    importfolder: QAction
    reloadWorkspace: QAction

    def __init__(self):
        super().__init__("File")
        self.importFile = QAction("Import File")
        self.importFile.setShortcut("Ctrl+O")

        self.importFolder = QAction("Import Folder")
        self.importFolder.setShortcut("Ctrl+Shift+O")

        self.reloadWorkspace = QAction("Reload Workspace")
        self.reloadWorkspace.setShortcut("Ctrl+F5")

        self.addAction(self.importFile)
        self.addAction(self.importFolder)
        self.addAction(self.reloadWorkspace)


class WindowMenu(QMenu):
    minimize: QAction

    def __init__(self):
        super().__init__("Window")
        self.minimize = QAction("Minimize")
        self.minimize.setShortcut("Ctrl+M")

        self.addAction(self.minimize)


class MenuBar(QMenuBar):
    file: FileMenu
    window: WindowMenu

    def __init__(self):
        super().__init__()
        self.file = FileMenu()
        self.window = WindowMenu()
        
        self.addMenu(self.file)
        self.addMenu(self.window)
