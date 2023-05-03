
from jungle import sarc
import qtawesome
import nodes


class SARCFileReader(nodes.Reader):
	def __init__(self, file, path):
		self.file = file
		self.path = path
	
	def text(self):
		return self.path.split("/")[-1]

	def read(self):
		return self.file.files[self.path]


class SARCUnnamedFileReader(nodes.Reader):
	def __init__(self, file, hash):
		self.file = file
		self.hash = hash
	
	def text(self):
		return "%08x" %self.hash

	def read(self):
		return self.file.unnamed_files[self.hash]


class SARCUnnamedFilesNode(nodes.Node):
	def __init__(self, plugins, file):
		super().__init__()
		self.setText(0, "<unnamed files>")

		for hash in self.file.unnamed_files:
			reader = SARCUnnamedFileReader(file, hash)
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
			reader = SARCFileReader(file, path)
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
			reader = SARCFileReader(self.file, file)
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
