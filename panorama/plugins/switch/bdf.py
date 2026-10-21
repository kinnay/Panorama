
from PyQt6.QtWidgets import *

from jungle.errors import ParseError
from jungle.switch import bdf

from panorama import colors, nodes, plugins, utils

import qtawesome


class BDFWidget(QTreeWidget):
    def __init__(self, file: bdf.BDFFile):
        super().__init__()
        self.setHeaderLabels(["ID", "Status", "Size"])
        self.setAlternatingRowColors(True)

        for entry in file.entries:
            QTreeWidgetItem(
                self, [
                    str(entry.id), entry.status.name,
                    utils.formatSize(len(entry.data))
                ]
            )


class BDFNode(nodes.File):
    _plugins: plugins.Plugins
    _file: bdf.BDFFile | None

    def __init__(self, plugins: plugins.Plugins, reader: nodes.Reader):
        super().__init__(reader)
        self._plugins = plugins

        self.setText(0, reader.filename())
        self.setIcon(0, qtawesome.icon("fa5s.box", color=colors.ARCHIVE))

        try:
            self._file = bdf.BDFFile()
            self._file.parse(reader.read())
        except ParseError:
            self._file = None
            return

        for entry in self._file.entries:
            reader = nodes.MemoryReader(str(entry.id), entry.data)
            self.addChild(self._plugins.create(reader))

    def createWidgets(self) -> dict[str, QWidget]:
        if self._file:
            return {"BDF": BDFWidget(self._file)}
        return {}


class BDFPlugin:
    def analyze(self, data: bytes) -> bool:
        return data[:4] == b"sslT"

    def create(self, plugins: plugins.Plugins, reader: nodes.Reader) -> BDFNode:
        return BDFNode(plugins, reader)
