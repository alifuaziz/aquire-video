import sys
import cv2
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QSlider, QHBoxLayout
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer, Qt
import PySpin
import numpy as np
import time

class CameraViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FLIR Chameleon3 Camera Viewer")

        # Create a label to display the video feed
        self.image_label = QLabel(self)

        # Create buttons for starting and stopping video recording
        self.start_button = QPushButton("Start Recording")
        self.stop_button = QPushButton("Stop Recording")
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)

        # Create a slider for adjusting framerate
        self.framerate_label = QLabel("Framerate: 30 FPS")
        self.framerate_slider = QSlider(Qt.Orientation.Horizontal)
        self.framerate_slider.setRange(5, 60)  # Framerate range from 5 to 60 FPS
        self.framerate_slider.setValue(30)
        self.framerate_slider.valueChanged.connect(self.update_framerate_label) # Update the label when the slider value changes

        # Create a layout for the framerate slider and label
        framerate_layout = QHBoxLayout()
        framerate_layout.addWidget(self.framerate_label)
        framerate_layout.addWidget(self.framerate_slider)

        # Create a label to display elapsed time
        self.elapsed_time_label = QLabel("Elapsed Time: 0.0 s")

        # Create a layout for the main window
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addLayout(framerate_layout)
        layout.addWidget(self.elapsed_time_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

        # Initialize the camera
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()

        if self.cam_list.GetSize() == 0:
            print("No camera detected.")
            sys.exit()

        self.camera = self.cam_list.GetByIndex(0)
        self.camera.Init()

        # Configure the camera for continuous video acquisition
        self.camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        self.camera.BeginAcquisition()

        # Video recording variables
        self.RECORDING = False
        self.video_writer = None
        self.FRAMERATE = 30 # Default framerate
        self.TIME_INTERVAL = 1000 // self.FRAMERATE  # Calculate the time interval based on the framerate
        self.frame_count = 0  # Counter for frames written
        
        # Create a timer to update the video feed
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(self.TIME_INTERVAL)  # Update the video feed every 30 ms (default)

        # Elapsed time variables
        self.start_time = None
        self.elapsed_timer = QTimer()
        self.elapsed_timer.timeout.connect(self.update_elapsed_time)

        # Get camera resolution
        self.width = self.camera.Width.GetValue()
        self.height = self.camera.Height.GetValue()

        # Check if the camera outputs color or grayscale images
        self.IS_COLOR = self.camera.PixelFormat.GetValue() in [PySpin.PixelFormat_RGB8, PySpin.PixelFormat_BGR8]

        print(f"Camera Resolution: {self.width}x{self.height}")
        print(f"Is Color: {self.IS_COLOR}")

    def update_image(self):
        try:
            
            # Retrieve the latest image from the camera
            image_result = self.camera.GetNextImage()

            # Convert the image data to a format suitable for PyQt6 and OpenCV
            image_data = image_result.GetNDArray()

            
            if self.IS_COLOR:
                # Convert BGR to RGB for displaying in PyQt
                image_data = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
                image_format = QImage.Format.Format_RGB888
                bytes_per_line = 3 * self.width
            else:
                image_format = QImage.Format.Format_Grayscale8
                bytes_per_line = self.width

            image = QImage(image_data.data, self.width, self.height, bytes_per_line, image_format)

            # Display the image in the GUI
            pixmap = QPixmap.fromImage(image)
            self.image_label.setPixmap(pixmap)

            # Save the image to the video file if recording is enabled
            if self.RECORDING and self.video_writer is not None:
                if not self.IS_COLOR:
                    # Convert grayscale to BGR before writing to the video
                    image_bgr = cv2.cvtColor(image_data, cv2.COLOR_GRAY2BGR)
                else:
                    image_bgr = cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR)  # Back to BGR for video writer

                # Write the frame to the video_writer object that will save to become a video
                self.video_writer.write(image_bgr)
                self.frame_count += 1  # Increment frame count

            # Release the image back to the camera
            image_result.Release()
        
        except PySpin.SpinnakerException as e:
            print(f"Error: {e}")

    def update_framerate_label(self):
        # Update the label to reflect the current framerate slider value
        self.FRAMERATE = self.framerate_slider.value()
        self.TIME_INTERVAL = 1000 // self.FRAMERATE  # Calculate the time interval based on the framerate
        self.framerate_label.setText(f"Framerate: {self.FRAMERATE} FPS")

    def update_elapsed_time(self):
        # Update the elapsed time label
        if self.start_time is not None:
            elapsed_time = time.time() - self.start_time
            self.elapsed_time_label.setText(f"Elapsed Time: {elapsed_time:.1f} s")

    def start_recording(self):
        try:
            # Create a video writer object to save the video with the selected framerate
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.video_writer = cv2.VideoWriter("output.mp4", fourcc, self.FRAMERATE, (self.width, self.height), isColor=True)

            if not self.video_writer.isOpened():
                print("Error: Could not open video file for writing.")
                return

            print(f"Recording started at {self.FRAMERATE} FPS...")
            self.RECORDING = True
            self.frame_count = 0  # Reset frame count
            self.start_time = time.time()  # Start the timer
            self.elapsed_timer.start(100)  # Update elapsed time every 100 ms
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        except Exception as e:
            print(f"Failed to start recording: {e}")

    def stop_recording(self):
        # Release the video writer object
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

        print(f"Recording stopped... Total frames written: {self.frame_count}. Elapsed time: {time.time() - self.start_time:.1f} s")
        self.RECORDING = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        # Stop the elapsed timer
        self.elapsed_timer.stop()
        self.start_time = None  # Reset start time
        self.elapsed_time_label.setText("Elapsed Time: 0.0 s")  # Reset elapsed time display

    def closeEvent(self, event):
        # Stop the timer
        self.timer.stop()

        # Clean up the camera and system resources when the window is closed
        self.camera.EndAcquisition()
        self.camera.DeInit()
        del self.camera
        self.cam_list.Clear()
        self.system.ReleaseInstance()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = CameraViewer()
    window.show()

    sys.exit(app.exec())


