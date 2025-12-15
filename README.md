This project implements a viewer for various file formats that are seen in Nintendo games.

## Features
After launching the tool, you can import files or folder into the workspace. This allows you to browse through files in a tree, including files that are stored in archives. After selecting a file in the tree, the contents of the file are displayed on the screen. In addition to file-specific widgets, a hex editor is shown that displays the raw contents of the file, even for files that would otherwise not be supported. In addition, all files can be extracted from archives.

The following file formats currently have a plugin implemented for them:

| Library | Format | Extensions | Description |
| --- | --- | --- | --- |
| Multiple | [BYAML](https://nintendo-formats.com/libs/common/byaml.html) | `.byml` / `.byaml` | Binary YAML |
| AAL | [BAMETA](https://nintendo-formats.com/libs/aal/bameta.html) | `.bameta` | Audio metadata |
| AAL | [BARS](https://nintendo-formats.com/libs/aal/bars.html) | `.bars` | Audio resources |
| AAL | [BARSLIST](https://nintendo-formats.com/libs/aal/barslist.html) | `.barslist` | Audio resource lists |
| AGL | [PMAA](https://nintendo-formats.com/libs/agl/pmaa.html) | `.bagl*` | Graphics parameters |
| NW4F | [BFWAV](https://nintendo-formats.com/libs/nw/bfwav.html) | `.bfwav` | Wave files |
| SEAD | [SARC](https://nintendo-formats.com/libs/sead/sarc.html) | `.sarc` | Archives |
| SEAD | [SZS](https://nintendo-formats.com/libs/sead/yaz0.html) | `.szs` | Yaz0 compression |
| Other | [ZSTD](https://facebook.github.io/zstd) | `.zs` | Zstd compression |

## Requirements
Using this project requires the following packages to be installed:
* [PyQt6](https://pypi.org/project/PyQt6/) (for the GUI)
* [QtAwesome](https://github.com/spyder-ide/qtawesome) (for icons)
* [jungle](https://github.com/kinnay/jungle) (for file format parsers)
* [ninty](https://github.com/kinnay/ninty) (for fast decoding routines)
* [psutil](https://github.com/giampaolo/psutil) (for memory usage measurement)
* [zstd](https://github.com/sergey-dryabzhinsky/python-zstd) (for zstd decompression)

All packages, except for jungle, can be installed with `pip3 install PyQt6 QtAwesome ninty psutil zstd`.

Jungle requires manual installation (see repository for details).

## Screenshots
<div style="float: left">
  <img src="https://github.com/user-attachments/assets/ed5ef941-2e95-4a62-b0d4-1924d8d36dc7" width="750" />
  <img src="https://github.com/user-attachments/assets/ed895f53-a9f7-4c21-8151-0f720d63a337" width="750" />
</div>
