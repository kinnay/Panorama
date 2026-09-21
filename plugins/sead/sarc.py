
from PyQt6.QtWidgets import *
from jungle.errors import ParseError
from jungle.sead import sarc
import colors
import mmap
import nodes
import plugins
import properties
import qtawesome


class SARCWidget(properties.PropertyView):
	def __init__(self, file: sarc.SARCFile):
		super().__init__()

		self.setProperties({
			"Endianness": "Big" if file.endianness == ">" else "Little",
			"File format version": f"{file.version >> 8}.{file.version & 0xFF}",
			"Hash multiplier": file.hash_multiplier,
			"Detected alignment": file.alignment,
			"Number of files": len(file.files) + len(file.unnamed_files)
		})


class SARCUnnamedFilesNode(nodes.Node):
	def __init__(self, plugins: plugins.Plugins, file: sarc.SARCFile):
		super().__init__()
		self.setText(0, "Unnamed Files")

		for hash in file.unnamed_files:
			reader = nodes.MemoryReader(f"{hash:08x}", file.unnamed_files[hash])
			self.addChild(plugins.create(reader))


class SARCFolderNode(nodes.Node):
	def __init__(
		self, plugins: plugins.Plugins, file: sarc.SARCFile, path: str
	):
		super().__init__()
		self.setText(0, path.split("/")[-1])

		files = []
		folders = []
		for filepath in file.files:
			if filepath.startswith(path + "/"):
				subpath = filepath[len(path) + 1:]
				if "/" in subpath:
					folder = path + "/" + subpath.split("/")[0]
					if folder not in folders:
						folders.append(folder)
				else:
					files.append(filepath)
		
		for folder in folders:
			self.addChild(SARCFolderNode(plugins, file, folder))
		
		for path in files:
			reader = nodes.MemoryReader(path.split("/")[-1], file.files[path])
			self.addChild(plugins.create(reader))


class SARCNode(nodes.File):
	_plugins: plugins.Plugins
	_file: sarc.SARCFile | None

	def __init__(self, plugins: plugins.Plugins, reader: nodes.Reader):
		super().__init__(reader)
		self._plugins = plugins

		self.setText(0, reader.filename())
		self.setIcon(0, qtawesome.icon("fa5s.box", color=colors.ARCHIVE))

		try:
			self._file = sarc.SARCFile()
			self._file.parse(reader.read())
		except ParseError:
			self._file = None
			return

		files = []
		folders = []
		for path in self._file.files:
			if "/" in path:
				name = path.split("/")[0]
				if name not in folders:
					folders.append(name)
			else:
				files.append(path)
		
		for folder in folders:
			self.addChild(SARCFolderNode(self._plugins, self._file, folder))
		for file in files:
			reader = nodes.MemoryReader(file, self._file.files[file])
			self.addChild(self._plugins.create(reader))
		
		if self._file.unnamed_files:
			self.addChild(SARCUnnamedFilesNode(self._plugins, self._file))
	
	def createWidgets(self) -> dict[str, QWidget]:
		if self._file:
			return {"SARC": SARCWidget(self._file)}
		return {}


class SARCPlugin:
	def analyze(self, data: bytes) -> bool:
		return data[:4] == b"SARC"

	def create(
		self, plugins: plugins.Plugins, reader: nodes.Reader
	) -> SARCNode:
		return SARCNode(plugins, reader)
