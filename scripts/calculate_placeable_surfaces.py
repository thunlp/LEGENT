from legent.asset.utils import get_placable_surface, get_mesh_size
from legent import Environment, Observation, generate_scene, ResetInfo
import numpy as np

# Download the 3D model from https://sketchfab.com/3d-models/minecraft-workbench-211cc17a34f547debb63c5a034303111#download
# TODO: Change this to the absolute path of the downloaded glb file on your computer
asset = "F:/Downloads/minecraft_workbench.glb"
scale = 1

# Download the 3D model from https://sketchfab.com/3d-models/soviet-sofa-7120d8cfad7e4455b772f3fab4bfd243#download
# TODO: Change this to the absolute path of the downloaded glb file on your computer
asset = "F:/Downloads/soviet_sofa.glb"
scale = 0.01

surfaces = get_placable_surface(asset, visualize=False)


env = Environment(env_path=None)
try:

    def build_scene_with_lights():
        scene = generate_scene(room_num=1)

        asset_position = [2, get_mesh_size(asset)[1] / 2 * scale, 1]
        scene["instances"].append({"prefab": asset, "position": asset_position, "rotation": [0, 0, 0], "scale": [scale, scale, scale], "type": "kinematic"})

        # Visualize the placable surfaces
        if "walls" not in scene:
            scene["walls"] = []
        for surface in surfaces:
            surface_center = [(surface["x_max"] + surface["x_min"]) / 2, surface["y"], (surface["z_max"] + surface["z_min"]) / 2]
            surface_size = [(surface["x_max"] - surface["x_min"]), 0.005 / scale, (surface["z_max"] - surface["z_min"])]

            surface_center = (np.array(surface_center) * scale).tolist()
            surface_size = (np.array(surface_size) * scale).tolist()

            position = (np.array(asset_position) + np.array(surface_center)).tolist()
            scene["walls"].append({"position": position, "rotation": [0, 0, 0], "size": surface_size, "material": "#00CCFF"})

        return scene

    obs: Observation = env.reset(ResetInfo(build_scene_with_lights()))
    while True:
        if obs.text == "#RESET":
            env.reset(ResetInfo(build_scene_with_lights()))
        obs = env.step()
finally:
    env.close()
