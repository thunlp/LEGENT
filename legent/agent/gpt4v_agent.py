from legent.agent.agent import AgentClient
import base64
from io import BytesIO
from PIL import Image
from typing import List
import numpy as np
from legent.action.action import parse_action, Action
from legent.utils.io import log


def encode_image_file(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def encode_image_array(image_np):
    image_pil = Image.fromarray(image_np)
    buffer = BytesIO()
    image_pil.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    encoded_string = base64.b64encode(image_bytes).decode("utf-8")
    return encoded_string


def encode_task(obs_history: List[np.array], action_history: List[str], prompt):
    messages = [{"role": "system", "content": [{"type": "text", "text": prompt}]}]
    message_trajectory = {"role": "user", "content": []}
    assert len(obs_history) == 1 + len(action_history)
    for i in range(len(action_history)):
        message_trajectory["content"].append({"type": "text", "text": "Observation:"})
        message_trajectory["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image_array(obs_history[i])}"}})
        message_trajectory["content"].append({"type": "text", "text": f"Action: {action_history[i]}\n"})
    message_trajectory["content"].append({"type": "text", "text": "Observation:"})
    message_trajectory["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image_array(obs_history[-1])}"}})

    messages.append(message_trajectory)
    messages.append({"role": "user", "content": [{"type": "text", "text": "Action(Note that your action MUST be the aforementioned 'action code'.): "}]})
    return messages


class GPT4VAgentClient(AgentClient):
    def __init__(self, prompt: str, api_key=None, base_url=None) -> None:
        import openai

        if api_key:
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

        self.images_history = []
        self.action_history = []
        self.prompt = prompt
        super().__init__(ssh="")

    def send_chat(self, messages):
        response = self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=messages,
            max_tokens=50,
            n=1,
            stop=["\n"],
            temperature=0.0,
        )
        ret = response.choices[0].message.content
        return ret

    def clear_history(self):
        self.images_history = []
        self.action_history = []
        return Action()

    def request_action(self, obs):
        self.images_history.append(obs.image)

        messages = encode_task(self.images_history[-6:], self.action_history[-5:], self.prompt.format(self.current_chat))
        action = self.send_chat(messages)

        try:
            if action.startswith("Action: "):
                action = action[len("Action: ") :]
            log("GPT4-V action: " + action)
            self.action_history.append(action)
            action = parse_action(action)
        except:
            log("failed to parse response to action. skip.")
            action = Action()
        return action
