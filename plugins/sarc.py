
from jungle.errors import ParseError
from jungle.sead import sarc
import qtawesome
import nodes
import properties


class SARCWidget(properties.PropertyView):
	def __init__(self, file):
		super().__init__()

		self.setProperties({
			"Endianness": "Big" if file.endianness == ">" else "Little",
			"File format version": "%i.%i" %(file.version >> 8, file.version & 0xFF),
			"Hash multiplier": file.hash_multiplier,
			"Detected alignment": file.alignment,
			"Number of files": len(file.files) + len(file.unnamed_files)
		})


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
		super().__init__(reader)
		self.plugins = plugins

		self.setText(0, reader.text())
		self.setIcon(0, qtawesome.icon("fa5s.box", color="#a50"))

		try:
			self.file = sarc.SARCFile()
			self.file.parse(reader.read())
		except ParseError:
			self.file = None
			return

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
	
	def createWidgets(self):
		if self.file:
			return {"SARC": SARCWidget(self.file)}
		return {}


class SARCPlugin:
	def analyze(self, data):
		return data[:4] == b"SARC"

	def create(self, plugins, reader):
		return SARCNode(plugins, reader)
