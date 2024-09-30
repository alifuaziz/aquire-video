import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

# import the CameraWindow class from CameraWindow.py
from CameraWindow import CameraWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = CameraWindow()
    window.show()
    
    sys.exit(app.exec())
