import cv2
import numpy as np
import PyNvVideoCodec as nvc


VIDEO_PATH = 'test_files/random_noise_video.mp4'
# VIDEO_PATH = 'test_files/random_noise_video.yuv'



# Initialize input video (you can also use a webcam or any other video source)
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print("Error: Could not open video file.")
    exit()

# get video properties
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
bitrate = 4_000_000  # 4 Mbps


# Initialize encoder
# Set up codec parameters (e.g., resolution, framerate, bitrate)
# width, height = 1280, 720
# bitrate = 4_000_000  # 4 Mbps
# fps = 30

encoder = nvc.CreateEncoder(
    width,
    height,
    "NV12",
    True,
    codec='h264',
    )
# Open a file to save the encoded video
output_file = 'test_files/output_video.h264'
with open(output_file, 'wb') as f:
    while True:
        ret, frame = cap.read()

        if not ret:
            break  # End of video or error in reading frame

        # Resize frame to match encoder dimensions
        frame_resized = cv2.resize(frame, (width, height))
        
        # Convert frame to NV12 format
        nv12_frame = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2YUV_I420)


        # resize frame to match encoder dimensions
        nv12_frame = np.ravel(nv12_frame)
        
        # Feed frame to encoder
        encoded_frames = encoder.Encode(nv12_frame)

        # Write encoded frames to output file
        for encoded_frame in encoded_frames:
            print('frame', encoded_frame)
            f.write(encoded_frame)  # Save each encoded frame to the file

    # After feeding all frames, flush the encoder to get any remaining output
    final_frames = encoder.Flush()
    
    for encoded_frame in final_frames:
        f.write(encoded_frame)  # Save the final encoded frames to the file

    encoder.EndEncode()

# Release resources
cap.release()

