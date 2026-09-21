
from PyQt6.QtWidgets import *
import mmap


class Node(QTreeWidgetItem):
	"""Base class for a tree node that is shown in the filesystem tree."""

	_childrenCreated: bool
	"""
	Whether its children have been created yet, when lazy evaluation is used.
	"""

	def __init__(self):
		super().__init__()
		self._childrenCreated = False
	
	def __lt__(self, other: QTreeWidgetItem) -> bool:
		if isinstance(other, Node):
			if self.priority() < other.priority():
				return True
			if self.priority() > other.priority():
				return False
		return super().__lt__(other)

	def priority(self) -> int:
		"""
		May be overridden by subclasses. Returns the sort order of the node.
		When multiple nodes have an equal sort order, they are sorted
		alphabetically.
		"""
		return 0

	def showIndicator(self, shown: bool) -> None:
		"""
		This method can be used to force an expansion button to be shown. This
		method should be used when it is known that the node has children but
		the children are created lazily when the node is expanded.
		"""
		if shown:
			policy = QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
		else:
			policy = QTreeWidgetItem.ChildIndicatorPolicy \
				.DontShowIndicatorWhenChildless
		self.setChildIndicatorPolicy(policy)
	
	def expand(self) -> None:
		"""
		Creates the child nodes of the node if they have not been created yet.
		"""
		if not self._childrenCreated:
			self.createChildren()
			self._childrenCreated = True
	
	def createChildren(self) -> None:
		"""
		May be overridden by subclasses to implement lazy creation of children.
		This method is called once when the node is expanded.
		"""

	def createWidgets(self) -> dict[str, QWidget]:
		"""
		May be overridden by subclasses. Returns one widget per tab. The
		dictionary key is the title of each tab.
		"""
		return {}


class File(Node):
	"""Base class for file nodes that can be viewed and extracted."""

	_reader: Reader

	def __init__(self, reader: Reader):
		super().__init__()
		self._reader = reader
	
	def reader(self) -> Reader:
		return self._reader

	def read(self) -> bytes | mmap.mmap:
		return self._reader.read()


class Reader:
	"""Base class for file readers."""

	def filename(self) -> str:
		"""
		Returns the filename of the reader. This is displayed in the tree view.
		Must be overridden by subclasses.
		"""
		raise NotImplementedError(f"{self.__class__.__name__}.filename()")
	
	def read(self) -> bytes | mmap.mmap:
		"""
		Returns the content of the file, either as a bytes object or an mmap
		object for large files.
		"""
		raise NotImplementedError(f"{self.__class__.__name__}.read()")


class MemoryReader(Reader):
	"""A basic reader for files that have been loaded in memory."""

	_filename: str
	_data: bytes

	def __init__(self, filename: str, data: bytes):
		self._filename = filename
		self._data = data
	
	def filename(self) -> str:
		return self._filename

	def read(self) -> bytes:
		return self._data
