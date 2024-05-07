import objaverse
from legent import Environment, Observation, generate_scene, ResetInfo, get_mesh_size, load_json
from legent.utils.config import ENV_FOLDER

objaverse._VERSIONED_PATH = f"{ENV_FOLDER}/objaverse"  # Change the path to save the downloaded objects


# Download from https://drive.google.com/file/d/1VhY_E0SGVsVVqBbO-sF6LzQrtCfI7SN2/view?usp=sharing
# TODO: Change the path to the downloaded file
uid2size = load_json("objaverse_holodeck_uid2size.json")


env = Environment(env_path="auto")

try:

    def create_scene_with_objaverse_objects():
        scene = generate_scene(room_num=1)

        # Some example uids:
        # 000074a334c541878360457c672b6c2e  slipper
        # 5d3a99865ac84d8a8bf06b263aa5bb55  old bed (this model is originally broken)
        # cd956b2abec04b52ac48bea1ec141d60  modern bed (this model have multiple parts)
        # 000a0c5cdc3146ea87485993fbaf5352  statue
        # 493cf761ada14c0bbc1f5b71369d8d93  sofa
        # 7c6aa7d97a8443ce8fdd01bdc5ec9f15  table
        # 20de33c317ce49a687b9fe8075d60e8a  TV
        # TODO: Change this to the uid of the Objaverse object you want to import
        # Or you can use random.choice(list(uid2size.keys())) to randomly select an object
        uid = "000074a334c541878360457c672b6c2e"
        asset_path = list(objaverse.load_objects([uid]).values())[0]

        if uid in uid2size:

            def get_scale(uid, asset_path):
                mesh_size = get_mesh_size(asset_path)
                size = uid2size[uid]
                scale = size / mesh_size
                scale = [max(scale), max(scale), max(scale)]
                return list(scale)

            y_size = uid2size[uid][1]
            scale = get_scale(uid, asset_path)
        else:
            # If the size is not available, make the longest side of the mesh to be 1.
            # This is not the correct way to scale the object, but better than loading the original huge object.
            mesh_size = get_mesh_size(asset_path)
            scale = 1 / max(mesh_size)
            y_size = mesh_size[1] * scale
            scale = [scale, scale, scale]

        scene["instances"].append({"prefab": asset_path, "position": [2, y_size / 2, 2], "rotation": [0, 0, 0], "scale": scale, "type": "kinematic"})
        return scene

    obs: Observation = env.reset(ResetInfo(create_scene_with_objaverse_objects()))
    while True:
        if obs.text == "#RESET":
            scene = create_scene_with_objaverse_objects()
            env.reset(ResetInfo(scene))
        obs = env.step()
finally:
    env.close()
