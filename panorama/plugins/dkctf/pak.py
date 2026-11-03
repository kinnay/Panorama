
from PyQt6.QtWidgets import *

from jungle.dkctf import pak
from jungle.errors import ParseError

from panorama import colors, nodes, plugins

import qtawesome


class PAKFileNode(nodes.Node):
    def __init__(
        self, plugins: plugins.Plugins, asset: pak.PAKAsset, id: str
    ):
        super().__init__()
        self.setText(0, asset.filename or id)

        reader = nodes.MemoryReader("File", asset.data)
        self.addChild(plugins.create(reader))

        reader = nodes.MemoryReader("Metadata", asset.metadata)
        self.addChild(plugins.create(reader))


class PAKFolderNode(nodes.Node):
    def __init__(
        self, plugins: plugins.Plugins, file: pak.PAKFile, type: str
    ):
        super().__init__()
        self.setText(0, type)

        for id, asset in file.assets.items():
            if asset.type != type:
                continue

            if asset.metadata:
                node = PAKFileNode(plugins, asset, id)
                self.addChild(node)
            else:
                filename = asset.filename or id
                reader = nodes.MemoryReader(filename, asset.data)
                self.addChild(plugins.create(reader))


class PAKNode(nodes.File):
    _plugins: plugins.Plugins
    _file: pak.PAKFile | None

    def __init__(self, plugins: plugins.Plugins, reader: nodes.Reader):
        super().__init__(reader)
        self._plugins = plugins

        self.setText(0, reader.filename())
        self.setIcon(0, qtawesome.icon("fa5s.box", color=colors.ARCHIVE))

        try:
            self._file = pak.PAKFile()
            self._file.parse(reader.read())
        except ParseError:
            self._file = None
            return

        types = []
        for asset in self._file.assets.values():
            if asset.type not in types:
                types.append(asset.type)
        types.sort()

        for type in types:
            self.addChild(PAKFolderNode(self._plugins, self._file, type))


class PAKPlugin:
    def analyze(self, data: bytes) -> bool:
        return data[:4] == b"RFRM" and data[20:24] == b"PACK"

    def create(
        self, plugins: plugins.Plugins, reader: nodes.Reader
    ) -> PAKNode:
        return PAKNode(plugins, reader)
