from legent import Environment, ResetInfo, generate_scene
from legent import Environment, Observation, generate_scene, ResetInfo, get_mesh_size, load_json
import random
import os

# Download the assets from https://drive.google.com/file/d/11WiKzCYFSMFXB3FO9LKi8mPfFyFirzIo/view?usp=sharing
# TODO: Change this to the path of the extracted assets
path_to_data_folder = "F:/Downloads/procthor_assets"

assets = load_json(f"{path_to_data_folder}/procthor_assets.json")
asset_info = {asset["asset_id"]: asset for asset in assets}

# to absolute path
for asset in assets:
    for mesh in asset["mesh_materials"]:
        for material in mesh["materials"]:
            for map in ["base_map", "metallic_map", "normal_map", "height_map", "occulusion_map", "emission_map", "detail_mask_map", "detail_base_map", "detail_normal_map"]:
                if material[map]:
                    material[map] = os.path.abspath(f"{path_to_data_folder}/{material[map]}")
        

def create_scene_with_procthor_objects():
    scene = generate_scene(room_num=1)
    asset_id = random.choice(assets)["asset_id"]
    asset_id = "Alarm_Clock_1" # "Alarm_Clock_1" "Fridge_15" "Pot_17" "Bowl_18" "Sofa_207_4" "Sofa_210_1"
    path_to_3d_model = os.path.abspath(f"{path_to_data_folder}/{asset_id}/{asset_id}.fbx")
    scene["instances"].append({"prefab": path_to_3d_model, "position": [2, 1 / 2, 1], "rotation": [0, 0, 0], "scale": [1, 1, 1], "type": "kinematic", "mesh_materials": asset_info[asset_id]["mesh_materials"]})

    # Add point lights
    scene["walls"] = []
    scene["lights"] = []
    scene["light_probes"] = []
    for i in range(3):
        for j in range(3):
            light_position = [1+i*2, 2.5, 1+j*2]
            light_rotation = [90, 0, 0]
            scene["walls"].append(
                {"position": light_position, "rotation": light_rotation, "size": [0.1, 0.1, 0.1], "material": "Light"}
            )
            scene["lights"].append(
                {
                    "name": "PointLight0",
                    "lightType": "Point",
                    "position": light_position,
                    "rotation": light_rotation,
                    "color": [1.0, 0.962069, 0.8382353], # [1.0, 0.9133874, 0.5514706]
                    "intensity": 0.6,  # brightness
                    "range": 15,
                    "shadowType": "Soft",
                }
            )
            scene["light_probes"].append({"position": [2, 2.5, 2]})
    return scene

scene = create_scene_with_procthor_objects()
env = Environment(env_path=None)
try:
    obs: Observation = env.reset(ResetInfo(scene))
    while True:
        if obs.text == "#RESET":
            env.reset(ResetInfo(create_scene_with_procthor_objects()))
        obs = env.step()
finally:
    env.close()
