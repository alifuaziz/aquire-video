import ffmpeg

def convert_to_h265(input_file, output_file):
    (
        ffmpeg
        .input(input_file)
        .output(output_file, 
                vcodec='hevc_nvenc',  # Use NVIDIA HEVC encoder
                acodec='aac',         # Audio codec
                video_bitrate='4M',   # Set video bitrate
                )
        .global_args('-hwaccel', 'cuda')  # Hardware acceleration
        .run(overwrite_output=True)
    )

# Example usage
input_video = 'test_files/random_noise_video.mp4'
output_video = 'test_files/output_video.mp4'
convert_to_h265(input_video, output_video)
