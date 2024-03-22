import os
from legent.utils.io import save_image, load_json, store_json, time_string
from legent.action.action import ActionFinish
from legent.utils.config import DATASET_FOLDER


class Trajectory:
    def __init__(self, traj_id: str, task_setting) -> None:
        if traj_id is None:
            traj_id = time_string()
        self.traj_id = traj_id
        self.task_setting = task_setting
        self.images = []
        self.actions = []
        self.steps = 0

    def add_image(self, image_array):
        self.images.append(image_array)

    def add_action(self, action):
        if action is None:
            action = ActionFinish()
        self.actions.append(action)
        self.steps += 1


class TrajectorySaver:
    def __init__(self, save_path=None) -> None:
        if not save_path:
            self.save_path = f"{DATASET_FOLDER}/{time_string()}"
        else:
            self.save_path = save_path
        os.makedirs(self.save_path, exist_ok=True)
        self.traj_ids = []
        self.samples = []

    def save_traj(self, traj: Trajectory):
        # make the directory
        traj_id = traj.traj_id
        save_path = f'{self.save_path}/{traj.traj_id}'
        os.makedirs(save_path, exist_ok=True)
        assert len(traj.actions) == len(traj.images)

        # save images
        for i, image in enumerate(traj.images):
            save_image(image, f"{save_path}/{i:04d}.png")

        # save action
        trajectory = [{"image": f"{traj_id}/{i:04d}.png", "action": action.to_string()} for i, action in enumerate(traj.actions)]
        sample = {
            "id": traj_id,
            "interactions": [
                {
                    "from": "human",
                    "text": traj.task_setting["task"]
                },
                {
                    "from": "agent",
                    "trajectory": trajectory
                }
            ]
        }
        store_json(sample, f"{save_path}/trajectory.json")
        store_json(traj.task_setting, f"{save_path}/task_setting.json")

    def save(self):
        dirs = [os.path.join(self.save_path, d) for d in os.listdir(self.save_path) if os.path.isdir(os.path.join(self.save_path, d))]
        samples = [load_json(os.path.join(d, "trajectory.json")) for d in dirs]
        store_json(samples, f"{self.save_path}/trajectories.json")
