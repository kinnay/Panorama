
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


class ImageWidget(QWidget):
    _image: QImage
    _position: QPointF
    _scale: float

    _prevMousePos: QPointF

    def __init__(self, image: QImage):
        super().__init__()
        self._image = image
        self._position = QPointF()
        self._scale = 1.0

        self._prevMousePos = QPointF()

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        self._scale *= 1.001 ** delta

        position = event.position()
        difference = position - self._position
        self._position -= difference * (1.001 ** delta - 1)

        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        self._prevMousePos = event.position()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)

        position = event.position()
        difference = position - self._prevMousePos
        self._prevMousePos = position

        if event.buttons() & Qt.MouseButton.LeftButton:
            self._position += difference
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        with painter:
            painter.translate(self._position)
            painter.scale(self._scale, self._scale)
            painter.drawImage(0, 0, self._image)
