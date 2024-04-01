import threading
import requests
import queue
import io
from PIL import Image
from legent.action.action import Action, ActionFinish, parse_action
from legent.utils.io import log, parse_ssh, SSHTunnel


class AgentClient:
    def __init__(self, ssh: str, remote_model_port: int = 50050) -> None:
        self.MODEL_PORT = 50050
        if ssh:
            host, port, username, password = parse_ssh(ssh)
            self.ssh_tunnel = SSHTunnel(host, port, username, password, self.MODEL_PORT, remote_model_port)
        self.ssh = ssh

        self.request_queue = queue.Queue()  # Queue for storing requests
        self.response_queue = queue.Queue()  # Queue for storing responses

        worker_thread = threading.Thread(target=self.request_handler)
        worker_thread.daemon = True  # Set as a daemon thread so it will automatically quit if the main program exits
        worker_thread.start()

        self.current_chat = ""  # The chat from the user that is currently under processing
        self.is_waiting_response = False

    def request_handler(self):
        while True:
            try:
                obs = self.request_queue.get(timeout=1)  # Avoid endless polling of an empty queue, saving CPU resources, and ensures timely responses to new requests.
                if isinstance(obs, str) and obs == "#RESET":
                    action = self.clear_history()
                    self.response_queue.put(action)
                else:
                    action = self.request_action(obs)
                    self.response_queue.put(action)
            except queue.Empty:
                continue

    def act(self, obs):
        if obs.text:
            self.current_chat = obs.text
            self.request_queue.put("#RESET")
            self.is_waiting_response = True

        if self.is_waiting_response:  # check if the request has return
            try:
                action = self.response_queue.get_nowait()
                self.is_waiting_response = False
                if isinstance(action, ActionFinish):
                    self.current_chat = ""
                return action
            except queue.Empty:
                return Action()

        # send new request if current chat exists
        if self.current_chat:
            self.request_queue.put(obs)
            self.is_waiting_response = True
        return Action()

    def clear_history(self):
        url = f"http://127.0.0.1:{self.MODEL_PORT}/clear_history"
        response = requests.get(url)
        return Action()

    def request_action(self, obs):
        image = Image.fromarray(obs.image)
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        buffered.seek(0)

        # Set up the image and text data
        files = {"image": buffered}
        data = {"text": self.current_chat}

        url = f"http://127.0.0.1:{self.MODEL_PORT}/get_action"
        response = requests.post(url, files=files, data=data)

        try:
            action = response.json()["action"]
            action = parse_action(action)
        except:
            log("failed to parse response to action. skip.")
            # TODO: better implementation for invalid action return
            action = Action(json_actions=f"INVALID ACTION: {response.json()['action']}")
        return action

    def close(self):
        if self.ssh:
            self.ssh_tunnel.close()
