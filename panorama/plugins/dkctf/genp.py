
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from dataclasses import fields

from jungle.dkctf import common, genp
from jungle.errors import ParseError

from panorama import colors, nodes, plugins, utils
from panorama.widgets import ScaledTreeWidget

import qtawesome
import typing

if typing.TYPE_CHECKING:
    from _typeshed import DataclassInstance


type ParentItem = QTreeWidget | QTreeWidgetItem


class GENPWidget(ScaledTreeWidget):
    def __init__(self, file: genp.GENPFile):
        super().__init__()
        self.setHeaderLabels(["Field", "Value"])
        self._createItem(self, file.root)

        self.setRatios([.5, .5])

    def _createItem(
        self, parent: ParentItem, object: DataclassInstance
    ) -> None:
        for field in fields(object):
            value = getattr(object, field.name)
            if value is None:
                continue

            name = utils.underscoreToNaturalText(field.name)

            create_children = False
            if isinstance(value, genp.BEConstant): text = str(value.value)
            elif isinstance(value, genp.IEConstant): text = str(value.value)
            elif isinstance(value, genp.REConstant): text = str(value.value)
            elif isinstance(value, genp.Element):
                text = value.__class__.__name__
                create_children = True
            elif isinstance(value, (int, float, str, common.CGuid)):
                text = str(value)
            else:
                text = "<unsupported type>"

            item = QTreeWidgetItem(parent, [name, text])

            if create_children:
                self._createItem(item, value)


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
