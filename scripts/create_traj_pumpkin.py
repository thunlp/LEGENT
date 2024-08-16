from legent import Environment, ResetInfo, TaskCreator, Controller, TrajectorySaver

# env = Environment(env_path=None, use_animation=False) # significantly increase the sampling rate without using animations
env = Environment(env_path="auto", use_animation=False, camera_resolution_width=1024, camera_resolution_height=1024, camera_field_of_view=60) # significantly increase the sampling rate without using animations

def generate_tasks():
    from legent import generate_scene

    tasks = []
    for i in range(10):
        print(f"Generate task {i}")
        task = {
            "task": "Go to the Pumpkin.",
            "plan": ["Go to the Pumpkin."]
        }
        scene = generate_scene(object_counts={"LowPolyInterior_Pumpkin": 1}) # Ensure that the generated scene contains a pumpkin.
        
        object_id = {instance['prefab']: i for i, instance in enumerate(scene['instances'])}['LowPolyInterior_Pumpkin']
        task['solution'] = [f"goto({object_id})"]
        task['scene'] = scene

        tasks.append(task)
    return tasks

try:
    saver = TrajectorySaver()
    tasks = generate_tasks()
    for task in tasks:
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