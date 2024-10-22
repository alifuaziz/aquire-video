import numpy as np

# Video settings
width, height = 1280, 720  # Width and height of the video
fps = 30  # Frames per second
duration = 2  # Duration of the video in seconds
output_file = 'random_noise_video.yuv'  # Output file name

# Total number of frames
total_frames = fps * duration

# Open the output YUV file
with open(output_file, 'wb') as f:
    for _ in range(total_frames):
        # Generate random YUV data
        y = np.random.randint(0, 256, (height, width), dtype=np.uint8)  # Y channel
        u = np.random.randint(0, 256, (height // 2, width // 2), dtype=np.uint8)  # U channel (subsampled)
        v = np.random.randint(0, 256, (height // 2, width // 2), dtype=np.uint8)  # V channel (subsampled)

        # Write Y channel
        f.write(y.tobytes())
        # Write U channel (subsampled)
        f.write(u.tobytes())
        # Write V channel (subsampled)
        f.write(v.tobytes())

print(f'YUV video saved as {output_file}')
