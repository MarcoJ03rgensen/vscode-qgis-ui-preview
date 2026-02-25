import sys
import base64
import re
import tempfile
import os

def mock_qgis_widgets(ui_file_path):
    """
    Reads the .ui file and temporarily mocks custom QGIS widgets (e.g., QgsMapCanvas)
    by replacing them with standard QWidgets so PyQt can render the layout without QGIS dependencies.
    """
    with open(ui_file_path, 'r', encoding='utf-8') as file:
        ui_content = file.read()
    
    # Simple regex to replace Qgs custom classes with QWidget in the XML
    mocked_content = re.sub(r'<class>Qgs[A-Za-z]+</class>', '<class>QWidget</class>', ui_content)
    mocked_content = re.sub(r'class="Qgs[A-Za-z]+"', 'class="QWidget"', mocked_content)

    temp_ui = tempfile.NamedTemporaryFile(delete=False, suffix=".ui", mode='w', encoding='utf-8')
    temp_ui.write(mocked_content)
    temp_ui.close()
    
    return temp_ui.name

def render_ui_to_base64(ui_file_path):
    try:
        from PyQt5 import uic, QtWidgets
        from PyQt5.QtCore import Qt, QBuffer, QIODevice
    except ImportError:
        try:
            from PyQt6 import uic, QtWidgets
            from PyQt6.QtCore import Qt, QBuffer, QIODevice
        except ImportError:
            print("Error: PyQt5 or PyQt6 is required to render the UI. Make sure it is installed in your Python environment.", file=sys.stderr)
            sys.exit(1)

    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    
    # Strip out QGIS-specific widgets to prevent import errors
    safe_ui_file = mock_qgis_widgets(ui_file_path)

    try:
        widget = uic.loadUi(safe_ui_file)
    except Exception as e:
        os.unlink(safe_ui_file)
        print(f"Failed to parse UI file: {e}", file=sys.stderr)
        sys.exit(1)
    
    os.unlink(safe_ui_file)

    widget.setAttribute(Qt.WA_DontShowOnScreen, True)
    widget.show()
    widget.adjustSize()

    pixmap = widget.grab()

    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    pixmap.save(buffer, "PNG")
    b64 = base64.b64encode(buffer.data()).decode('utf-8')

    print(b64)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render_ui.py <path_to_ui_file>", file=sys.stderr)
        sys.exit(1)
    render_ui_to_base64(sys.argv[1])