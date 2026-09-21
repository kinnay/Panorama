
"""
Provides nodes for files and folders that are stored on disk.
"""


from PyQt6.QtWidgets import *

import io
import mmap
import nodes
import os
import plugins
import qtawesome


class FileReader(nodes.Reader):
	"""Reader for files that are stored on disk."""

	_path: str

	def __init__(self, path: str):
		self._path = path

	def path(self) -> str:
		return self._path
	
	def filename(self) -> str:
		return os.path.basename(self._path)
	
	def read(self) -> bytes | mmap.mmap:
		"""
		Opens the file. Files that are smaller than 1 MB are read completely
		into memory. Larger files are mapped with mmap.
		"""
		with open(self._path, "rb") as f:
			f.seek(0, io.SEEK_END)
			size = f.tell()
			f.seek(0)

			if size < 1024 * 1024:
				return f.read()
			return mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)


class Folder(nodes.Node):
	"""Represents a folder on disk."""

	_plugins: plugins.Plugins
	_path: str

	def __init__(self, plugins: plugins.Plugins, path: str):
		super().__init__()
		self._plugins = plugins
		self._path = path

		self.setText(0, os.path.basename(path))
		self.setIcon(0, qtawesome.icon("fa5s.folder", color="#fc0"))

		self.showIndicator(bool(os.listdir(self._path)))
	
	def path(self) -> str:
		return self._path
	
	def priority(self) -> int:
		return -1 # Show folders before everything else

	def createChildren(self) -> None:
		for name in os.listdir(self._path):
			childpath = os.path.join(self._path, name)
			if os.path.isdir(childpath):
				self.addChild(Folder(self._plugins, childpath))
			elif os.path.isfile(childpath):
				reader = FileReader(childpath)
				self.addChild(self._plugins.create(reader))
			else:
				self.addChild(Other(childpath))


class Other(nodes.Node):
	"""
	Special filesystem node.
	
	Represents a filesystem node that is neither a folder nor a regular file.
	For example, this could be a symbolic link or a Unix socket file.
	"""

	_path: str
	
	def __init__(self, path: str):
		super().__init__()
		self._path = path

		self.setText(0, os.path.basename(path))
		self.setIcon(0, qtawesome.icon("fa5s.question"))

	def path(self) -> str:
		return self._path
