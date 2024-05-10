# Scene Generation

A generalized embodied agent needs exposure to a variety of scenes, but constructing these scenes requires extensive manual effort. LEGENT employs automatic scene generation methods and will continue to enhance them.

## Generate a new scene in the client

After launching the client with "legent launch", sending "#RESET" in the chat box will generate a new scene.

## Generate a new scene using code

The following code demonstrates how to end the current scene and regenerate a new one every 10 seconds.

``` python
from legent import Environment, ResetInfo, generate_scene
from time import time
env = Environment(env_path="auto")
try:
    start = time()
    env.reset()
    while True:
        if time() - start > 10:
            start = time()
            env.reset(ResetInfo(generate_scene())) # Equivalent to env.reset()
        else:
            env.step()
finally:
    env.close()
```

After calling `env.reset`, it will not return until the scene is fully loaded and rendered. `env.reset()` accepts a ResetInfo parameter, where ResetInfo.scene is the scene configuration. Below is the explanation for each field in ResetInfo.scene.


| Key       | Descriptions                                   | Details                                                                                                                                                                                                                                                                                                                                                                                                                       |
| --------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| instances | the information of all objects                 | For each instance, `instance['prefab']` is the prefab name of the object. <br> `instance['position']`, `instance['rotation']`, and `instance['scale']` represent the object's position, rotation, and scale, respectively. <br> `instance[type]` is the object's interaction attribute. `"kinematic"` means the object is unaffected by physics; `"interactable"` means it can be interacted with and is affected by physics. |
| player    | the information of the player                  | `player['position']`, `player['rotation']`, and `player['scale']` represent the player's position, rotation, and scale, respectively.                                                                                                                                                                                                                                                                                         |
| agent     | the information of the agent                   | `agent['position']` and `agent['rotation']` represent the agent's position and rotation.                                                                                                                                                                                                                                                                                                                                      |
| lights    | the information of all lights                  | Optional.                                                                                                                                                                                                                                                                                                                                                                                                                     |
| center    | The position of the panoramic top-down camera. | This is the camera position for the top-down view you see when you press the V key to switch views.                                                                                                                                                                                                                                                                                                                           |

If `scene` follows the format above, you can use `env.reset` to build the scene. There are the following sources of scenes:

1. Using the default scene generation algorithm
2. Using predefined scenes
3. Using your own scene generation algorithm
4. Manually constructed scenes or manually modified scenes based on other scenes

The following code demonstrates manually creating a simple scene. The scene includes only a large floor, an order of potato chips, the player and the agent.

``` python
from legent import Environment, ResetInfo
env = Environment(env_path="auto")
scene = {
    "instances": [
        {
            "prefab": "LowPolyInterior_Floor_01",
            "position": [0, 0, 0],
            "rotation": [0, 0, 0],
            "scale": [4, 1, 4],
            "type": "kinematic"
        },
        {
            "prefab": "LowPolyInterior_Potato",
            "position": [0,0.1,0],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "type": "interactable"
        },
    ],
    "player": {
        "position": [0,0.1,1],
        "rotation": [0, 180, 0]
    },
    "agent": {
        "position": [0,0.1,-1],
        "rotation": [0, 0, 0]
    },
    "center": [0, 10, 0],
    "prompt": ""
}
try:
    env.reset(ResetInfo(scene))
    while True:
        env.step()
finally:
    env.close()
```

The following code demonstrates using a predefined scene.

``` python
from legent import Environment, ResetInfo, load_json
import pkg_resources

env = Environment(env_path="auto")
scene = load_json(pkg_resources.resource_filename('legent', 'scenes/scene-default.json'))

try:
    env.reset(ResetInfo(scene))
    while True:
        env.step()
finally:
    env.close()
```

If you need to use your own scene generation algorithm, you can edit the source code of `legent.server.scene_generator.generate_scene` function.

## Debug your scene generation algorithm

If you write your own scene generation algorithm, it often requires repeated debugging. It would be inconvenient if you have to restart the client each time. Below is the recommended practice.

Start the scene generation server.

```
legent serve
```

Start the client.

```
legent launch
```

Press V to change the view to the top-down view. Keep the client running. If you want to generate a new scene, send "#RESET" in the chat box. If your scene generation algorithm changed, just stop and restart `legent serve`.
