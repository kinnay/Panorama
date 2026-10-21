
from PyQt6.QtWidgets import *

from jungle.errors import ParseError
from jungle.aal import bameta

from panorama import colors, nodes, plugins, properties

import qtawesome


class BAMETAWidget(properties.PropertyView):
    def __init__(self, file: bameta.BAMETAFile):
        super().__init__()

        props: properties.PropertyDict = {
            "Endianness": "Big" if file.endianness == ">" else "Little",
            "Version": f"0x{file.version:X}",
            "Name": file.name,
            "Type:": file.type.name,
            "Number of channels": file.num_channels,
            "Number of samples": file.num_samples,
            "Number of samples (48000 Hz)": file.num_output_samples,
            "Sample rate": file.sample_rate,
            "Is looped": "Yes" if file.flags & bameta.Flags.Looped else "No"
        }

        if file.flags & bameta.Flags.Looped:
            props["Loop start sample"] = file.loop_start

        props["Is stream"] = "Yes" if file.flags & bameta.Flags.Stream else "No"
        props["Has prefetch data"] = \
            "Yes" if file.flags & bameta.Flags.Prefetch else "No"
        props["Is opus"] = "Yes" if file.flags & bameta.Flags.Opus else "No"

        props["RMS amplitude"] = file.amplitude_rms
        props["Loudness"] = 10 ** (file.loudness / 20)
        props["Peak amplitude"] = file.amplitude_peak

        if file.stream_tracks:
            tracks = []
            for track in file.stream_tracks:
                tracks.append({
                    "Number of channels": track.channels,
                    "Volume": track.volume
                })
            props["Stream tracks"] = tracks
        
        markers = []
        for marker in file.markers:
            markers.append({
                "Id": marker.id,
                "Name": marker.name,
                "Start sample": marker.start,
                "Length": marker.length
            })
        props["Markers"] = markers

        exts = []
        for ext in file.ext:
            exts.append({
                "Name": ext.name,
                "Value": ext.value
            })
        props["Ext"] = exts

        self.setProperties(props)


class BAMETANode(nodes.File):
    _file: bameta.BAMETAFile | None

    def __init__(self, reader: nodes.Reader):
        super().__init__(reader)
        self._file = bameta.BAMETAFile()
        try:
            self._file.parse(reader.read())
        except ParseError:
            self._file = None

        self.setText(0, reader.filename())
        self.setIcon(0, qtawesome.icon("fa5s.file", color=colors.AUDIO))

    def createWidgets(self):
        widgets = {}
        if self._file:
            widgets["Metadata"] = BAMETAWidget(self._file)
        return widgets


class BAMETAPlugin:
    def analyze(self, data: bytes) -> bool:
        return data[:4] == b"AMTA"

    def create(
        self, plugins: plugins.Plugins, reader: nodes.Reader
    ) -> BAMETANode:
        return BAMETANode(reader)
