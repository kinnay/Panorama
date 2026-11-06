
from PyQt6.QtWidgets import *

from jungle.errors import ParseError
from jungle.gfd import gfx2
from jungle.gx2.textures import GX2Texture

from panorama import colors, nodes, plugins, utils
from panorama.widgets import PropertyView

import qtawesome


class Gfx2Widget(PropertyView):
    def __init__(self, file: gfx2.Gfx2File):
        super().__init__()
        props = {
            "Alignment": file.alignment,
            "# Textures": len(file.textures),
            "# Vertex shaders": len(file.vertex_shaders),
            "# Pixel shaders": len(file.pixel_shaders),
            "# Geometry shaders": len(file.geometry_shaders)
        }
        self.setProperties(props)


class Gfx2TextureWidget(PropertyView):
    def __init__(self, texture: GX2Texture):
        super().__init__()
        surface = texture.surface
        props = {
            "Dim": surface.dim.name,
            "Width": surface.width,
            "Height": surface.height,
            "Depth": surface.depth,
            "Mip levels": surface.mip_levels,
            "Type": surface.type.name,
            "Format": surface.format.name,
            "AA mode": surface.aa_mode.name,
            "Use": surface.use.name,
            "Image size": utils.formatSize(len(surface.image)),
            "Mipmap size": utils.formatSize(len(surface.mipmaps)),
            "Tile mode": surface.tile_mode.name,
            "Swizzle": surface.swizzle,
            "Alignment": surface.alignment,
            "Pitch": surface.pitch,
            "Mip level offset": surface.mip_level_offset,
            "View first mip": texture.view_first_mip,
            "View num mips": texture.view_num_mips,
            "View first slice": texture.view_first_slice,
            "View num slices": texture.view_num_slices,
            "Comp map": texture.comp_map,
            "Registers": texture.regs
        }
        self.setProperties(props)


class Gfx2TextureNode(nodes.Node):
    _texture: GX2Texture

    def __init__(self, texture: GX2Texture, index: int):
        super().__init__()

        self._texture = texture

        self.setText(0, f"texture{index}")
        self.setIcon(0, qtawesome.icon("fa6s.image", color=colors.GRAPHICS))

    def createWidgets(self) -> dict[str, QWidget]:
        return {
            "Texture": Gfx2TextureWidget(self._texture)
        }


class Gfx2Node(nodes.File):
    _plugins: plugins.Plugins
    _file: gfx2.Gfx2File | None

    def __init__(self, plugins: plugins.Plugins, reader: nodes.Reader):
        super().__init__(reader)
        self._plugins = plugins

        self.setText(0, reader.filename())
        self.setIcon(0, qtawesome.icon("fa5s.box", color=colors.GRAPHICS))

        try:
            self._file = gfx2.Gfx2File()
            self._file.parse(reader.read())
        except ParseError:
            self._file = None
            return

        for i, texture in enumerate(self._file.textures):
            self.addChild(Gfx2TextureNode(texture, i))

    def createWidgets(self) -> dict[str, QWidget]:
        widgets: dict[str, QWidget] = {}
        if self._file is not None:
            widgets["Gfx2"] = Gfx2Widget(self._file)
        return widgets


class Gfx2Plugin:
    def analyze(self, data: bytes) -> bool:
        return data[:4] == b"Gfx2"

    def create(
        self, plugins: plugins.Plugins, reader: nodes.Reader
    ) -> Gfx2Node:
        return Gfx2Node(plugins, reader)
