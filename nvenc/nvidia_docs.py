
            
            self.cai = []
            self.cai.append(AppCAI(
            (height, width, 1), 
            (width, 1, 1), 
            "|u1", self.gpuAlloc))
            chroma_alloc = int(self.gpuAlloc) 
            + width * height
            self.cai.append(AppCAI((int(height / 2), 
            int(width / 2), 2), 
            (width, 2, 1), 
            "|u1", 
            chroma_alloc))
            self.frameSize = nv12_frame_size
    def cuda(self):
        return self.cai

encoder = nvc.CreateEncoder(
          1920,
          1080, 
         "NV12", False)
input_frame = AppFrame(
          1920, 
          1080, 
          "NV12")
bitstream = encoder.Encode(input_gpu_frame)