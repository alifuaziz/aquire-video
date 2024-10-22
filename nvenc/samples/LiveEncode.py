import PyNvVideoCodec as nvc
import numpy as np
import json
import argparse
from pathlib import Path
import PySpin
import cv2
from PIL import Image

def GetFrameSize(width, height, surface_format):
    '''
    Explanation of the width and height calcalations for different surface formats:
    
    YUV420 (also known as YUV 4:2:0):

    Calculation: width * height * 3 / 2
    Explanation: This is a chroma subsampled format, meaning that the color information 
    (chroma) is stored at a lower resolution than the brightness (luma). Specifically, 
    the luma (Y) takes up width * height bytes, and the chroma (U and V) takes up half 
    that amount (width * height / 2), making the total size 1.5 * width * height.

    ARGB and ABGR:

    Calculation: width * height * 4
    Explanation: In these formats, each pixel contains 4 bytes of information: one byte
    each for alpha (transparency), red, green, and blue. Since each pixel has 4 components 
    and each component is 1 byte, the total size is 4 * width * height.

    YUV444:

    Calculation: width * height * 3
    Explanation: In YUV 4:4:4, there’s no chroma subsampling. Each pixel has 3 components
    (Y, U, and V), each taking up 1 byte, so the size is 3 * width * height.

    P010:

    Calculation: width * height * 3 / 2 * 2
    Explanation: This is a 10-bit format, but typically stored in 16-bit words for each 
    Y, U, and V component. The structure is similar to YUV420, but because it's 10-bit, each pixel takes more space. To account for this, you multiply the YUV420 size by 2, making the final size 1.5 * 2 * width * height.

    YUV444_16BIT:

    Calculation: width * height * 3 * 2
    Explanation: This is YUV444, but with 16 bits (2 bytes) per component (Y, U, and V).
    Since each component is now 2 bytes, you multiply the usual width * height * 3 by 2,
    making the total 6 * width * height.
    
    '''
    
    frame_size = int(width * height * 3 / 2)
    if surface_format == "ARGB" or surface_format == "ABGR":
        frame_size = width * height * 4
    if surface_format == "YUV444":
        frame_size = width * height * 3
    if surface_format == "YUV420":
        frame_size = int(width * height * 3 / 2)
    if surface_format == "P010":
        frame_size = int(width * height * 3 / 2 * 2)
    if surface_format == "YUV444_16BIT":
        frame_size = int(width * height * 3 * 2)
    return frame_size

def initialize_camera():
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    if cam_list.GetSize() == 0:
        print("No cameras detected.")
        return None
    cam = cam_list[0]
    cam.Init()
    cam.BeginAcquisition()
    return cam, system

def stream_frames(cam, frame_count, width, height, fmt):
    frame_size = GetFrameSize(width, height, fmt)
    frames = []

    try:
        for _ in range(frame_count):
            image_result = cam.GetNextImage()
            if image_result.IsIncomplete():
                print("Image incomplete with image status %d..." % image_result.GetImageStatus())
                continue
            
            image_data = image_result.GetNDArray()
            # convert to three channel to grayscale
            image_data = cv2.cvtColor(image_data, cv2.COLOR_GRAY2BGR)
            # convert to grayscale to yuv
            image_data = cv2.cvtColor(image_data, cv2.COLOR_BGR2YUV)
            # split the yuv image
            y, u, v = cv2.split(image_data)
            frames.append(y.flatten())  # Flatten the colour image data to 1D array
            image_result.Release() # Release the image buffer

    except Exception as e:
        print(f"Error capturing frames: {e}")

    return np.array(frames)

def encode(gpuID, frames: np.array , enc_file_path, width, height, fmt, use_cpu_memory, config_params):
    frame_size = GetFrameSize(width, height, fmt)
    with open(enc_file_path, "wb") as enc_file:
        nvenc = nvc.CreateEncoder(width, height, fmt, use_cpu_memory, **config_params)  # create encoder object
        for frame in frames:
            if frame.size != 0:
                bitstream = nvenc.Encode(frame)  # encode frame one by one
                bitstream = bytearray(bitstream)
                enc_file.write(bitstream)
        print("Flushing encoder queue")
        bitstream = nvenc.EndEncode()  # flush encoder queue
        bitstream = bytearray(bitstream)
        enc_file.write(bitstream)

def sample_usage():
    output_file_path = "C:/Users/alifa/Documents/aquire-video/test_files/streamed_video.h264"
    
    
    total_num_frames = 1000
    
    # Initialize camera
    cam, system = initialize_camera()
    if not cam:
        return

    # Camera settings
    format = "NV12"  # NV12, YUV444, 
    width  = cam.Width.GetValue()
    height = cam.Height.GetValue()
    
    # Capture frames
    frames = stream_frames(cam, total_num_frames, width, height, format)

    # Encode captured frames
    encode(
        0,                      
        frames,                  # np.array of frames 
        output_file_path,        # Output file path
        width,                   # pixel width
        height,                  # pixel height
        format,                  # 
        use_cpu_memory=True, 
        config_params={}
    )

    # print(f"Encoding {len(frames)} frames to {enc_file_path}")
    
    
    # Cleanup
    cam.EndAcquisition()
    cam.DeInit()
    del cam
    system.ReleaseInstance()

if __name__ == "__main__":
    sample_usage()
