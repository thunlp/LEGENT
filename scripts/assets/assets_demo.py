from legent import Environment, ResetInfo, generate_scene

env = Environment(env_path="auto")


scene = generate_scene(room_num=1)
# Download the 3D model from https://sketchfab.com/3d-models/lays-classic-hd-textures-free-download-d6cbb11c15ab4db4a100a4e694798279#download
# TODO: Change this to the absolute path of the downloaded glb file, e.g., "F:/Downloads/lays_classic__hd_textures__free_download.glb".
path_to_3d_model = "path/to/lays_classic__hd_textures__free_download.glb"
scene["instances"].append({"prefab": path_to_3d_model, "position": [1, 0.1, 1], "rotation": [90, 0, 0], "scale": [0.5, 0.5, 0.5], "type": "interactable"})

try:
    env.reset(ResetInfo(scene))
    while True:
        env.step()
finally:
    env.close()
