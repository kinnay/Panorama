
from jungle.sead import sarc
import qtawesome
import nodes


class SARCUnnamedFilesNode(nodes.Node):
	def __init__(self, plugins, file):
		super().__init__()
		self.setText(0, "Unnamed Files")

		for hash in file.unnamed_files:
			reader = nodes.MemoryReader("%08x" %hash, file.unnamed_files[hash])
			self.addChild(plugins.create(reader))


class SARCFolderNode(nodes.Node):
	def __init__(self, plugins, file, path):
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
	def __init__(self, plugins, reader):
		super().__init__()
		self.plugins = plugins
		self.reader = reader

		self.file = sarc.SARCFile()
		self.file.parse(reader.read())

		self.setText(0, reader.text())
		self.setIcon(0, qtawesome.icon("fa5s.box", color="#a50"))

		files = []
		folders = []
		for path in self.file.files:
			if "/" in path:
				name = path.split("/")[0]
				if name not in folders:
					folders.append(name)
			else:
				files.append(path)
		
		for folder in folders:
			self.addChild(SARCFolderNode(self.plugins, self.file, folder))
		for file in files:
			reader = nodes.MemoryReader(file, self.file.files[file])
			self.addChild(self.plugins.create(reader))
		
		if self.file.unnamed_files:
			self.addChild(SARCUnnamedFilesNode(self.plugins, self.file))
	
	def read(self):
		return self.reader.read()


class SARCPlugin:
	def analyze(self, data):
		return data[:4] == b"SARC"

	def create(self, plugins, reader):
		return SARCNode(plugins, reader)
