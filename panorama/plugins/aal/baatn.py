
from PyQt6.QtWidgets import *

from jungle.errors import ParseError
from jungle.aal import baatn

from panorama import colors, nodes, plugins, properties

import qtawesome


class BAATNWidget(properties.PropertyView):
    def __init__(self, file: baatn.BAATNFile):
        super().__init__()

        props: properties.PropertyDict = {
            "Endianness": "Big" if file.endianness == ">" else "Little",
            "Version": file.version,
            "Directivity": file.directivity,
            "Culling": file.culling,
            "Listener enabled": file.listener_enabled,
            "Occlusion enabled": file.occlusion_enabled
        }

        for distance_param_target in baatn.DistanceParamTarget:
            curve = file.curves[distance_param_target]
            props[distance_param_target.name] = {
                "Name": curve.name,
                "Type": curve.type.name
            }

        self.setProperties(props)


class BAATNNode(nodes.File):
    _file: baatn.BAATNFile | None

    def __init__(self, reader: nodes.Reader):
        super().__init__(reader)
        self._file = baatn.BAATNFile()
        try:
            self._file.parse(reader.read())
        except ParseError:
            self._file = None

        self.setText(0, reader.filename())
        self.setIcon(0, qtawesome.icon("fa5s.file", color=colors.AUDIO))

    def createWidgets(self):
        widgets = {}
        if self._file:
            widgets["BAATN"] = BAATNWidget(self._file)
        return widgets


class BAATNPlugin:
    def analyze(self, data: bytes) -> bool:
        return data[:4] == b"AATN"

    def create(
        self, plugins: plugins.Plugins, reader: nodes.Reader
    ) -> BAATNNode:
        return BAATNNode(reader)
