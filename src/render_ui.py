import sys
import base64

def render_ui_to_base64(ui_file_path):
    try:
        from PyQt5 import uic, QtWidgets
        from PyQt5.QtCore import Qt, QBuffer, QIODevice
    except ImportError:
        try:
            from PyQt6 import uic, QtWidgets
            from PyQt6.QtCore import Qt, QBuffer, QIODevice
        except ImportError:
            print("Error: PyQt5 or PyQt6 is required to render the UI.", file=sys.stderr)
            sys.exit(1)

    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    
    try:
        widget = uic.loadUi(ui_file_path)
    except Exception as e:
        print(f"Failed to parse UI file: {e}\\n(Note: If your UI uses custom QGIS widgets like QgsMapCanvas, they might not be importable outside of QGIS environment)", file=sys.stderr)
        sys.exit(1)

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
