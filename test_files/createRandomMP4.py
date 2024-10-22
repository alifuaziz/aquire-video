import cv2
import numpy as np

# Video settings
width, height = 1280, 720  # Width and height of the video
fps = 30  # Frames per second
duration = 2  # Duration of the video in seconds
bitrate = 4_000_000  # 4 Mbps
output_file = 'random_noise_video.mp4'  # Output file name

# Create a VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4 file
out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

# Total number of frames
total_frames = fps * duration

# Generate and write random noise frames
for _ in range(total_frames):
    # Create a random frame with noise
    random_frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    
    # Write the frame to the video
    out.write(random_frame)

# Release the VideoWriter
out.release()

print(f'Video saved as {output_file}')
