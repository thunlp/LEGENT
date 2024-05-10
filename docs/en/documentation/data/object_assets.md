# Object Assets

## Default objects

To Edit

## Import your own 3D objects

We use glTF as the standard import format. It's an **openly specified** 3D format that is widely supported by modern software, offers fast transmission, and can store almost all the properties of a 3D object. The environment can directly import 3D objects in `.gltf` or `.glb` format at runtime without any processing or pre-operations.

!!! Note
    
    Other formats can be easily converted to glTF using softwares like [Blender](https://www.blender.org/). We'll create a tutorial and a one-step script to facilitate this process soon.

#### Minimal example

Here's a simple example of how to import an external 3D object:

``` python

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

```

Download the Lay's chips from [Sketchfab](https://sketchfab.com/3d-models/lays-classic-hd-textures-free-download-d6cbb11c15ab4db4a100a4e694798279#download) or [here](https://drive.google.com/file/d/1zH5Bd6YyHQ-ktbQJ7hn8gk0LzzrgH9NF/view?usp=sharing). Simply replace `prefab` with the absolute path of your 3D model to import it into the scene.

<img src="https://github.com/thunlp/LEGENT/assets/50205889/c9ef44f2-8a76-4c06-a68b-78c05aece05f" width="360" height="240">

#### Advanced example


Let's try using some code to build a simple Minecraft scene. Download the grass block from [Sketchfab](https://sketchfab.com/3d-models/minecraft-grass-block-84938a8f3f8d4a0aa64aaa9c4e4d27d3#download) or [here](https://drive.google.com/file/d/1C9sBx9YuEcSD0mJBj3xzPXM1XMgLRmXh/view?usp=sharing). Download the workbench from [Sketchfab](https://sketchfab.com/3d-models/minecraft-workbench-211cc17a34f547debb63c5a034303111#download) or [here](https://drive.google.com/file/d/1DazVSrljCo0i0bhvEpxs7QqxkACLQMcG/view?usp=sharing) .

Create a scene using the following script:

??? note "Code"

    ``` python
    from legent import Environment, Observation, ResetInfo
    import random

    env = Environment(env_path="auto")

    # Download the 3D model from https://sketchfab.com/3d-models/minecraft-grass-block-84938a8f3f8d4a0aa64aaa9c4e4d27d3#download
    # TODO: Change this to the absolute path of the downloaded glb file, e.g., "F:/ Downloads/minecraft_grass_block.glb".
    path_to_grass_block = "/path/to/minecraft_grass_block.glb"

    # Download the 3D model from https://sketchfab.com/3d-models/minecraft-workbench-211cc17a34f547debb63c5a034303111#download
    # TODO: Change this to the absolute path of the downloaded glb file, e.g., "F:/ Downloads/minecraft_workbench.glb"
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

    ```

The code above is essentially a trivial scene generation algorithm, while Minecraft's scene generation is far more sophisticated.

<img src="https://github.com/thunlp/LEGENT/assets/50205889/607a213a-d38e-451f-9c94-f89bccb0168c" width="360" height="240">

#### Scene generation integration

Integrate your 3D objects into the default scene generation algorithm.

To Edit

## Import Generated 3D objects


<img src="https://github.com/thunlp/LEGENT/assets/50205889/8c795926-cb32-40c3-8980-ebeb7d7137b4" width="200" height="200">
<img src="https://github.com/thunlp/LEGENT/assets/50205889/70591205-5351-42fc-9399-abf9173cefe2" width="200" height="200">


With the continuous advancement of 3D generation technology, it's foreseeable that the quality of generated objects will be very high, making it an excellent supplement to existing object assets. A diverse range of objects is crucial for the generalization of embodied agents. The logic for importing generated objects is the same as for importing regular objects, because the output of 3D generation scripts also needs to conform to mainstream 3D formats.

Here is an example for importing 3D objects generated by [CRM](https://arxiv.org/abs/2403.05034), an advanced image-to-3D method. Download the example object from [here](https://drive.google.com/file/d/1do5HyqUjEC76Rqg8ZSz0l8wgqHhbhUxP/view?usp=sharing) or generate objects using the 3D generation methods yourself.

??? note "Code"

    ```python
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

    ```

## Import Academic Datasets

<img src="https://github.com/thunlp/LEGENT/assets/50205889/3ad646c8-f9b0-4b75-9ecc-cde661d891c5" width="360" height="240">

[Objaverse](https://arxiv.org/abs/2212.08051) is a large dataset of objects that is used in many research works. The demonstration code for importing Objaverse can be found [here](https://github.com/thunlp/LEGENT/blob/main/scripts/assets/assets_objaverse.py). Note that the sizes of objects in Objaverse are inconsistent and don't match real-world settings, so resizing is necessary. This information wasn't originally included in Objaverse. We use the sizes labeled in [Holodeck](https://arxiv.org/abs/2312.09067) to resize the objects, which can be downloaded [here](https://drive.google.com/file/d/1VhY_E0SGVsVVqBbO-sF6LzQrtCfI7SN2/view?usp=sharing).

<img src="https://github.com/thunlp/LEGENT/assets/50205889/5f3fb6f8-d2b5-45fd-b5ee-70bab0303d60" width="360" height="240">
