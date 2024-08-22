from legent.protobuf.communicator_pb2 import ObservationProto
import json
import io


class Observation:
    def __init__(self, obs: ObservationProto):
        import skimage  # TODO: use Pillow instead

        self.type = obs.type
        image_stream = io.BytesIO(obs.image)
        self.image = skimage.io.imread(image_stream, plugin="imageio")
        self.text = obs.text
        self.game_states = json.loads(obs.game_states)
        if obs.api_returns:
            self.api_returns = json.loads(obs.api_returns)
        else:
            self.api_returns = None
