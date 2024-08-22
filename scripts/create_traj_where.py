from legent import Environment, ResetInfo, TaskCreator, Controller, TrajectorySaver

env = Environment(env_path="auto", use_animation=False, camera_resolution_width=448, camera_resolution_height=448, camera_field_of_view=120)
scene_num = 100
object_cands = ["Orange", "Apple", "Banana", "Cola"]
receptacle_cands = ["Sofa", "Kitchen_Chair", "Table", "Bar", "Dresser"]

try:
    saver = TrajectorySaver()
    for i in range(scene_num):
        while True:
            try:
                task = TaskCreator().create_scene_for_task_by_hardcoding(task_type="where", object_cands=object_cands, receptacle_cands=receptacle_cands, room_num=2)
                break
            except Exception as e:
                print("Exeption:", e)
                pass
                
        env.reset(ResetInfo(scene=task["scene"]))
        controller = Controller(env, task["solution"])
        traj = controller.collect_trajectory(task, add_finish_action=False)
        if traj:
            # The task has been completed successfully
            saver.save_traj(traj=traj)
            print(f'Complete task "{task["task"]}" in {traj.steps} steps.')
        else:
            print(f'Complete task "{task["task"]}" is invalid. Deserted.')
    saver.save()
finally:
    env.close()
