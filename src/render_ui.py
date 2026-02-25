import sys
import os
import base64
import re
import tempfile
import importlib.util
import inspect
from unittest.mock import MagicMock

def setup_qt_env():
    try:
        from PyQt5 import QtWidgets, QtCore, uic
        return QtWidgets, QtCore, uic
    except ImportError:
        try:
            from PyQt6 import QtWidgets, QtCore, uic
            return QtWidgets, QtCore, uic
        except ImportError:
            print("Error: PyQt5 or PyQt6 is required.", file=sys.stderr)
            sys.exit(1)

def mock_qgis_imports():
    """Mock the qgis module so that Python files can be imported without QGIS installed."""
    QtWidgets, QtCore, uic = setup_qt_env()
    
    class MockGuiModule(MagicMock):
        def __getattr__(self, name):
            # If it looks like a QGIS widget class (QgsMapCanvas, QgsFileWidget, etc), return QWidget
            if name.startswith('Qgs'):
                return QtWidgets.QWidget
            return MagicMock()

    # Mock the QGIS namespace to prevent ModuleNotFound errors in .py files
    sys.modules['qgis'] = MagicMock()
    sys.modules['qgis.core'] = MagicMock()
    sys.modules['qgis.gui'] = MockGuiModule()
    sys.modules['qgis.utils'] = MagicMock()

def mock_qgis_widgets_in_xml(ui_file_path):
    with open(ui_file_path, 'r', encoding='utf-8') as file:
        ui_content = file.read()
    
    mocked_content = re.sub(r'<class>Qgs[A-Za-z]+</class>', '<class>QWidget</class>', ui_content)
    mocked_content = re.sub(r'class="Qgs[A-Za-z]+"', 'class="QWidget"', mocked_content)

    temp_ui = tempfile.NamedTemporaryFile(delete=False, suffix=".ui", mode='w', encoding='utf-8')
    temp_ui.write(mocked_content)
    temp_ui.close()
    return temp_ui.name

def render_widget_to_base64(widget, QtCore):
    widget.setAttribute(QtCore.Qt.WA_DontShowOnScreen, True)
    widget.show()
    widget.adjustSize()

    pixmap = widget.grab()

    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QIODevice.WriteOnly)
    pixmap.save(buffer, "PNG")
    return base64.b64encode(buffer.data()).decode('utf-8')

def render_ui_file(ui_file_path, QtWidgets, QtCore, uic):
    safe_ui_file = mock_qgis_widgets_in_xml(ui_file_path)
    try:
        widget = uic.loadUi(safe_ui_file)
    except Exception as e:
        os.unlink(safe_ui_file)
        print(f"Failed to parse UI file: {e}", file=sys.stderr)
        sys.exit(1)
    os.unlink(safe_ui_file)
    return render_widget_to_base64(widget, QtCore)

def render_py_file(py_file_path, QtWidgets, QtCore):
    mock_qgis_imports()
    
    dir_name = os.path.dirname(py_file_path)
    sys.path.insert(0, dir_name)
    module_name = os.path.splitext(os.path.basename(py_file_path))[0]
    
    try:
        spec = importlib.util.spec_from_file_location(module_name, py_file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"Failed to import Python file: {e}", file=sys.stderr)
        sys.exit(1)

    widget_to_render = None
    
    # Introspect the imported python file to find PyQt UI classes
    for name, obj in inspect.getmembers(module, inspect.isclass):
        # 1. Matches pyuic-generated UI files (e.g. class Ui_Dialog(object))
        if name.startswith("Ui_") and hasattr(obj, "setupUi"):
            widget_to_render = QtWidgets.QDialog()
            ui = obj()
            ui.setupUi(widget_to_render)
            break
        # 2. Matches programmatic QWidget classes you built directly
        elif issubclass(obj, QtWidgets.QWidget) and obj.__module__ == module_name:
            try:
                # Attempt to instantiate with parent=None
                widget_to_render = obj(None)
                break
            except Exception:
                try:
                    # Attempt to instantiate with no arguments
                    widget_to_render = obj()
                    break
                except Exception:
                    pass

    if not widget_to_render:
        print("Could not find a valid QWidget subclass or pyuic 'Ui_' class in this Python file.", file=sys.stderr)
        sys.exit(1)
        
    return render_widget_to_base64(widget_to_render, QtCore)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render_ui.py <path_to_ui_or_py_file>", file=sys.stderr)
        sys.exit(1)
        
    file_path = sys.argv[1]
    QtWidgets, QtCore, uic = setup_qt_env()
    
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
        
    try:
        if file_path.endswith('.ui'):
            b64 = render_ui_file(file_path, QtWidgets, QtCore, uic)
        elif file_path.endswith('.py'):
            b64 = render_py_file(file_path, QtWidgets, QtCore)
        else:
            print("Unsupported file extension. Please provide a .ui or .py file.", file=sys.stderr)
            sys.exit(1)
            
        print(b64)
    except Exception as e:
        print(f"Rendering failed: {e}", file=sys.stderr)
        sys.exit(1)
