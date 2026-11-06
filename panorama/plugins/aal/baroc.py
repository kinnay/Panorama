
from PyQt6.QtWidgets import *

from jungle.errors import ParseError
from jungle.aal import baroc

from panorama import colors, nodes, plugins
from panorama.widgets import PropertyView

import qtawesome


class BAROCWidget(PropertyView):
    def __init__(self, file: baroc.BAROCFile):
        super().__init__()

        props = {
            "Endianness": "Big" if file.endianness == ">" else "Little",
            "Version": file.version,
            "Roll off model": file.roll_off_model.name,
            "Reference distance": file.ref_distance,
            "Maximum distance": file.max_distance,
            "Roll off factor": file.roll_off_factor,
            "Start value": file.start_value,
            "Is increase mode": file.is_increase_mode,
        }

        if file.culling_distance is not None:
            props["Culling distance"] = file.culling_distance

        self.setProperties(props)


class BAROCNode(nodes.File):
    _file: baroc.BAROCFile | None

    def __init__(self, reader: nodes.Reader):
        super().__init__(reader)
        self._file = baroc.BAROCFile()
        try:
            self._file.parse(reader.read())
        except ParseError:
            self._file = None

        self.setText(0, reader.filename())
        self.setIcon(0, qtawesome.icon("fa5s.file", color=colors.AUDIO))

    def createWidgets(self):
        widgets = {}
        if self._file:
            widgets["BAROC"] = BAROCWidget(self._file)
        return widgets


class BAROCPlugin:
    def analyze(self, data: bytes) -> bool:
        return data[:4] == b"AROC"

    def create(
        self, plugins: plugins.Plugins, reader: nodes.Reader
    ) -> BAROCNode:
        return BAROCNode(reader)
