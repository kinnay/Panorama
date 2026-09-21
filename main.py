
"""
Panorama is a program that is designed to view various file formats that are
seen in Nintendo games.
"""

from PyQt6.QtCore import *
from PyQt6.QtGui import *
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

	_text: QLabel
	_timer: QTimer
	
	def __init__(self):
		super().__init__()
		self._text = QLabel()
		self.addPermanentWidget(self._text)

		self._timer = QTimer()
		self._timer.setInterval(500)
		self._timer.timeout.connect(self._updateStatus)
		self._timer.start()
		self._updateStatus()
	
	def _updateStatus(self) -> None:
		process = psutil.Process()
		usage = utils.formatSize(process.memory_info().rss)
		text = f"Memory usage: {usage}"
		self._text.setText(text)


class MainWindow(QMainWindow):
	"""The main window of the program."""

	_settings: QSettings

	_plugins: plugins.Plugins
	_unsaved: bool

	_menu: menu.MenuBar
	_statusBar: StatusBar

	_workspaceView: workspace.WorkspaceView
	_workspacePaths: list[str]
	_workspaceDock: QDockWidget

	def __init__(self, settings: QSettings):
		super().__init__()
		self._settings = settings

		# Initialize general variables
		self._plugins = plugins.Plugins()
		self._unsaved = False

		# Initialize various components
		self._initializeGeometry()
		self._initializeMenuBar()
		self._initializeStatusBar()
		self._initializeWorkspace()
		
		self.setCentralWidget(QWidget())
		self.setWindowTitle("Panorama")

	def closeEvent(self, e: QCloseEvent) -> None:
		self._settings.setValue("window.geometry", self.saveGeometry())
		self._settings.setValue("window.state", self.saveState())

	def _initializeGeometry(self) -> None:
		"""Restores the window to its previous geometry."""

		geometry = self._settings.value("window.geometry")
		if geometry:
			self.restoreGeometry(geometry)
		else:
			screen = self.screen().size()
			self.setGeometry(
				screen.width() // 4, screen.height() // 4,
				screen.width() // 2, screen.height() // 2
			)

	def _initializeMenuBar(self) -> None:
		self._menu = menu.MenuBar()
		self._menu.file.importFile.triggered.connect(self._handleImportFile)
		self._menu.file.importFolder.triggered.connect(self._handleImportFolder)
		self._menu.file.reloadWorkspace.triggered.connect(
			self._handleReloadWorkspace
		)
		self.setMenuBar(self._menu)

	def _initializeStatusBar(self) -> None:
		self._statusBar = StatusBar()
		self.setStatusBar(self._statusBar)

	def _initializeWorkspace(self) -> None:
		self._workspaceView = workspace.WorkspaceView(
			self._plugins, self._settings
		)
		self._workspaceView.itemActivated.connect(self._handleItemActivated)
		self._workspaceView.itemRemoved.connect(self._handleItemRemoved)

		self._workspacePaths = self._settings.value("workspace.paths", [])
		for path in self._workspacePaths:
			self._workspaceView.addPath(path)

		self._workspaceDock = QDockWidget("Workspace")
		self._workspaceDock.setObjectName("workspace")
		self._workspaceDock.setWidget(self._workspaceView)
		self.addDockWidget(
			Qt.DockWidgetArea.LeftDockWidgetArea, self._workspaceDock
		)

		self.restoreState(self._settings.value("window.state", b""))
		
	def _handleImportFile(self) -> None:
		path, filter = QFileDialog.getOpenFileName(
			self, "Import file", self._settings.value("filesystem.import_path"),
			"All files (*.*)"
		)
		if path and path not in self._workspacePaths:
			self._workspacePaths.append(path)
			self._settings.setValue("workspace.paths", self._workspacePaths)
			self._settings.setValue("filesystem.import_path", path)
			self._workspaceView.addPath(path)

	def _handleImportFolder(self) -> None:
		dir = QFileDialog.getExistingDirectory(
			self, "Import Folder", self._settings.value("filesystem.import_path")
		)
		if dir and dir not in self._workspacePaths:
			self._workspacePaths.append(dir)
			self._settings.setValue("workspace.paths", self._workspacePaths)
			self._settings.setValue("filesystem.import_path", dir)
			self._workspaceView.addPath(dir)
	
	def _handleReloadWorkspace(self) -> None:
		self._workspaceView.clear()
		for path in self._workspacePaths:
			self._workspaceView.addPath(path)

	def _handleItemActivated(self, item: nodes.Node) -> None:
		widgets = item.createWidgets()

		# Always create a hex editor and text editor if applicable
		if isinstance(item, nodes.File):
			data = item.read()
			if isinstance(data, bytes) and \
			   all(chr(c) in string.printable for c in data):
				widgets["Text"] = text.TextWidget(data.decode())
			widgets["Hex"] = binary.BinaryWidget(data)
		
		if widgets:
			tabs = QTabWidget()
			for name, widget in widgets.items():
				tabs.addTab(widget, name)
			self.setCentralWidget(tabs)
	
	def _handleItemRemoved(self, path: str) -> None:
		self._workspacePaths.remove(path)
		self._settings.setValue("workspace.paths", self._workspacePaths)


if __name__ == "__main__":
	sys.argv += ["-platform", "xcb"]
	
	app = QApplication(sys.argv)
	settings = QSettings("Yannik Marchand", "Panorama")
	window = MainWindow(settings)
	window.show()
	app.exec()
