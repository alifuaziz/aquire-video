import PySpin
import subprocess
import cv2
import numpy as np

def capture_and_encode_spinnaker_camera(output_file, num_frames=60, fps=30):
    """
    Capture frames from the Spinnaker camera and directly encode to H.265 using FFmpeg and CUDA.

    Args:
        output_file (str): The output file path for the encoded video.
        num_frames (int): Number of frames to capture from the camera.
        fps (int): Frames per second for the output video.
    """
    # Initialize camera system
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    if cam_list.GetSize() == 0:
        print("No Spinnaker cameras detected.")
        system.ReleaseInstance()
        return

    camera = cam_list.GetByIndex(0)

    try:
        camera.Init()
        camera.BeginAcquisition()
        print("Capturing video from Spinnaker camera...")

        # Retrieve frame width and height from the camera
        image_result = camera.GetNextImage()
        frame_width = image_result.GetWidth()
        frame_height = image_result.GetHeight()
        print(f"Frame resolution: {frame_width}x{frame_height}")
        image_result.Release()

        # FFmpeg command for piping
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-f', 'rawvideo',  # Raw video format
            '-pix_fmt', 'bgr24',  # Pixel format for raw video
            f'-s', f'{frame_width}x{frame_height}',  # Frame size from the camera
            '-r', str(fps),  # Frame rate
            '-i', '-',  # Input from stdin
            '-c:v', 'hevc_nvenc',  # Use NVIDIA HEVC encoder
            '-b:v', '4M',  # Bitrate
            '-pix_fmt', 'yuv420p',  # Output pixel format
            output_file
        ]

        # Open subprocess to pipe frames to FFmpeg
        process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

        for i in range(num_frames):
            image_result = camera.GetNextImage()

            if image_result.IsIncomplete():
                print(f"Image incomplete with image status {image_result.GetImageStatus()}")
            else:
                # Convert Spinnaker image to NumPy array (BGR format for OpenCV)
                image_data = image_result.GetNDArray()

                # Handle the Bayer format to ensure the frame is correctly converted to BGR
                if image_result.GetPixelFormatName() == "BayerRG8":
                    frame = cv2.cvtColor(image_data, cv2.COLOR_BAYER_RG2BGR)
                else:
                    frame = image_data  # If already in BGR or another format

                # Verify that the frame size is correct before sending it to FFmpeg
                assert frame.shape[0] == frame_height and frame.shape[1] == frame_width, \
                    f"Frame size mismatch! Expected: {frame_width}x{frame_height}, Got: {frame.shape[1]}x{frame.shape[0]}"

                # Write frame to FFmpeg process
                process.stdin.write(frame.tobytes())

            image_result.Release()

        # Close the FFmpeg process
        process.stdin.close()
        process.wait()

        print(f"Video saved to {output_file}.")

    except PySpin.SpinnakerException as ex:
        print("Error:", ex)

    finally:
        camera.EndAcquisition()
        camera.DeInit()
        del camera
        cam_list.Clear()
        system.ReleaseInstance()


# Example usage
output_video = 'test_files/output_video.mp4'  # Output in mp4 format
capture_and_encode_spinnaker_camera(output_video, num_frames=60, fps=30)
