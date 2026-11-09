
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from panorama import colors, nodes, plugins
from panorama.widgets import ImageWidget

import qtawesome


class ImageNode(nodes.File):
    _image: QImage | None
    
    def __init__(self, reader: nodes.Reader):
        super().__init__(reader)
        try:
            self._image = QImage.fromData(reader.read())
        except Exception:
            self._image = None

        self.setText(0, reader.filename())
        self.setIcon(0, qtawesome.icon("fa6s.image", color=colors.GRAPHICS))

    def createWidgets(self) -> dict[str, QWidget]:
        widgets: dict[str, QWidget] = {}
        if self._image:
            widgets["Image"] = ImageWidget(self._image)
        return widgets


class ImagePlugin:
    def analyze(self, data: bytes) -> bool:
        # We only detect JPEG and PNG for now
        return data[:2] == b"\xFF\xD8" or data[:4] == b"\x89PNG"

    def create(
        self, plugins: plugins.Plugins, reader: nodes.Reader
    ) -> ImageNode:
        return ImageNode(reader)
