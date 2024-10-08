import time
import os
import random
import re
import time
from typing import Literal
import numpy as np
from legent.server.scene_generator import generate_scene, prefabs
from legent.utils.config import TASKS_FOLDER
from legent.utils.io import store_json, load_json_from_toolkit, time_string, scene_string, log_green, log
from legent.utils.math import is_point_on_box
from legent.dataset.chat_prompt import get_prompt


class ChatAPI:
    def __init__(self, api_key=None, base_url=None) -> None:
        import openai

        if api_key:
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

    def send_chat(self, messages):
        response = self.client.chat.completions.create(
            model="gpt-4",  # 'gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-4', 'gpt-4-32k'
            messages=messages,
            max_tokens=None,
            n=1,
            stop=None,
            temperature=0.7,
        )
        ret = response.choices[0].message.content
        return ret


registered_api = [ChatAPI]


def chat_api():
    global registered_api

    def decorator(api_class):
        registered_api.append(api_class)
        log(f"register API: {api_class.__name__}")
        return api_class

    return decorator


class ChatBase:
    def __init__(self, api_key=None, base_url=None) -> None:
        global registered_api
        self.chat_api = registered_api[-1](api_key, base_url)

    def send_chat(self, messages):
        return self.chat_api.send_chat(messages)


class TaskCreator(ChatBase):

    def create_task_for_scene_by_hardcoding(self, task_type=Literal["come", "goto", "take", "bring", "put", "where", "exist"], scene=None, room_num=2):
        # TODO: verified the correctness of all cases

        def get_random_object(scene):
            object_candidates = []
            for i, instance in enumerate(scene["instances"]):
                if instance["type"] == "interactable":
                    object_candidates.append(i)
            object_id = random.choice(object_candidates)
            object_name = scene["instances"][object_id]["prefab"].split("_")[1]
            return object_id, object_name

        def get_random_target(scene, object_id):
            target_candidates = []
            for i, instance in enumerate(scene["instances"]):
                if i != object_id and "Floor" not in instance["prefab"] and "Wall" not in instance["prefab"]:
                    target_candidates.append(i)
            target_id = random.choice(target_candidates)
            target_name = scene["instances"][object_id]["prefab"].split("_")[1]
            return target_id, target_name

        def get_on_which_object(scene, object_id):
            on_candidates = []
            object_pos = scene["instances"][object_id]["position"]
            on_id, on_name = None, None
            # get all candidates Floor->Table->Plate->Apple, [Floor, Table, Plate]
            for i, instance in scene["instances"]:
                # TODO: get size from observation.game_states
                pos, size, rot = np.array(instance["position"]), np.array(prefabs[instance["prefab"]]["size"]), np.array(instance["rotation"])
                if i != object_id and is_point_on_box(object_pos, pos, size, box_rotation=rot):  # TODO: consider more
                    on_candidates.append(i)
            max_y = -100
            on_id = None
            for i in on_candidates:
                if scene["instances"][i]["position"]["y"] > max_y:
                    max_y = scene["instances"][i]["position"]["y"]
                    on_id = i

            if on_id is not None:
                on_name = scene["instances"][on_id]["prefab"].split("_")[1]
            return on_id, on_name

        # generate a scene
        if not scene:
            scene = generate_scene(room_num=room_num)

        # generate (task, plan, solution) triplets
        if task_type == "come":
            task = "Come here."
            solution = ["goto_user()"]
            plan = ["Go to the user."]

        elif task_type == "goto":
            object_id, object_name = get_random_object(scene)
            task = f"Go to the {object_name}."
            solution = [f"goto({object_id})"]
            plan = [f"Go to the {object_name}."]

        elif task_type == "take":
            object_id, object_name = get_random_object(scene)
            task = f"Take the {object_name}."
            solution = [f"goto({object_id})", "grab()"]
            plan = [f"Go to the {object_name}.", "Grab the object."]

        elif task_type == "bring":
            object_id, object_name = get_random_object(scene)
            task = f"Bring the {object_name}."
            solution = [f"goto({object_id})", "grab()", "goto_user()"]
            plan = [f"Go to the {object_name}.", "Grab the object.", "Go to the user."]

        elif task_type == "put":
            object_id, object_name = get_random_object(scene)
            target_id, target_name = get_random_target(scene, object_id)
            task = f"Put the {object_name} on the {target_name}."
            solution = [f"goto({object_id})", "grab()", f"goto({target_id})", "release()"]
            plan = [f"Go to the {object_name}.", "Grab the object.", f"Go to the {target_name}.", "Release the object."]

        elif task_type == "where":
            # TODO: use ChatGPT
            object_id, object_name = get_random_object()
            on_id, on_name = get_on_which_object(scene, object_id)
            task = f"Where is the {object_name}?"
            reply = f"It's on the {on_name}."
            solution = [f"goto({object_id})", f'speak("{reply}")']
            plan = [f"Go to the {object_name}.", "Reply to the user."]

        elif task_type == "exist":
            # create "Yes"
            object_id, object_name = get_random_object()
            on_id, on_name = get_on_which_object(scene, object_id)
            task = f"Is there a {object_name} on the {on_name}."
            reply = "Yes."
            solution = [f"goto({on_id})", f'speak("{reply}")']
            plan = [f"Go to the {on_name}.", "Reply to the user."]
            # TODO: create "No" (select a on_id and get all objects on it. random select one object not included.)

        sample = {"task": task, "plan": plan, "solution": solution, "scene": scene}
        samples = [sample]
        return samples

    def create_task_for_scene_by_prompting(self, task_type=Literal["come", "goto", "take", "bring", "put", "where", "exist"], scene=None, sample_num=1):
        if not scene:
            scene = generate_scene()

        task_prompt = {p["type"]: p for p in load_json_from_toolkit("dataset/task-prompts.json")}[task_type]
        if task_prompt["TYPE"] == "instrution following":
            system_message = "You are a user in the room. You need to ask a robot do something."
        else:
            system_message = "You are a user in the room. You need to ask a robot some questions."

        scene_str = scene_string(scene)

        scene_description = f"You are in a room with the following objects(in table format):\n{scene_str}"

        # TODO: give more examples to improve the results. use inputs and outputs from hardcoding as examples
        examples = [f"Task: {e['example']}; Plan: {e['plan']}; Solution: {e['solution']}" for e in task_prompt["examples"]]
        task_prompt["example"] = "\n".join(examples)
        # TODO: Add descriptions for functions goto_user(), goto(object_id), grab(), release().
        task_description = f"""You need to {task_prompt['message']}
You need to propose {sample_num} independent tasks and corresponding solutions, in the format of "Task: task; Plan: plan; Solution: solution.", with no line breaks between the three (use ';' to seperate). 
One sentence in Plan should match one function call in Solution, and the Solution should contain only the following instructions and no other irrelevant output:
1. goto_user()
2. goto(object_id): go to the object and look at it
3. find(object_id): find the object to answer where it is (no need to approach it)
4. grab(): grab the object you are looking at
5. release(): put the grabbed object onto what you have gone to
6. speak(text)
For example (The examples are from other scenes. The number means object_id):
{task_prompt['example']}
"""
        content = f"{scene_description}\n{task_description}"
        messages = [
            {"role": "system", "content": system_message},
            {"role": "assistant", "content": task_prompt["example"]},  # this message can ensure the format correct
            {"role": "user", "content": content},
        ]

        ret = self.send_chat(messages)

        log_green(f"<g>Send to LLM</g>:\n{content}\n<g>Received from LLM</g>:\n{ret}")

        task_lines = [task for task in ret.split("\n") if task]
        samples = []
        for task in task_lines:
            task, plan, solution = task.split("; ")
            task, plan, solution = task.split(": ")[1], plan.split(": ")[1], solution.split(": ")[1]
            sample = {"task": task, "plan": plan.split(". "), "solution": solution.split(", "), "scene": scene}
            samples.append(sample)
        print({"task": task, "plan": plan, "solution": solution})
        time.sleep(0.5)
        return samples

    def create_task_for_scene_by_chatting(self, scene=None):
        raise NotImplementedError

    def create_tasks(self, task_types=None, method: Literal["hardcoding", "prompting", "chatting"] = "hardcoding", scene_num=1):
        if not task_types:
            task_types = [p["type"] for p in load_json_from_toolkit("dataset/task-prompts.json")]
        save_path = f"{TASKS_FOLDER}/{method}/{time_string()}"
        create_func = {
            "hardcoding": self.create_task_for_scene_by_hardcoding,
            "prompting": self.create_task_for_scene_by_prompting,
            "chatting": self.create_task_for_scene_by_chatting,
        }[method]
        all_samples = []

        for task_type in task_types:
            task_save_path = f"{save_path}/{task_type}"
            os.makedirs(task_save_path)

            for scene_id in range(scene_num):
                samples = create_func(task_type)
                all_samples.extend(samples)
                for sample_id, sample in enumerate(samples):
                    store_json(sample, f"{task_save_path}/scene{scene_id}_task{sample_id}.json")

        return all_samples

    def create_scene_for_task_by_hardcoding(self, task_type="where", object_cands=None, receptacle_cands=None, room_num=1):
        # TODO: add goto task to this function
        if task_type == "where":
            if object_cands is None:
                object_cands = ["Orange", "Apple", "Banana", "Cola"]
            object_text = {"Orange": "orange", "Apple": "apple", "Banana": "banana", "Cola": "cola"}
            object_prefab = {"Orange": "LowPolyInterior_Orange", "Apple": "LowPolyInterior_Apple", "Banana": "LowPolyInterior_Banana", "Cola": "LowPolyInterior_Cola"}

            if receptacle_cands is None:
                receptacle_cands = ["Sofa", "Kitchen_Chair", "Table", "Bar", "Dresser"]  # Kitchenchair, Giftbox
            receptacle_text = {"Sofa": "sofa", "Kitchen_Chair": "chair", "Table": "table", "Bar": "countertop", "Dresser": "dresser"}

            exclusions = {"Banana-Kitchen_Chair"}
            while True:
                object_name = random.choice(object_cands)
                receptacle_name = random.choice(receptacle_cands)
                if f"{object_name}-{receptacle_name}" not in exclusions:
                    break

            receptacle_object_counts = {receptacle_name: {"count": 1, "objects": [{object_name: 1}]}}
            # receptacle_object_counts = {"Sofa": {"count": 1, "objects": [{"Apple": 1}]}}
            object_id = -1
            loop_count = 0
            # Banana KitchenChair
            # Apple Sofa
            while object_id == -1:  # Failed to put the object
                # print(".", end="", flush=True)
                # print(receptacle_object_counts)
                scene = generate_scene(receptacle_object_counts=receptacle_object_counts, room_num=room_num)
                loop_count += 1
                if loop_count > 4:
                    raise Exception(f"failed to put {object_name} on {receptacle_name} after many attempts")
                for i, instance in enumerate(scene["instances"]):
                    if instance["prefab"] == object_prefab[object_name]:
                        object_id = i
                        break
            question_text = object_text[object_name]
            answer_text = receptacle_text[receptacle_name]
            task = f"Where is the {question_text}?"
            reply = f"It's on the {answer_text}."
            solution = [f"find({object_id})", f'speak("{reply}")']
            plan = [f"Go to the {question_text}.", "Reply to the user."]
            sample = {"task": task, "plan": plan, "solution": solution, "scene": scene, "answer": answer_text}
            return sample
        else:
            raise NotImplementedError

    def create_scenes_for_task_by_hardcoding(self, task_type="where", scene_num=1):
        return [self.create_scene_for_task_by_hardcoding(task_type=task_type) for i in range(scene_num)]


