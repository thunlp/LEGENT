from legent import Environment, Observation, ResetInfo
import random

env = Environment(env_path="auto")

# Download the 3D model from https://sketchfab.com/3d-models/minecraft-grass-block-84938a8f3f8d4a0aa64aaa9c4e4d27d3#download
# TODO: Change this to the absolute path of the downloaded glb file, e.g., "F:/Downloads/minecraft_grass_block.glb".
path_to_grass_block = "/path/to/minecraft_grass_block.glb"

# Download the 3D model from https://sketchfab.com/3d-models/minecraft-workbench-211cc17a34f547debb63c5a034303111#download
# TODO: Change this to the absolute path of the downloaded glb file, e.g., "F:/Downloads/minecraft_workbench.glb"
path_to_workbench = "/path/to/minecraft_workbench.glb"


def create_simple_minecraft_scene():
    scene = {"instances": []}

    # Add 10*10 grass blocks
    for x in range(-5, 5):
        for z in range(-5, 5):
            # Stack a random number of grass blocks
            height = random.randint(1, 3)
            for y in range(height):
                scene["instances"].append({"prefab": path_to_grass_block, "position": [x, y + 0.5, z], "rotation": [0, 0, 0], "scale": [0.5, 0.5, 0.5], "type": "kinematic"})
            # Add the player on top of the grass block at (0, 2)
            if x == 0 and z == 2:
                scene["player"] = {"position": [0, height, 2], "rotation": [0, 180, 0]}
            # Add a workbench on top of the grass block at (0, 0)
            elif x == 0 and z == 0:
                scene["instances"].append({"prefab": path_to_workbench, "position": [0, height + 0.5, 0], "rotation": [0, 0, 0], "scale": [1, 1, 1], "type": "kinematic"})
            # Add the agent on top of the grass block at (0, -2)
            elif x == 0 and z == -2:
                scene["agent"] = {"position": [0, height, -2], "rotation": [0, 0, 0]}
    return scene


try:

    obs: Observation = env.reset(ResetInfo(create_simple_minecraft_scene()))
    while True:
        if obs.text == "#RESET":
            env.reset(ResetInfo(create_simple_minecraft_scene()))
        obs = env.step()
finally:
    env.close()
