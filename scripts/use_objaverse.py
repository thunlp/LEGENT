import objaverse
import objaverse.xl as oxl
import pandas as pd
import trimesh

from legent import Environment, Observation, generate_scene, ResetInfo, get_mesh_size, load_json
from legent.utils.config import ENV_FOLDER
import random

objaverse._VERSIONED_PATH = f"{ENV_FOLDER}/objaverse"


def objaverse_object(uid):
    objects = objaverse.load_objects([uid])
    return list(objects.values())[0]


def objaverse_object_info(uid, raw=False):
    annotation = objaverse.load_annotations([uid])[uid]
    if raw:
        return annotation
    info = {
        "uid": uid,
        "name": annotation["name"],
        "tags": [tag["name"] for tag in annotation["tags"]],
        "categories": [cat["name"] for cat in annotation["categories"]],
        "description": annotation["description"],
        "vertex_count": annotation["vertexCount"],
        "url": annotation["viewerUrl"],
    }
    return info


def try_objaverse():  # NOT annotated. The annotations are noisy.
    uids = objaverse.load_uids()

    # Sample some objects
    sample_uids = random.sample(uids, 5)
    for uid in sample_uids:
        info = objaverse_object_info(uid)
        print(info["name"], info)

    # Find the cherry-picked example shown in https://objaverse.allenai.org/objaverse-1.0
    # annotations = objaverse.load_annotations(uids)
    # uid = [uid for uid, annotation in annotations.items() if annotation["name"] == "Spicy Ramen Noodle"][0]
    uid = "101c08b5c8534944b43959b142a140b1"
    info = objaverse_object_info(uid)
    print(info["name"], info)

    # Download the model
    path = objaverse_object(uid)

    # Visualize the model
    trimesh.load(path).show()


def try_objaverse_lvis():  # Annotated with categories but much less objects
    # Get the information: 1156 categories, 46207 objects
    annotations = objaverse.load_lvis_annotations()
    # print(list(annotations.keys()))
    print("Categories:", len(annotations), "Objects:", sum([len(annotations[category]) for category in annotations]))

    # Sample a model from a category and print its information
    uids = annotations["Christmas_tree"]
    print("Christmas_tree Objects:", len(uids))
    uid = uids[0]  # random.choice(uids)
    info = objaverse_object_info(uid)
    print(info["name"], info)

    # Download the model
    path = objaverse_object(uid)

    # Visualize the model
    trimesh.load(path).show()


def try_objaverse_xl():  # NOT annotated. See https://huggingface.co/datasets/allenai/objaverse/discussions/7
    annotations: pd.DataFrame = oxl.get_annotations(download_dir=f"{ENV_FOLDER}/objaverse-xl")
    print(annotations)


# try_objaverse()
# try_objaverse_lvis()
# try_objaverse_xl()


uid2size = {}


def use_uid2size():
    global uid2size
    if not uid2size:
        # Download from https://drive.google.com/file/d/1VhY_E0SGVsVVqBbO-sF6LzQrtCfI7SN2/view?usp=sharing
        # TODO: Change the path to the downloaded file
        uid2size = load_json("objaverse_holodeck_uid2size.json")


def get_scale(uid, verbose=False):
    global uid2size
    file_path = objaverse_object(uid)
    mesh_size = get_mesh_size(file_path)
    size = uid2size[uid]
    scale = size / mesh_size
    scale = [max(scale), max(scale), max(scale)]
    if verbose:
        return mesh_size, size, scale
    return list(scale)


if __name__ == "__main__":
    env = Environment(env_path=None)

    try:

        def build_scene_with_custom_objects():
            scene = generate_scene(room_num=1)

            # Download and use any object with gltf or glb format
            # For example, download the glb file and extract it from https://sketchfab.com/3d-models/lays-classic-hd-textures-free-download-d6cbb11c15ab4db4a100a4e694798279#download
            # The lays chips
            # scene["instances"].append({"prefab": "path/to/lays_classic__hd_textures__free_download.glb", "position": [1, 0.1, 1], "rotation": [90, 0, 0], "scale": [1, 1, 1], "type": "interactable"})

            # Use objects from objaverse

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
            asset = objaverse_object(uid)

            use_uid2size()
            if uid in uid2size:
                y_size = uid2size[uid][1]
                scale = get_scale(uid)
            else:
                # If the size is not available, make the longest side of the mesh to be 1.
                # This is not the correct way to scale the object, but better than loading the original huge object.
                mesh_size = get_mesh_size(asset)
                scale = 1 / max(mesh_size)
                y_size = mesh_size[1] * scale
                scale = [scale, scale, scale]

            scene["instances"].append({"prefab": asset, "position": [2, y_size / 2, 2], "rotation": [0, 0, 0], "scale": scale, "type": "kinematic"})
            return scene

        obs: Observation = env.reset(ResetInfo(build_scene_with_custom_objects()))
        while True:
            if obs.text == "#RESET":
                scene = build_scene_with_custom_objects()
                env.reset(ResetInfo(scene))
            obs = env.step()
    finally:
        env.close()
