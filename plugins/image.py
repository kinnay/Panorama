
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import colors
import nodes
import plugins
import qtawesome


class ImageWidget(QWidget):
    def __init__(self, image: QImage):
        super().__init__()
        pixmap = QPixmap.fromImage(image)
        
        label = QLabel()
        label.setPixmap(pixmap)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


#class ImageWidget(QLabel):
#    def __init__(self, image: QImage):
#        super().__init__()
#        self.setPixmap(QPixmap.fromImage(image))


class ImageNode(nodes.File):
    _image: QImage | None
    
    def __init__(self, reader: nodes.Reader):
        super().__init__(reader)
        try:
            self._image = QImage.fromData(reader.read())
        except Exception:
            self._image = None

        self.setText(0, reader.filename())
        self.setIcon(
            0, qtawesome.icon("fa6s.image", color=colors.GRAPHICS)
        )

    def createWidgets(self) -> dict[str, QWidget]:
        widgets: dict[str, QWidget] = {}
        if self._image:
            widgets["Image"] = ImageWidget(self._image)
        return widgets


class ImagePlugin:
    def analyze(self, data: bytes) -> bool:
        # We only detect JPEG for now
        return data[:2] == b"\xFF\xD8"

    def create(
        self, plugins: plugins.Plugins, reader: nodes.Reader
    ) -> ImageNode:
        return ImageNode(reader)
