import sys
import PySpin
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap
import numpy as np


class CameraWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("FLIR Camera Feed")
        self.setGeometry(100, 100, 800, 600)
        
        # Create a QLabel to display the camera feed
        self.label = QLabel(self)
        self.label.setFixedSize(800, 600)
        
        # Create a layout and set it for the main widget
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # Initialize the camera
        self.init_camera()

        # Set up a timer to refresh the image
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30ms (~33 FPS)

    def init_camera(self):
        # Initialize the FLIR camera using PySpin
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        
        if self.cam_list.GetSize() == 0:
            print("No camera detected.")
            sys.exit(0)
        
        self.camera = self.cam_list[0]
        self.camera.Init()
        self.camera.BeginAcquisition()

    def update_frame(self):
        try:
            # Retrieve next frame from the camera
            image_result = self.camera.GetNextImage()

            if image_result.IsIncomplete():
                print("Image incomplete with image status %d ..." % image_result.GetImageStatus())
            else:
                # Get image data as numpy array
                image_data = image_result.GetNDArray()
                
                # Convert image data to QImage
                height, width = image_data.shape
                q_image = QImage(image_data.data, width, height, QImage.Format.Format_Grayscale8)
                
                # Display the image in the label
                pixmap = QPixmap.fromImage(q_image)
                self.label.setPixmap(pixmap)
            
            # Release the image from memory
            image_result.Release()
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)

    def closeEvent(self, event):
        # Cleanup the camera when the window is closed
        self.camera.EndAcquisition()
        self.camera.DeInit()
        del self.camera
        self.cam_list.Clear()
        self.system.ReleaseInstance()
        super().closeEvent(event)

        