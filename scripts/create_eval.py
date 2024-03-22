from legent.utils.config import EVAL_FOLDER
from legent import store_json, generate_scene, time_string, TaskCreator, Environment, ResetInfo, Controller
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--task", type=str, default="come", choices=["come", "where"], help="task")
parser.add_argument("--get_steps", type=bool, default=False, help="whether simulate the task to get the ground_truth steps")
parser.add_argument("--num", type=int, default=10, help="evaluation episode num")
args = parser.parse_args()

save_path = f"{EVAL_FOLDER}/{time_string()}-{args.task}/tasks"
os.makedirs(save_path)

eval_episodes = args.num

if args.get_steps:
    env = Environment(env_path="auto", use_animation=False, camera_resolution=448)  # significantly increase the sampling rate without using animations


def agent_player_too_near(task_setting):
    from legent.utils.math import distance
    from legent.dataset.eval import COME_DONE_DISTANCE
    import numpy as np

    scene = task_setting["scene"]
    agent_pos, player_pos = scene["agent"]["position"], scene["player"]["position"]
    agent_pos, player_pos = np.array([agent_pos[0], agent_pos[2]]), np.array([player_pos[0], player_pos[2]])
    d = distance(agent_pos, player_pos)
    return d < COME_DONE_DISTANCE + 1


try:
    for i in range(eval_episodes):
        while True:
            try:
                if args.task == "come":
                    task_setting = TaskCreator().create_task_for_scene_by_hardcoding(task_type="come", room_num=2)[0]

                    # remove settings that the agent and the user are too close
                    if agent_player_too_near(task_setting):
                        print("Desert invalid distance, regenerate")
                        continue
                elif args.task == "where":
                    task_setting = TaskCreator().create_scene_for_task_by_hardcoding(task_type="where", room_num=1)
                break
            except Exception as e:
                print("Exeption", e)
                pass
        if args.get_steps:
            env.reset(ResetInfo(scene=task_setting["scene"]))
            controller = Controller(env, task_setting["solution"])
            traj = controller.collect_trajectory(task_setting, return_invalid=True)
            task_setting["steps"] = len(traj.actions)

        store_json(task_setting, file=f"{save_path}/{i:04d}.json")
finally:
    if args.get_steps:
        env.close()
