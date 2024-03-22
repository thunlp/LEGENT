from legent import get_latest_folder, load_json, store_json
from legent.utils.config import DATASET_FOLDER


FIXED_PROMPT = """You are a vision language assistant agent with high intelligence.
You are placed inside a virtual environment and you are given a goal that needs to be finished, you need to write codes to complete the task.
You can solve any complex tasks by decomposing them into subtasks and tackling them step by step, but you should only provide the action code for solving the very next subtask.
You need to call the following action apis to complete the tasks:
1. speak(text): reply to the questions.
2. move_forward(meters): move forward a certain distance.
3. rotate_right(degrees): rotate a certain degrees.
4. rotate_down(degrees)
5. grab()
6. release()
"""


def make_instruction_train(task, action_history):
    action_history = f"Previous Actions: {'; '.join(action_history)}\n" if action_history else ""
    return f"{FIXED_PROMPT}Your task: {task}\n{action_history}Please give your next action. The view you see: <image>"


def make_sample(id, task, image, action, action_history):
    return {
        "id": id,
        "image": image,
        "conversations": [
            {
                "from": "human",
                "value": make_instruction_train(task=task, action_history=action_history),
            },
            {
                "from": "gpt",
                "value": action
            }
        ]
    }


example = {'id': '20240311-165946-211047', 'interactions': [{'from': 'human', 'text': 'Come here.'}, {'from': 'agent', 'trajectory': [{'image': '20240311-165946-211047/0000.png', 'action': 'rotate_right(-45)'}, {'image': '20240311-165946-211047/0001.png', 'action': 'rotate_right(-45)'}, {'image': '20240311-165946-211047/0002.png', 'action': 'rotate_right(-15)'}, {'image': '20240311-165946-211047/0003.png', 'action': 'move_forward(0.7)'}, {'image': '20240311-165946-211047/0004.png', 'action': 'finish()'}]}]}


def format_training_data_for_llava(data_folder=None, add_action_history=False):
    if not data_folder:
        data_folder = get_latest_folder(DATASET_FOLDER)
    trajectories = load_json(f"{data_folder}/trajectories.json")
    training_samples = []
    for i, traj in enumerate(trajectories):
        action_history = []

        id = traj['id']
        task = traj['interactions'][0]['text']
        for i, step in enumerate(traj['interactions'][1]['trajectory']):
            step_id = f"{id}-{i:04d}"
            image, action = step['image'], step['action']

            training_samples.append(make_sample(step_id, task, image, action, action_history if add_action_history else None))
            action_history.append(action)

    store_json(training_samples, f"{data_folder}/train-llava.json")


format_training_data_for_llava(add_action_history=False)
