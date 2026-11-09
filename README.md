This project implements a viewer for various file formats that are seen in Nintendo games.

## Installation
This tool can be installed as follows: `pipx install panorama-tools`.

To update the tool to the latest version, run `pipx upgrade panorama-tools`.

After installation, the tool can be started by executing `panorama`.

## Features
After launching the tool, you can import files or folder into the workspace. This allows you to browse through files in a tree, including files that are stored in archives. After selecting a file in the tree, the contents of the file are displayed on the screen. In addition to file-specific widgets, a hex viewer is shown that displays the raw contents of the file, even for files that would otherwise not be supported.

Many files formats are currently supported, including archive, audio and texture formats. Check out the [plugins](https://github.com/kinnay/Panorama/tree/main/panorama/plugins) folder to see a list of file formats that are currently supported.

## Screenshots
<div style="float: left">
  <img src="https://github.com/user-attachments/assets/ed5ef941-2e95-4a62-b0d4-1924d8d36dc7" width="750" />
  <img src="https://github.com/user-attachments/assets/ed895f53-a9f7-4c21-8151-0f720d63a337" width="750" />
</div>
