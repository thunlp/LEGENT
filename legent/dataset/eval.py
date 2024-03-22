from legent.utils.math import vec_xz, distance
from legent.action.action import Action

COME_DONE_DISTANCE = 2.0

def task_done(task, action: Action, obs, task_setting):
    if task == "come":
        game_states = obs.game_states
        d = distance(vec_xz(game_states["agent"]["position"]), vec_xz(game_states["player"]["position"]))
        done = d < COME_DONE_DISTANCE
        return done, {"distance": d}
    elif task == "where":
        done = task_setting["answer"] in action.text.lower()
        return done, {}
    else:
        raise NotImplementedError
