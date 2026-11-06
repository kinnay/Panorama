
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from dataclasses import fields

from jungle.dkctf import genp
from jungle.errors import ParseError

from panorama import colors, nodes, plugins, utils
from panorama.widgets import PropertyView

import qtawesome


class GENPWidget(PropertyView):
    def __init__(self, file: genp.GENPFile):
        super().__init__()

        root = file.root
        props = {}
        for field in fields(root):
            value = getattr(root, field.name)
            if value is None:
                continue

            name = utils.underscoreToNaturalText(field.name)
            props[name] = value
        
        self.setProperties(props)


class GENPNode(nodes.File):
    _file: genp.GENPFile | None

    def __init__(self, reader: nodes.Reader):
        super().__init__(reader)

        self._file = genp.GENPFile()
        try:
            self._file.parse(reader.read())
        except ParseError:
            self._file = None

        self.setText(0, reader.filename())
        self.setIcon(0, qtawesome.icon("fa6s.burst", color=colors.GRAPHICS))

    def createWidgets(self):
        widgets = {}
        if self._file:
            widgets["GENP"] = GENPWidget(self._file)
        return widgets


class GENPPlugin:
    def analyze(self, data: bytes) -> bool:
        return data[:4] == b"RFRM" and data[20:24] == b"GENP"

    def create(
        self, plugins: plugins.Plugins, reader: nodes.Reader
    ) -> GENPNode:
        return GENPNode(reader)
