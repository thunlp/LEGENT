from legent import Environment, ResetInfo, TaskCreator, Controller, TrajectorySaver


env = Environment(env_path="auto", use_animation=False, camera_resolution_width=448, camera_resolution_height=448, camera_field_of_view=120, run_options={"port": 50099})  # significantly increase the sampling rate without using animations
scene_num = 1000

try:
    saver = TrajectorySaver()
    for i in range(scene_num):
        while True:
            try:
                task = TaskCreator().create_task_for_scene_by_hardcoding(task_type="come", room_num=2)[0]
                break
            except Exception as e:
                print("Exeption", e)
                pass
                
        env.reset(ResetInfo(scene=task['scene']))
        controller = Controller(env, task['solution'])
        traj = controller.collect_trajectory(task)

        if traj:
            # The task has been completed successfully
            saver.save_traj(traj=traj)
            print(f'Complete task "{task["task"]}" in {traj.steps} steps.')
        else:
            print(f'Complete task "{task["task"]}" failed. Deserted.')
    saver.save()
finally:
    env.close()
