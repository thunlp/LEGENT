from legent.action.action import Action
from legent.action.observation import Observation
from typing import List, Optional, Dict
import numpy as np
from legent.environment.env import Environment
from legent.utils.math import vec_xz, vec, compute_signed_angle_2d_dir, distance, clip_angle, compute_angle_to_y_axis, compute_angle_to_y_axis_diff
from legent.action.api import *
from legent.dataset.trajectory import Trajectory
import re
from legent.dataset.eval import task_done, COME_DONE_DISTANCE


class Actions:
    def __init__(self) -> None:
        pass

    def init_actions(self, env: Environment) -> None:
        pass

    def get_next_action(self) -> Optional[Action]:
        """Get actions for next step. If all the actions has ended, return None.

        Returns:
            Optional[Action]: The action.
        """
        pass


class TrajectoryNotValidError(Exception):
    """If a trajectory is useful for traing, this error will be raised.
    For example, if the agent does not see the object, it should not answer where it is."""

    def __init__(self, message="trajectory not valid for training"):
        super().__init__(message)


MAX_MOVE_DISTANCE = 2  # for use_teleport = True
MAX_ROTATE_DEGREE = 90  # for all


class PathFollower(Actions):

    def __init__(self, object_id=None, use_teleport=True) -> None:
        self.object_id = object_id
        self.corners: List = None  # corners (List): positions of all corner points on the path.
        self.use_teleport = use_teleport

    def init_actions(self, env: Environment) -> None:
        api_call = PathToObject(self.object_id) if self.object_id else PathToUser()
        obs = env.step(Action(api_calls=[api_call]))
        self.corners = obs.api_returns["corners"]

    def get_next_action(self, obs: Observation) -> Optional[Action]:
        agent_info = obs.game_states["agent"]
        camera = obs.game_states["agent_camera"]
        return self._get_next_action(agent_info["position"], camera["forward"])

    def _get_next_action(self, position, forward) -> Optional[Action]:
        """Get next action.

        Args:
            position (Dict): position of the agent
            forward (Dict): orientation of the agent
        """
        position = vec_xz(position)
        forward = vec_xz(forward)
        REACH_DISTANCE = 0.01 if self.use_teleport else 0.05
        NEAR_DISTANCE = 0.5

        # get next target corner
        while True:
            if not self.corners:
                return None
            corner = vec_xz(self.corners[0])  # target
            if distance(position, corner) < REACH_DISTANCE:  # remove very near targets
                self.corners = self.corners[1:]
            elif distance(position, corner) < NEAR_DISTANCE and len(self.corners) == 1:  # near the last corner (destination)
                return None
            else:
                break

        angle = compute_signed_angle_2d_dir(forward, corner - position)
        angle = clip_angle(angle, MAX_ROTATE_DEGREE)

        action = Action(use_teleport=self.use_teleport)
        if self.use_teleport:
            # need to rotate if not facing the next corner
            if abs(angle) > 1:
                action.rotate_right = angle

            # need to forward and roate
            else:
                max_move_distance = MAX_MOVE_DISTANCE
                # if go to the last corner (destination), do not move too far, otherwise the agent may step onto the object.
                if len(self.corners) == 1:
                    eps_near = 0.02
                    max_move_distance = min(MAX_MOVE_DISTANCE, distance(position, corner) - NEAR_DISTANCE + eps_near)

                forward_distance = distance(position, corner)
                # cannot reach the target corner in one step, just move forward
                if forward_distance > max_move_distance:
                    forward_distance = max_move_distance
                # can reach the corner
                else:
                    # move forward and rotate to next corner
                    self.corners = self.corners[1:]
                    if self.corners:
                        position = corner
                        corner = vec_xz(self.corners[0])
                        angle = compute_signed_angle_2d_dir(forward, corner - position)
                        angle = clip_angle(angle, MAX_ROTATE_DEGREE)
                        if abs(angle) > 1:
                            action.rotate_right = angle
                action.teleport_forward = forward_distance
        else:
            action.move_forward = 1
            if abs(angle) > 1:
                action.rotate_right = angle
        # print(action.to_string())
        return action


class PathFollowerWithVisibilityCheck(PathFollower):
    def __init__(self, object_id=None, use_teleport=True, min_distance=3) -> None:
        super().__init__(object_id, use_teleport)
        self.alreay_in_view = False
        self.min_distance = min_distance

    def init_actions(self, env: Environment) -> None:
        super().init_actions(env)
        obs = env.step(Action(api_calls=[ObjectInView(self.object_id)]))
        self.alreay_in_view = obs.api_returns["in_view"]

    def get_next_action(self, obs: Observation) -> Optional[Action]:
        d = distance(vec_xz(obs.game_states["agent"]["position"]), vec_xz(obs.game_states["instances"][self.object_id]["position"]))

        # The actions will finish when the object is near and visible to the agent.
        if d < self.min_distance and (self.alreay_in_view or (obs.api_returns and obs.api_returns["in_view"])):
            return None
        else:
            action = super().get_next_action(obs)
            if action:
                action.api_calls = [ObjectInView(self.object_id)]
            return action


