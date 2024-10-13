""" This script demonstrates how to hide/show/move an object immediately through the API calls, which is useful when you want to customize the interaction logic.

# API calls explanation

- HideObject(object_id): Hide the object with the specified object_id.
- ShowObject(object_id): Show the object with the specified object_id.
- MoveObject(object_id, position, rotation): Move the object with the specified object_id to the specified position and rotation.
- AgentTargetObjectID(): Get the object_id of the object that the agent is looking at.
- PlayerTargetObjectID(): Get the object_id of the object that the player is looking at.


# Script usage

After running the script, you can type the following commands in the chat box to interact with the scene:
- hide: Hide the object that the player is looking at.
- hide <object_id>: Hide the object with the specified object_id.
- show <object_id>: Show the object with the specified object_id.
- grab: Hide the object that the player is looking at if the player is close to the object.
- move: Move the object that the player is looking at to a higher position.

"""

from legent import Environment, Observation, Action
from legent.action.api import HideObject, ShowObject, MoveObject, AgentTargetObjectID, PlayerTargetObjectID
from legent.utils.math import vec_xz, distance
import re

env = Environment(env_path="auto")
try:
    obs: Observation = env.reset()
    while True:
        api_calls = []
        if obs.text == "#RESET":
            env.reset()
        elif obs.text == "hide":
            obs = env.step(Action(api_calls=[PlayerTargetObjectID()]))
            object_id = int(obs.api_returns["object_id"])
            api_calls.append(HideObject(object_id))
        elif obs.text.startswith("hide"):
            object_id = int(re.findall(r"\d+", obs.text)[0])
            api_calls.append(HideObject(object_id))
        elif obs.text.startswith("show"):
            object_id = int(re.findall(r"\d+", obs.text)[0])
            api_calls.append(ShowObject(object_id))
        elif obs.text.startswith("grab"):
            obs = env.step(Action(api_calls=[PlayerTargetObjectID()]))
            object_id = int(obs.api_returns["object_id"])
            if distance(vec_xz(obs.game_states["instances"][object_id]["position"]), vec_xz(obs.game_states["player"]["position"])) < 2:
                api_calls.append(HideObject(object_id))
        elif obs.text == "move":
            obs = env.step(Action(api_calls=[PlayerTargetObjectID()]))
            object_id = int(obs.api_returns["object_id"])
            object = obs.game_states["instances"][object_id]
            pos, rot = object["position"], object["rotation"]
            api_calls.append(MoveObject(object_id, [pos["x"], pos["y"] + 1, pos["z"]], [rot["x"], rot["y"], rot["z"]]))

        obs = env.step(Action(api_calls=api_calls))
finally:
    env.close()
