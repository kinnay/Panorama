

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from jungle.errors import ParseError
from jungle.gx2.textures import GX2SurfaceFormat, GX2SurfaceType
from jungle.nw import bflim

from ninty import gx2, lzss

from panorama import colors, nodes, plugins, utils
from panorama.widgets import PropertyView, ImageWidget

import qtawesome
import struct


ImageFormats = {
    bflim.BFLIMFormat.L8: (GX2SurfaceType.UNORM, GX2SurfaceFormat.R8),
    bflim.BFLIMFormat.A8: (GX2SurfaceType.UNORM, GX2SurfaceFormat.R8),
    bflim.BFLIMFormat.LA8: (GX2SurfaceType.UNORM, GX2SurfaceFormat.R8_G8),
    bflim.BFLIMFormat.BC1: (GX2SurfaceType.UNORM, GX2SurfaceFormat.BC1),
    bflim.BFLIMFormat.BC3: (GX2SurfaceType.UNORM, GX2SurfaceFormat.BC3),
    bflim.BFLIMFormat.BC4L: (GX2SurfaceType.UNORM, GX2SurfaceFormat.BC4),
    bflim.BFLIMFormat.BC4A: (GX2SurfaceType.UNORM, GX2SurfaceFormat.BC4),
    bflim.BFLIMFormat.BC5: (GX2SurfaceType.UNORM, GX2SurfaceFormat.BC5),
}


class BFLIMWidget(PropertyView):
    def __init__(self, file: bflim.BFLIMFile):
        super().__init__()
        version = ".".join([
            str(file.version >> 24),
            str((file.version >> 16) & 0xFF),
            str((file.version >> 8) & 0xFF),
            str(file.version & 0xFF)
        ])

        props = {
            "Endianness": "Big" if file.endianness == ">" else "Little",
            "Version": version,

            "Width": file.width,
            "Height": file.height,
            "Alignment": file.alignment,
            "Format": file.format.name,
            "Tile mode": file.tile_mode.name,
            "Swizzle": file.swizzle,
            "Data size": utils.formatSize(len(file.data))
        }
        self.setProperties(props)


class BFLIMViewer(QWidget):
    def __init__(self, file: bflim.BFLIMFile):
        super().__init__()
        widget: QWidget
        if file.format not in ImageFormats:
            widget = QLabel(f"Unsupported image format: {file.format.name}")
        else:
            type, format = ImageFormats[file.format]
            format_value = (type << 8) | format

            deswizzled = gx2.deswizzle(
                file.data, file.width, file.height, format_value,
                file.tile_mode, file.swizzle
            )
            decoded = gx2.decode(
                deswizzled, file.width, file.height, format_value
            )

            image = QImage(
                decoded, file.width, file.height, QImage.Format.Format_RGBA8888
            )
            widget = ImageWidget(image)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(widget)


class BFLIMNode(nodes.File):
    _file: bflim.BFLIMFile | None

    def __init__(self, reader: nodes.Reader):
        super().__init__(reader)

        self._file = bflim.BFLIMFile()
        try:
            self._file.parse(reader.read())
        except ParseError:
            self._file = None

        self.setText(0, reader.filename())
        self.setIcon(0, qtawesome.icon("fa6s.image", color=colors.GRAPHICS))

    def createWidgets(self):
        widgets = {}
        if self._file:
            widgets["BFLIM"] = BFLIMWidget(self._file)
            widgets["Viewer"] = BFLIMViewer(self._file)
        return widgets


class BFLIMPlugin:
    def analyze(self, data: bytes) -> bool:
        if len(data) < 4:
            return False
        
        offset_be = struct.unpack_from(">I", data, -4)[0]
        offset_le = struct.unpack_from("<I", data, -4)[0]
        if data[offset_be : offset_be + 6] == b"FLIM\xFE\xFF":
            return True
        if data[offset_le : offset_le + 6] == b"FLIM\xFF\xFE":
            return True
        return False

    def create(
        self, plugins: plugins.Plugins, reader: nodes.Reader
    ) -> BFLIMNode:
        return BFLIMNode(reader)