class ChatAnnotator(ChatBase):
    def __init__(self, api_key=None, base_url=None, add_history=False):
        super().__init__(api_key, base_url)
        self.add_history = add_history
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]

    def _annotate_solution(self, user_chat, game_states):
        prompt = get_prompt(user_chat, game_states)
        messages = self.messages + [{"role": "user", "content": prompt}]
        return self.send_chat(messages)

    def annotate_solution(self, user_chat, game_states):
        solution = self._annotate_solution(user_chat, game_states)
        if self.add_history:
            messages += [{"role": "user", "content": user_chat}, {"role": "assistant", "content": solution}]
            reserved_turn = 3
            if len(messages) > 1 + reserved_turn * 2:
                messages = messages[:1] + messages[-reserved_turn * 2 :]
        log_green(f"<g>user:</g>\n{user_chat}")
        log_green(f"<g>agent:</g>\n{solution}")
        if solution == "" or solution.startswith("<!doctype html>"):
            solution = 'speak("Request failed.")'

        apis = ["speak", "speak_without_look", "play", "goto_user", "goto", "goto_point", "toggle", "put_in_drawer", "goto_and_grab", "grab", "goto_and_grab", "release", "look", "open", "speak_and_play"]

        def is_valid(p):
            for action in p.split("\n"):
                action = action.strip()
                if any([action.startswith(f"{api}(") for api in apis]) and action.endswith(")"):
                    continue
                else:
                    print(f"solution '{action}' not valid, skip")
            return True

        def post_process(p):
            if is_valid(p):
                res = []
                for action in p.split("\n"):
                    action = action.strip()
                    try:
                        func = action.split("(", maxsplit=1)[0]
                        arg = action.split("(", maxsplit=1)[1][:-1].strip('"')
                    except:
                        continue
                    res.append(func + ":" + arg)
                for i in range(len(res) - 1):
                    if res[i].startswith("look") and res[i + 1].startswith("speak"):  # TODO: refactor the logic
                        res[i + 1] = "speak_without_look:" + res[i + 1].split(":", maxsplit=1)[1]
                return "\n".join(res)
            else:
                if "\n" not in p and not re.search(r"[a-z]", p):
                    return f"speak:{p}"
                return ""

        solution = post_process(solution.strip())
        return solution
