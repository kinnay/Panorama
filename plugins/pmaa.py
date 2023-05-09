
from jungle.agl import pmaa
from jungle.db import hashes
import nodes
import properties
import qtawesome


class PMAAWidget(properties.PropertyView):
	def __init__(self, file):
		super().__init__()

		props = {}
		props[self.makeName(file.root.hash)] = self.makeList(file.root)
		self.setProperties(props)
	
	def makeName(self, hash):
		name = hashes.crc32(hash)
		if name is None:
			return "%08x" %hash
		return name

	def makeList(self, list):
		props = {}
		for child in list.children:
			props[self.makeName(child.hash)] = self.makeList(child)
		for object in list.objects:
			props["%s:%s" %(self.makeName(object.group_hash), self.makeName(object.hash))] = self.makeObject(object)
		return props

	def makeObject(self, object):
		props = {}
		for parameter in object.parameters:
			props[self.makeName(parameter.hash)] = parameter.value
		return props


class PMAANode(nodes.File):
	def __init__(self, plugins, reader):
		super().__init__()
		self.plugins = plugins
		self.reader = reader

		self.file = pmaa.PMAAFile()
		self.file.parse(reader.read())

		self.setText(0, reader.text())
		self.setIcon(0, qtawesome.icon("ri.landscape-fill", color="#00c"))

	def read(self):
		return self.reader.read()

	def createWidgets(self):
		return {
			"Metadata": PMAAWidget(self.file)
		}


class PMAAPlugin:
	def analyze(self, data):
		return data[:4] in [b"PMAA", b"AAMP"]

	def create(self, plugins, reader):
		return PMAANode(plugins, reader)
