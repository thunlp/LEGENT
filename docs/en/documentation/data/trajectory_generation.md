# Trajectory Generation

A trajectory refers to a sequence of `observation, action, observation, action, ...`, which is the training data for embodied agents.

The LEGENT environment can compute optimal controls for a solution based on the internal state of the environment. The `Controller` calculates and executes the optimal control for a solution step by step, obtaining a trajectory from the environment. Using the following code, you can directly generate training data.

``` python
from legent import Environment, ResetInfo, TaskCreator, Controller, TrajectorySaver

env = Environment(env_path="auto", use_animation=False) # significantly increase the sampling rate without using animations
try:
    saver = TrajectorySaver()
    tasks = TaskCreator().create_tasks(task_types=['come', 'goto'], method="hardcoding", scene_num=3) # or load from task files
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
```

The dataset will be saved at `.legent/dataset`.