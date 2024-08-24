"""
This script demonstrates how to create custom walls with textures and holes for windows and doors.
"""

from legent import Environment, Observation, ResetInfo
import numpy as np


env = Environment(env_path="auto", camera_resolution_width=1024, camera_field_of_view=120)
try:

    height = 3.2
    square_size = 10
    center = np.array([0, 0, 0])

    scene = {"instances": [], "player": {"position": [0, 0.1, 1], "rotation": [0, 180, 0]}, "agent": {"position": [0, 0.1, -1], "rotation": [0, 0, 0]}, "walls": [], "floors": []}

    # Add a wall with holes for a window and a door
    # Download the texture from https://drive.google.com/file/d/1OQkoPfVIAl-VkUixgrShcGj5FjDPr4XU/view?usp=sharing
    # TODO: Change this to the path of the texture
    texture_path = "F:/Downloads/white-tile-wall-textures-background.jpg"
    scene["walls"].append(
        {
            "position": [0, 2, 0],
            "rotation": [0, 0, 0],
            "size": [4, 4, 0.2],
            # position_xy and size_xy are in the local coordinate system of the wall
            # The origin is at the center of the wall
            "holes": [{"position_xy": [-1, -1], "size_xy": [0.8, 2]}, {"position_xy": [0.5, 0], "size_xy": [1.2, 1.2]}],
            "material": texture_path,
        }
    )

    # Add floor
    # Download the texture from https://drive.google.com/file/d/1KAuP86G37_7VKtSKklos0nwq7DOaAi4i/view?usp=sharing
    # TODO: Change this to the path of the texture
    texture_path = "F:/Downloads/empty-wooden-plank-texture.jpg"
    scene["floors"].append({"position": [0, 0, 0], "rotation": [0, 0, 0], "size": [square_size, 0.2, square_size], "material": texture_path})

    # Add ceiling with a hole
    scene["floors"].append({"position": [0, height, 0], "rotation": [0, 0, 0], "size": [square_size, 0.2, square_size], "holes": [{"position_xz": [3, -3], "size_xz": [4, 4]}], "material": "#E0DFE3"})

    # Add 4 walls around the room
    for i in range(4):
        angle = 90 * i
        rad = angle * np.pi / 180
        direction = np.array([np.cos(rad), 0, np.sin(rad)])
        position = (center + direction * square_size / 2).tolist()
        position[1] = height / 2
        rotation = [0, angle + 90, 0]
        scene["walls"].append({"position": position, "rotation": rotation, "size": [square_size, height, 0.2], "material": "#E0DFE3"})

    obs: Observation = env.reset(ResetInfo(scene))
    while True:
        obs = env.step()
finally:
    env.close()
