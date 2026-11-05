
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from jungle.dkctf import txtr
from jungle.errors import ParseError
from jungle.gx2.textures import GX2SurfaceFormat, GX2SurfaceType

from ninty import gx2, lzss

from panorama import colors, nodes, plugins, properties, utils

import qtawesome


SurfaceFormats = {
    txtr.TextureFormat.UNORM_R8_G8_B8_A8:
        (GX2SurfaceType.UNORM << 8) | GX2SurfaceFormat.R8_G8_B8_A8,

    txtr.TextureFormat.UNORM_BC1:
        (GX2SurfaceType.UNORM << 8) | GX2SurfaceFormat.BC1,
    txtr.TextureFormat.UNORM_BC3:
        (GX2SurfaceType.UNORM << 8) | GX2SurfaceFormat.BC3,
    txtr.TextureFormat.UNORM_BC5:
        (GX2SurfaceType.UNORM << 8) | GX2SurfaceFormat.BC5
}


class TXTRWidget(properties.PropertyView):
    def __init__(self, file: txtr.TXTRFile):
        super().__init__()

        header = file.header
        sampler = header.sampler_data

        props = {
            "Texture type": header.type.name,
            "Texture format": header.format.name,
            "Width": header.width,
            "Height": header.height,
            "Depth": header.depth,
            "Tile mode": header.tile_mode,
            "Swizzle": header.swizzle,
            "Flags": sampler.flags,
            "Texture filter": sampler.filter.name,
            "Wrap mode X": sampler.wrap_x.name,
            "Wrap mode Y": sampler.wrap_y.name,
            "Wrap mode Z": sampler.wrap_z.name,
            "Mipmap sizes":
                [utils.formatSize(size) for size in header.mipmap_sizes],
            "Total data size": utils.formatSize(len(file.data))
        }
        self.setProperties(props)


class TXTRMetadataWidget(properties.PropertyView):
    def __init__(self, metadata: txtr.TXTRMetadata):
        super().__init__()

        buffers = []
        for buffer in metadata.buffers:
            buffers.append({
                "Compressed size": utils.formatSize(buffer.compressed_size),
                "Decompressed size": utils.formatSize(buffer.decompressed_size),
                "Offset": buffer.offset
            })
        
        props = {
            "Allocation category": metadata.allocation_category,
            "Header size": utils.formatSize(metadata.header_size),
            "Alignment": metadata.alignment,
            "Data offset": metadata.data_offset,
            "Data size": metadata.data_size,
            "Buffers": buffers
        }
        self.setProperties(props)


class TXTRViewer(QWidget):
    def __init__(self, file: txtr.TXTRFile, data: bytes):
        super().__init__()
        header = file.header

        label = QLabel()
        if header.type != txtr.TextureType.Texture2D:
            label.setText(f"Unsupported texture type: {header.type.name}")
        elif header.format not in SurfaceFormats:
            label.setText(f"Unsupported texture format: {header.format.name}")
        else:
            format = SurfaceFormats[header.format]
            deswizzled = gx2.deswizzle(
                data, header.width, header.height, format,
                header.tile_mode, header.swizzle
            )
            decoded = gx2.decode(
                deswizzled, header.width, header.height, format
            )

            image = QImage(
                decoded, header.width, header.height,
                QImage.Format.Format_RGBA8888
            )
            pixmap = QPixmap.fromImage(image)
            label.setPixmap(pixmap)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


class TXTRNode(nodes.File):
    _file: txtr.TXTRFile | None
    _metadata: txtr.TXTRMetadata | None
    _buffers: list[bytes]

    def __init__(self, plugins: plugins.Plugins, reader: nodes.Reader):
        super().__init__(reader)

        self._buffers = []

        self._file = txtr.TXTRFile()
        try:
            self._file.parse(reader.read())
        except ParseError:
            self._file = None

        self.setText(0, reader.filename())
        self.setIcon(0, qtawesome.icon("fa6s.image", color=colors.GRAPHICS))

        self._metadata = None

        meta = reader.metadata()
        if meta is None:
            return

        self._metadata = txtr.TXTRMetadata()
        try:
            self._metadata.parse(meta)
        except ParseError:
            self._metadata = None
            return

        if self._file is None:
            return

        for i, buffer in enumerate(self._metadata.buffers):
            compressed_data = self._file.data[
                buffer.offset : buffer.offset + buffer.compressed_size
            ]
            try:
                decompressed_data = lzss.decompress(
                    compressed_data, buffer.decompressed_size
                )
            except Exception:
                continue

            self._buffers.append(decompressed_data)

            reader = nodes.MemoryReader(f"decompressed{i}", decompressed_data)
            self.addChild(plugins.create(reader))

    def createWidgets(self):
        widgets = {}
        if self._file:
            widgets["TXTR"] = TXTRWidget(self._file)
        if self._metadata:
            widgets["Metadata"] = TXTRMetadataWidget(self._metadata)
        if self._file and len(self._buffers) == 1:
            widgets["Viewer"] = TXTRViewer(self._file, self._buffers[0])
        return widgets


class TXTRPlugin:
    def analyze(self, data: bytes) -> bool:
        return data[:4] == b"RFRM" and data[20:24] == b"TXTR"

    def create(
        self, plugins: plugins.Plugins, reader: nodes.Reader
    ) -> TXTRNode:
        return TXTRNode(plugins, reader)
