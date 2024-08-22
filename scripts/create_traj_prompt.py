import random

from legent import Environment, ResetInfo, TaskCreator, Controller, TrajectorySaver
from legent.dataset.task import chat_api

# @chat_api()
# class CustomChatAPI:
#   ...


env = Environment(env_path="auto", use_animation=False, camera_resolution_width=448, camera_resolution_height=448, camera_field_of_view=120, run_options={"port": 50099})

scene_num = 5

try:
    saver = TrajectorySaver()
    for i in range(scene_num):
        while True:
            try:
                room_num = random.choices([1, 2])[0]

                actions = ["come", "goto", "take", "bring", "put", "exist", "where"]
                actions_weights = [1, 1, 1, 1, 1, 1, 1]  # Corresponding to the weight of each task type
                chosen_action = random.choices(actions, weights=actions_weights, k=1)[0]

                task = TaskCreator().create_task_for_scene_by_prompting(task_type=chosen_action, sample_num=1)[0]

                break
            except Exception as e:
                print("Task Exeption", e)
                pass

        try:
            env.reset(ResetInfo(scene=task["scene"]))
            controller = Controller(env, task["solution"])
            traj = controller.collect_trajectory(task)
            if traj:
                # The task has been completed successfully
                saver.save_traj(traj=traj)
                print(f'Complete task "{task["task"]}" in {traj.steps} steps.')
            else:
                print(f'Complete task "{task["task"]}" failed. Deserted.')
        except Exception as e:
            print("Controller Exeption", e)
            pass
    saver.save()
finally:
    env.close()
