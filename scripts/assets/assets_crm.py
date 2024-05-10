from legent import Environment, Observation, ResetInfo, generate_scene, get_mesh_size, convert_obj_to_gltf
import os

env = Environment(env_path="auto")


def create_scene_with_generated_objects():
    scene = generate_scene(room_num=1)

    # Download the generated example from https://drive.google.com/file/d/1do5HyqUjEC76Rqg8ZSz0l8wgqHhbhUxP/view?usp=sharing
    # Or generate the assets using the CRM model from https://github.com/thu-ml/CRM
    # TODO: Change this to the path of the generated OBJ file, e.g., "F:/Downloads/卡通猫/tmpkiwg7ab4.obj"
    crm_generated_obj = "/path/to/generated/model.obj"

    crm_converted_gltf = "converted_example.gltf"
    asset_path = os.path.abspath(crm_converted_gltf)

    # NOTE: Here we convert the assets in runtime. However, it is recommended to convert the assets beforehand and use the converted assets directly.
    convert_obj_to_gltf(crm_generated_obj, crm_converted_gltf)
    asset_size = get_mesh_size(asset_path)

    scale = 0.1  # Make it smaller to resemble a toy.
    y = asset_size[1] / 2 * scale  # Position it so that it sits right on the ground.

    # Add the generated object to the scene
    scene["instances"].append({"prefab": asset_path, "position": [2, y, 2], "rotation": [0, 0, 0], "scale": [scale, scale, scale], "type": "interactable"})

    return scene


try:
    obs: Observation = env.reset(ResetInfo(create_scene_with_generated_objects()))
    while True:
        if obs.text == "#RESET":
            scene = create_scene_with_generated_objects()
            env.reset(ResetInfo(scene))
        obs = env.step()
finally:
    env.close()
