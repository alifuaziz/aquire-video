import pip 
import numpy as np
import PySpin
import PyNvVideoCodec as pynvcodec

CHUNK_SIZE = 10  # Number of frames to encode at a time

def initialize_camera():
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    
    if cam_list.GetSize() == 0:
        print("No camera found.")
        return None

    camera = cam_list.GetByIndex(0)
    camera.Init()

    # Check if PixelFormat is writable
    # pixel_format_node = camera.GetNodeMap().GetNode('PixelFormat')
    # 
    # if PySpin.IsAvailable(pixel_format_node) and PySpin.IsWritable(pixel_format_node):
    #     # Cast to IEnumeration
    #     pixel_format_enum = PySpin.IEnumeration(pixel_format_node)
    #     if pixel_format_enum is not None:
    #         # Get the desired entry (e.g., RGB8)
    #         entry = pixel_format_enum.GetEntryByName('RGB8')  # Use the appropriate format
    #         if entry is not None:
    #             pixel_format_enum.SetIntValue(entry.GetValue())
    #             print("Pixel format set to RGB8.")
    #         else:
    #             print("Desired pixel format not available.")
    #     else:
    #         print("Pixel format enumeration is not accessible.")
    # else:
    #     print("Pixel format is not writable or not available.")

    return camera



def print_camera_settings(camera):
    nodemap = camera.GetNodeMap()
    width = PySpin.CIntegerPtr(nodemap.GetNode('Width'))
    height = PySpin.CIntegerPtr(nodemap.GetNode('Height'))
    payload_size = PySpin.CIntegerPtr(nodemap.GetNode('PayloadSize'))

    print("Width:", width.GetValue())
    print("Height:", height.GetValue())
    print("Payload Size:", payload_size.GetValue())




def encode_frames(raw_frame_chunk, width, height, output_file):
    encoder = pynvcodec.CreateEncoder(width, height, "NV12", usecpuinutbuffer=True)
    
    
    
    for i in range(CHUNK_SIZE):
        chunk = raw_frame_chunk[i:i+10]
        
        bitstream = encoder.Encode(chunk)
        # BUG: The bitstream is empty
        with open(output_file, 'wb') as out_file:
            print("Writing to file")
            out_file.write(bitstream)
            
    
    
    
    # # Create a file to write the output
    # with open(output_file, 'wb') as out_file:
    #     for frame in raw_frame_chunk:
    #         # Convert raw frame to the required format if necessary
    #         encoded_frame = encoder.Encode(frame)
        
        
    #         out_file.write(encoded_frame)

    # encoder.EndEncode()


def main():
    # Get list of cameras
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    cam = cam_list.GetByIndex(0)
    # Start streaming and check if it is streaming
    cam.Init()
    cam.BeginAcquisition()
       
    # Create empty numpy array to store raw frames
    raw_frame_chunk = np.empty((CHUNK_SIZE, cam.Height(), cam.Width()), dtype=np.uint8)
    # raw_frame_chunk = []
    for _ in range(CHUNK_SIZE):  # Capture a fixed number of frames
        image_result = cam.GetNextImage()
        if image_result.IsIncomplete():
            print("Image incomplete with image status: {}".format(image_result.GetImageStatus()))
            continue
        
        # Get the raw data and append to raw_frames
        raw_data = image_result.GetNDArray()
        # append raw data to raw_frames numpy array
        raw_frame_chunk[_] = raw_data
        # raw_frame_chunk.append(raw_data)
        

    # Set your desired output file path
    output_file = 'output.h264'
    # Encode the chunk of frames
    encode_frames(
        raw_frame_chunk, 
        image_result.GetWidth(), 
        image_result.GetHeight(), 
        output_file
        )

    camera.EndAcquisition()
    camera.DeInit()
    del camera

if __name__ == "__main__":
    main()
