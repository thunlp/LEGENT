from legent.protobuf.communicator_pb2 import ObservationProto
import json
import io


class Observation:
    def __init__(self, obs: ObservationProto):
        from PIL import Image
        import numpy as np

        self.type = obs.type
        image_stream = io.BytesIO(obs.image)
        # TODO: Remove try-except block and use identifier instead.
        try:
            self.image = np.array(Image.open(image_stream))
            self.frames = [self.image]
        except:
            self.frames = self.unpack_image_sequence(obs.image)
            self.image = self.frames[-1]
        self.text = obs.text
        self.game_states = json.loads(obs.game_states)
        if obs.api_returns:
            self.api_returns = json.loads(obs.api_returns)
        else:
            self.api_returns = None
    
    def unpack_image_sequence(self, bytes_data):
        import io
        from PIL import Image
        import struct
        import numpy as np

        image_sequence_data = bytes_data
        frames = []

        # Create a BytesIO stream from the binary data
        image_stream = io.BytesIO(image_sequence_data)

        # Loop through the sequence and extract each image
        while image_stream.tell() < len(image_sequence_data):
            # Read the size of the next frame
            size_data = image_stream.read(4)
            if not size_data:
                break
            frame_size = struct.unpack('I', size_data)[0]

            # Read the image data for the frame
            frame_data = image_stream.read(frame_size)

            # Open the frame as an image
            frame_stream = io.BytesIO(frame_data)
            frame = np.array(Image.open(frame_stream))
            frames.append(frame)
        return frames