class LookAt(Actions):

    def __init__(self, object_id=None, use_teleport=True, horizontal_only=False) -> None:
        self.object_id = object_id
        self.use_teleport = use_teleport
        self.horizontal_only = horizontal_only

    def get_next_action(self, obs: Observation) -> Optional[Action]:
        target = vec(obs.game_states["instances"][self.object_id]["position"])

        agent = obs.game_states["agent"]
        camera = obs.game_states["agent_camera"]

        forward = vec(camera["forward"])
        # look at target horizontally
        h_angle = compute_signed_angle_2d_dir(forward, target - vec(agent["position"]))  # must be agent['position'] because rotate is not directly applied to camera but to the agent
        # look at target vertically
        v_angle = compute_angle_to_y_axis_diff(forward, target - vec(camera["position"]))
        h_angle = clip_angle(h_angle, MAX_ROTATE_DEGREE)
        v_angle = clip_angle(v_angle, MAX_ROTATE_DEGREE)
        if self.horizontal_only:
            v_angle = 0

        if abs(h_angle) <= 1:
            h_angle = 0
        if abs(v_angle) <= 1:
            v_angle = 0
        if h_angle == 0 and v_angle == 0:
            return None

        action = Action(use_teleport=self.use_teleport)
        if self.use_teleport:
            action.rotate_right = h_angle
            action.rotate_down = v_angle
        else:
            action.rotate_right = clip_angle(h_angle, 1)  # TODO: verify
            action.rotate_down = clip_angle(v_angle, 1)
        return action


class LookAtWithVisibilityCheck(LookAt):
    def __init__(self, object_id=None, use_teleport=True, horizontal_only=False) -> None:
        super().__init__(object_id, use_teleport, horizontal_only)
        self.alreay_in_view = False

    def init_actions(self, env: Environment) -> None:
        obs = env.step(Action(api_calls=[ObjectInView(self.object_id)]))
        self.alreay_in_view = obs.api_returns["in_view"]

    def get_next_action(self, obs: Observation) -> Optional[Action]:
        if self.alreay_in_view or (obs.api_returns and obs.api_returns["in_view"]):
            return None
        else:
            action = super().get_next_action(obs)
            if action is None and obs.api_returns and obs.api_returns["in_view"] == False:
                raise TrajectoryNotValidError()
            if action:
                action.api_calls = [ObjectInView(self.object_id)]
            return action


class LookStraightAhead(Actions):

    def __init__(self, use_teleport=True) -> None:
        self.use_teleport = use_teleport

    def get_next_action(self, obs: Observation) -> Optional[Action]:
        camera = obs.game_states["agent_camera"]
        forward = vec(camera["forward"])
        v_angle = 90 - compute_angle_to_y_axis(forward)
        v_angle = clip_angle(v_angle, MAX_ROTATE_DEGREE)

        if abs(v_angle) <= 1:
            return None

        action = Action(use_teleport=self.use_teleport)
        if self.use_teleport:
            action.rotate_down = v_angle
        else:
            action.rotate_down = clip_angle(v_angle, 1)
        return action


class Grab(Actions):
    def get_next_action(self, obs: Observation) -> Optional[Action]:
        if obs.game_states["agent_grab_instance"] == -1:
            return Action(grab=True)
        else:
            return None


class Release(Actions):
    def get_next_action(self, obs: Observation) -> Optional[Action]:
        if obs.game_states["agent_grab_instance"] != -1:
            return Action(grab=True)
        else:
            return None


class Speak(Actions):
    def __init__(self, text) -> None:
        self.done = False
        self.text = text

    def get_next_action(self, obs: Observation) -> Optional[Action]:
        if not self.done:
            self.done = True
            return Action(text=self.text)
        else:
            return None


class Controller:
    # Convert a solution to control
    def __init__(self, env: Environment, solution: List[str]) -> None:
        self.solution_steps: List[Actions]
        self.actions_queue = []
        self.env = env

        def parse_arg(input_string):
            return re.search(r"\(\"?(.*?)\"?\)", input_string).group(1)

        for solu in solution:
            if solu == "goto_user()":
                actions = LookStraightAhead()
                self.actions_queue.append(actions)

                actions = PathFollower()
                self.actions_queue.append(actions)
            elif solu.startswith("find("):
                object_id = int(parse_arg(solu))

                actions = PathFollowerWithVisibilityCheck(object_id)
                self.actions_queue.append(actions)

                actions = LookAtWithVisibilityCheck(object_id, horizontal_only=True)
                self.actions_queue.append(actions)
            elif solu.startswith("goto("):
                object_id = int(parse_arg(solution[0]))

                actions = LookStraightAhead()
                self.actions_queue.append(actions)

                actions = PathFollower(object_id)
                self.actions_queue.append(actions)

                actions = LookAt(object_id)
                self.actions_queue.append(actions)
            elif solu.startswith("grab("):
                actions = Grab()
                self.actions_queue.append(actions)
            elif solu.startswith("release("):
                actions = Release()
                self.actions_queue.append(actions)
            elif solu.startswith("speak("):
                actions = Speak(parse_arg(solu))
                self.actions_queue.append(actions)

        self.actions = self.actions_queue.pop(0)
        self.actions.init_actions(self.env)

    def get_next_action(self, obs):
        action = self.actions.get_next_action(obs)
        while action is None and len(self.actions_queue) > 0:  # remove finished actions recursively until action is not None or actions_queue is empty
            self.actions = self.actions_queue.pop(0)
            self.actions.init_actions(self.env)
            action = self.actions.get_next_action(obs)
        return action  # None means the actions has ended.

    def collect_trajectory(self, task_setting, traj_id=None, add_finish_action=True, return_invalid=False):
        traj = Trajectory(traj_id, task_setting)

        obs = self.env.step()
        for i in range(40):
            try:
                action = self.get_next_action(obs)
            except TrajectoryNotValidError:  # invalid trajectory: the agent does not see the object
                break
            if (action is not None) or add_finish_action:
                traj.add_image(obs.image)
                traj.add_action(action)
            if action is None:  # the actions has ended.
                done = True

                task_type = task_setting["task"].split(" ")[0].lower()
                if task_type == "come":
                    done, info = task_done(task_type, action, obs, task_setting)

                if done:
                    return traj
                break  # invalid trajectory: the agent does come to the user within a distance
            obs = self.env.step(action)
        if return_invalid:
            return traj
        return None  # discard the invalid trajectory
