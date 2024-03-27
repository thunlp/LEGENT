import multiprocessing
from legent import Environment, ResetInfo, TaskCreator, Controller, TrajectorySaver, time_string
from legent.utils.config import DATASET_FOLDER
import time
from datetime import timedelta


def worker(worker_id, save_path, scene_num):
    print(f"Worker {worker_id} started")

    env = Environment(env_path="auto", use_animation=False, camera_resolution=448, camera_field_of_view=120, run_options={"port": 50100 + worker_id})  # significantly increase the sampling rate without using animations

    try:
        saver = TrajectorySaver(save_path=save_path)
        for i in range(scene_num):
            while True:
                try:
                    task = TaskCreator().create_task_for_scene_by_hardcoding(task_type="come", room_num=2)[0]
                    break
                except Exception as e:
                    print("Exeption", e)
                    pass

            env.reset(ResetInfo(scene=task["scene"]))
            controller = Controller(env, task["solution"])
            traj = controller.collect_trajectory(task)

            if traj:
                # The task has been completed successfully
                saver.save_traj(traj=traj)
                print(f'Worker {worker_id}: Complete task "{task["task"]}" in {traj.steps} steps.')
            else:
                print(f'Worker {worker_id}: Complete task "{task["task"]}" failed. Deserted.')
        saver.save()
    finally:
        env.close()
    print(f"Worker {worker_id} finished")


if __name__ == "__main__":
    num_processes = 2
    total_scene_num = 10
    scene_num = total_scene_num // num_processes

    start_time = time.time()

    # Create and start multiple processes
    save_root_folder = f"{DATASET_FOLDER}/{time_string()}"
    processes = []
    for i in range(num_processes):
        p = multiprocessing.Process(target=worker, args=(i, f"{save_root_folder}/{i}", scene_num))
        processes.append(p)

    for p in processes:
        p.start()

    # Wait for all processes to finish
    for p in processes:
        p.join()

    elapsed_time = timedelta(seconds=time.time() - start_time)
    print(f"Program finished in {elapsed_time}")
