# QGIS / Qt UI Previewer for VS Code

Since there is no native way to render Qt/PyQt windows inside VS Code (as they require a host application or Qt environment), this extension bridges the gap for QGIS plugin developers. 

It provides a command to quickly visualize `.ui` (Qt Designer) files directly inside a VS Code webview tab by spinning up a headless Python instance, rendering the widget, and capturing it as an image.

## Features

- **Quick Preview**: Right-click any `.ui` file in your Explorer or editor tab and select **Preview Qt UI**.
- **PyQt5 & PyQt6 Support**: The python script automatically attempts to use whichever framework is installed in your active environment.
- **Side-by-side editing**: See the visual output of your Qt layout without needing to reload your QGIS plugin every time.

## Requirements

1. **Python**: Must be available in your system path.
2. **PyQt5 or PyQt6**: The environment VS Code uses to execute the script needs to have PyQt installed (which is standard if you are developing QGIS plugins).

## Getting Started / Customization

1. Clone this repository.
2. Run `npm install` to install the VS Code extension types.
3. Press `F5` in VS Code to launch an Extension Development Host.
4. Open a project containing a `.ui` file, right click it, and try the preview command!

### Notes on Custom QGIS Widgets
If your `.ui` file contains custom QGIS widgets (like `QgsMapCanvas`), they might fail to load in a standard PyQt environment outside of QGIS. To fix this, you can modify `src/render_ui.py` to gracefully mock those widgets or set your python path to include the `qgis.gui` libraries.
