
"""
Panorama is a program that is designed to view various file formats
that are seen in Nintendo games.
"""

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
import psutil
import string
import sys

import binary
import menu
import nodes
import plugins
import text
import utils
import workspace


class StatusBar(QStatusBar):
	"""A simple status bar that displays the memory usage of the program."""
	
	def __init__(self):
		super().__init__()
		self.text = QLabel()
		self.addPermanentWidget(self.text)

		self.timer = QTimer()
		self.timer.setInterval(500)
		self.timer.timeout.connect(self.updateStatus)
		self.timer.start()
		self.updateStatus()
	
	def updateStatus(self):
		process = psutil.Process()
		memory = "Memory usage: %s" %utils.formatSize(process.memory_info().rss)
		self.text.setText(memory)


class MainWindow(QMainWindow):
	"""The main window of the program."""

	def __init__(self, settings):
		super().__init__()
		self.settings = settings

		# Initialize general variables
		self.plugins = plugins.Plugins()
		self.unsaved = False

		# Initialize various components
		self.initializeGeometry()
		self.initializeMenuBar()
		self.initializeStatusBar()
		self.initializeWorkspace()
		
		self.setCentralWidget(QWidget())
		self.setWindowTitle("Panorama")

	def initializeGeometry(self):
		"""Restores the window to its previous geometry."""

		geometry = self.settings.value("window.geometry")
		if geometry:
			self.restoreGeometry(geometry)
		else:
			screen = self.screen().size()
			self.setGeometry(
				screen.width() // 4, screen.height() // 4,
				screen.width() // 2, screen.height() // 2
			)

	def initializeMenuBar(self):
		self.menu = menu.MenuBar()
		self.menu.file.importFile.triggered.connect(self.handleImportFile)
		self.menu.file.importFolder.triggered.connect(self.handleImportFolder)
		self.menu.file.reloadWorkspace.triggered.connect(self.handleReloadWorkspace)
		self.setMenuBar(self.menu)

	def initializeStatusBar(self):
		self.statusBar = StatusBar()
		self.setStatusBar(self.statusBar)

	def initializeWorkspace(self):
		self.workspaceView = workspace.WorkspaceView(self.plugins, self.settings)
		self.workspaceView.itemActivated.connect(self.handleItemActivated)

		self.workspacePaths = self.settings.value("workspace.paths", [])
		for path in self.workspacePaths:
			self.workspaceView.addPath(path)

		self.workspaceDock = QDockWidget("Workspace")
		self.workspaceDock.setObjectName("workspace")
		self.workspaceDock.setWidget(self.workspaceView)
		self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.workspaceDock)

		self.restoreState(self.settings.value("window.state", b""))

	def closeEvent(self, e):
		self.settings.setValue("window.geometry", self.saveGeometry())
		self.settings.setValue("window.state", self.saveState())
		
	def handleImportFile(self):
		path, filter = QFileDialog.getOpenFileName(
			self, "Import file", self.settings.value("filesystem.import_path"),
			"All files (*.*)"
		)
		if path and path not in self.workspacePaths:
			self.workspacePaths.append(path)
			self.settings.setValue("workspace.paths", self.workspacePaths)
			self.settings.setValue("filesystem.import_path", path)
			self.workspaceView.addPath(path)

	def handleImportFolder(self):
		dir = QFileDialog.getExistingDirectory(
			self, "Import Folder", self.settings.value("filesystem.import_path")
		)
		if dir and dir not in self.workspacePaths:
			self.workspacePaths.append(dir)
			self.settings.setValue("workspace.paths", self.workspacePaths)
			self.settings.setValue("filesystem.import_path", dir)
			self.workspaceView.addPath(dir)
	
	def handleReloadWorkspace(self):
		self.workspaceView.clear()
		for path in self.workspacePaths:
			self.workspaceView.addPath(path)

	def handleItemActivated(self, item):
		widgets = item.createWidgets()
		if isinstance(item, nodes.File):
			data = item.read()
			if isinstance(data, bytes) and all(chr(c) in string.printable for c in data):
				widgets["Text"] = text.TextWidget(data.decode())
			widgets["Hex"] = binary.BinaryWidget(data)
		
		if widgets:
			tabs = QTabWidget()
			for name, widget in widgets.items():
				tabs.addTab(widget, name)
			self.setCentralWidget(tabs)


if __name__ == "__main__":
	app = QApplication(sys.argv)
	settings = QSettings("Yannik Marchand", "Panorama")
	window = MainWindow(settings)
	window.show()
	app.exec()
