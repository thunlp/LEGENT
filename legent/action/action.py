from typing import Dict, List
from legent.protobuf.communicator_pb2 import ActionProto
from legent.server.scene_generator import generate_scene
import json
import re


class Action:

    def __init__(
        self,
        type: str = "STEP",
        text: str = "",
        json_actions: str = "",
        move_right: int = 0,
        move_forward: int = 0,
        rotate_right: float = 0,  # degrees
        rotate_down: float = 0,
        jump: bool = False,
        grab: bool = False,
        teleport_forward: float = 0,
        use_teleport: bool = False,  # whether to use teleport mode
        look_x: float = 0,
        look_y: float = 0,
        use_look_at: bool = False,  # whether to use look-at-image-point mode
        action_choice: int = -1, # used in option-base mode
        api_calls: List[str] = [],
    ) -> None:
        self.type = type
        self.text = text
        self.json_actions = json_actions

        self.move_right: int = move_right
        self.move_forward: int = move_forward
        self.rotate_right: float = rotate_right
        self.rotate_down: float = rotate_down
        self.jump: bool = jump
        self.grab: bool = grab

        self.teleport_forward: float = teleport_forward

        self.use_teleport: bool = use_teleport

        self.look_x: float = look_x
        self.look_y: float = look_y
        self.use_look_at: bool = use_look_at
        
        self.action_choice: int = action_choice

        self.api_calls: List[str] = api_calls

    def build(self) -> ActionProto:
        return ActionProto(
            type=self.type,
            text=self.text,
            json_actions=self.json_actions,
            float_actions=[self.move_right, self.move_forward, self.rotate_right, self.rotate_down] + [self.jump, self.grab, self.teleport_forward, self.look_x, self.look_y] + [self.action_choice],
            int_actions=[self.use_teleport, self.use_look_at],
            api_calls=json.dumps({"calls": self.api_calls}),
        )

    def to_string(self):
        action_strings = []
        if self.teleport_forward:
            action_strings.append(f"move_forward({self.teleport_forward:.1f})")  # TODO: avoid move_forward(0.0)
        if self.rotate_right:
            action_strings.append(f"rotate_right({int(self.rotate_right)})")
        if self.rotate_down:
            action_strings.append(f"rotate_down({int(self.rotate_down)})")
        if self.grab:
            action_strings.append(f"grab()")
        if self.text:
            action_strings.append(f'speak("{self.text}")')

        return ", ".join(action_strings)


class ActionFinish(Action):
    def to_string(self):
        return "finish()"


class ResetInfo:

    def __init__(self, scene: Dict = None, api_calls: List[str] = []) -> None:
        if not scene:
            scene = generate_scene()
        self.json_actions = json.dumps(scene)
        self.api_calls = api_calls

    def build(self) -> ActionProto:
        return ActionProto(type="RESET", json_actions=self.json_actions, api_calls=json.dumps({"calls": self.api_calls}))


def parse_float(elem):
    match = re.search(r"\((.*?)\)", elem)
    if match:
        param = match.group(1)
        try:
            result = float(param)
            return result
        except ValueError:
            return None
    else:
        return None


def parse_string(elem):
    match = re.search(r"\(\"(.*?)\"\)", elem)
    if match:
        param = match.group(1)
        return param
    else:
        return None


def parse_action(action_string):
    action = Action(use_teleport=True)
    for elem in action_string.split(", "):
        if elem.startswith("move_forward"):
            teleport_forward = parse_float(elem)
            if teleport_forward:
                action.teleport_forward = teleport_forward
        elif elem.startswith("rotate_right"):
            rotate_right = parse_float(elem)
            if rotate_right:
                action.rotate_right = rotate_right
        elif elem.startswith("rotate_down"):
            rotate_down = parse_float(elem)
            if rotate_down:
                action.rotate_down = rotate_down
        elif elem.startswith("speak"):
            text = parse_string(elem)
            if text:
                action.text = text
        elif elem.startswith("finish"):
            action = ActionFinish()
    return action
