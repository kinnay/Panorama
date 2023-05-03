
from PyQt6.QtWidgets import *

import io
import mmap
import nodes
import os
import qtawesome


class FileReader(nodes.Reader):
	def __init__(self, path):
		self.path = path
	
	def text(self):
		return os.path.basename(self.path)
	
	def read(self):
		with open(self.path, "rb") as f:
			f.seek(0, io.SEEK_END)
			size = f.tell()
			f.seek(0)

			if size < 1024 * 1024:
				return f.read()
			return mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)


class Folder(nodes.Node):
	def __init__(self, plugins, path):
		super().__init__()
		self.plugins = plugins
		self.path = path

		self.setText(0, os.path.basename(path))
		self.setIcon(0, qtawesome.icon("fa5s.folder", color="#fc0"))

		self.showIndicator(os.listdir(self.path))
	
	def createChildren(self):
		for name in os.listdir(self.path):
			childpath = os.path.join(self.path, name)
			if os.path.isdir(childpath):
				self.addChild(Folder(self.plugins, childpath))
			elif os.path.isfile(childpath):
				reader = FileReader(childpath)
				self.addChild(self.plugins.create(reader))
			else:
				self.addChild(Other(childpath))


class Other(nodes.Node):
	"""Special filesystem node.
	
	Represents a filesystem node that is neither a folder nor
	a regular file. For example, this could be a symbolic link
	or a Unix socket file."""
	
	def __init__(self, path):
		super().__init__()
		self.setText(0, os.path.basename(path))
		self.setIcon(0, qtawesome.icon("fa5s.question"))
