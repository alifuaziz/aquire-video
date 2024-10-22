import PySpin
import PyNvVideoCodec as nvc
import numpy as np
import ffmpeg



def acquire_images(cam):
    # Start acquisition
    cam.BeginAcquisition()

    try:
        # Retrieve the next available image
        image_result = cam.GetNextImage()

        # Ensure the image is complete
        if image_result.IsIncomplete():
            print(f"Image incomplete with status {image_result.GetImageStatus()}")
        else:
            # Convert image to NumPy array
            image_data = image_result.GetNDArray()
            print(f"Acquired image, size: {image_data.shape}")

        # Release image
        image_result.Release()

    finally:
        # End acquisition
        cam.EndAcquisition()

    return image_data



def compress_frame(frame, codec, width, height):
    # Convert frame to the correct format if necessary
    # (Assuming the frame is already in a valid format for compression)

    # Compress the frame
    enc_frame = codec.EncodeSingleFrame(frame)
    
    # Encoded frame is in the form of bytearray
    print(f"Compressed frame size: {len(enc_frame)} bytes")
    
    return enc_frame


def initialize_codec(width, height, bitrate=4000, fps=30):
    codec = nvc.PyNvEncoder(
        width,         # Video width
        height,        # Video height
        'NV12',        # Codec type
        bitrate,       # Bitrate (4000 kbps by default)
        fps,           # Frame rate (30 fps by default)
        False,         # Enable lossless compression (set to False for H264)
        {'preset': 'hq'}  # Additional parameters
    )
    return codec

def acquire_and_compress_video(cam, codec, output_file, width, height, num_frames=100):
    # Set up the ffmpeg process for video output
    process = (
        ffmpeg
        .input('pipe:', format='rawvideo', pix_fmt='nv12', s=f'{width}x{height}')
        .output(output_file, pix_fmt='yuv420p', vcodec='libx264', r=30)
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )

    # Start acquisition
    cam.BeginAcquisition()

    try:
        for i in range(num_frames):
            # Retrieve the next available image
            image_result = cam.GetNextImage()

            if image_result.IsIncomplete():
                print(f"Image incomplete with status {image_result.GetImageStatus()}")
                continue

            # Convert image to NumPy array
            frame = image_result.GetNDArray()

            # Compress the frame
            enc_frame = codec.EncodeSingleFrame(frame)

            # Write the encoded frame to the ffmpeg process
            process.stdin.write(enc_frame)

            print(f"Frame {i} compressed and processed")

            # Release the image
            image_result.Release()

    finally:
        # End acquisition
        cam.EndAcquisition()
        # Close ffmpeg process
        process.stdin.close()
        process.wait()

# Main function
if __name__ == '__main__':
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    
    if cam_list.GetSize() == 0:
        print("No cameras detected.")
        cam_list.Clear()
        system.ReleaseInstance()
        exit()

    cam = cam_list.GetByIndex(0)
    
    try:
        cam.Init()
        
        # Get camera width and height
        nodemap = cam.GetNodeMap()
        width_node = PySpin.CIntegerPtr(nodemap.GetNode("Width"))
        height_node = PySpin.CIntegerPtr(nodemap.GetNode("Height"))
        
        width = width_node.GetValue()
        height = height_node.GetValue()

        # Initialize codec
        codec = initialize_codec(width, height, bitrate=4000, fps=30)

        # Output file for the compressed video
        output_file = 'output_video.mp4'

        # Acquire and compress video, saving it to the file
        acquire_and_compress_video(cam, codec, output_file, width, height, num_frames=100)

    finally:
        cam.DeInit()
        del cam
        cam_list.Clear()
        system.ReleaseInstance()
