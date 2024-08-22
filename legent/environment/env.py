from typing import Optional, Dict
import subprocess
from legent.environment.env_utils import launch_executable, download_env, get_default_env_path
from legent.environment.communicator import RpcCommunicator
from legent.action.action import Action, ResetInfo
from legent.action.observation import Observation
from legent.server.scene_generator import generate_scene
from legent.utils.config import CLIENT_FOLDER, DEFAULT_GRPC_PORT
import os


class Environment:
    def __init__(self, env_path: Optional[str] = None, run_options: Dict = {}, use_animation=True, camera_resolution_width=448, camera_resolution_height=448, camera_field_of_view=120, rendering_options: Dict = {}, action_mode=0):
        """Initialize the environment.

        Args:
            action_mode (int, optional): 0 is low-level action mode, 1 is options-based action mode. Defaults to 0.
        """
        self._process: Optional[subprocess.Popen] = None
        # RPC is a one-to-one communication method, with each pair of python worker and game client using the same port.
        # If there are multiple environments, multiple different ports are required.
        port = run_options.get("port", DEFAULT_GRPC_PORT)
        self._communicator = RpcCommunicator(port)
        welcome()

        # If the environment name is None, a new environment will not be launched
        # and the communicator will directly try to connect to an existing unity environment (Unity Editor, or an executable file manually open).
        if env_path == "auto":  # TODO: check if up to date
            if not os.path.exists(CLIENT_FOLDER):
                download_env()
            env_path = get_default_env_path()
        if env_path is not None:
            try:
                run_args = ["--width", str(run_options.get("width", 640)), "--height", str(run_options.get("width", 480)), "--port", str(port)]
                rendering_args = ["--background", str(rendering_options.get("background", 1)), "--use_shadows", str(rendering_options.get("use_shadows", 1)),"--use_default_light", str(rendering_options.get("use_default_light", 1)), "--style", str(rendering_options.get("style", 1))]
                self._process = launch_executable(file_name=env_path, args=run_args + rendering_args)
            except Exception:
                self.close()
                raise
        else:
            print(f"Listening on port {port}. " f"Start inference or training by launching the LEGENT environment client.")
        self._communicator.initialize(self._poll_process, {"use_animation": use_animation, "camera_resolution_width": camera_resolution_width, "camera_resolution_height": camera_resolution_height, "camera_field_of_view": camera_field_of_view, "background": rendering_options.get("background", 1), "use_shadows": rendering_options.get("use_shadows", 1), "use_default_light": rendering_options.get("use_default_light", 1), "style": rendering_options.get("style", 1), "action_mode": action_mode})

    def _poll_process(self) -> None:
        """
        Check the status of the subprocess. If it has exited, raise a Exception
        """
        if not self._process:
            return
        poll_res = self._process.poll()
        if poll_res is not None:
            raise Exception("Game client exited")

    def step(self, inputs: Optional[Action] = None) -> Observation:
        # TODO: refine code comments
        if inputs is None:
            inputs = Action()
        if isinstance(inputs, Action):
            inputs = inputs.build()
        outputs = self._communicator.exchange(inputs, self._poll_process)
        return Observation(outputs)

    def reset(self, inputs: Optional[ResetInfo] = None) -> Observation:
        # NOTE: This design is different from most RL environments, as
        # all terminal decisions are made by the backend, allowing reset() and step() to be called in the same way.
        if inputs is None:
            inputs = ResetInfo(scene=generate_scene())
        if isinstance(inputs, Action) or isinstance(inputs, ResetInfo):
            inputs = inputs.build()
        return self.step(inputs)

    def close(self) -> None:
        """
        Close the communicator and environment subprocess (if necessary).
        """
        self._communicator.close()
        if self._process is not None:
            # Wait a bit for the process to shutdown, but kill it if it takes too long
            timeout = 300  # Number of seconds to wait for the environment to shut down beforeforce-killing it.
            try:
                self._process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._process.kill()
            # Set to None so we don't try to close multiple times.
            self._process = None

    def loop(self) -> None:
        try:
            while True:
                self.step()
        finally:
            self.close()


def welcome() -> None:
    print(
        r"""
 ___       ________   ________   ________   ________   _________   
|\  \     |\  _____\ |\   ____\ |\  _____\ |\   ___  \|\___   ___\ 
\ \  \    \ \  \__/  \ \  \___| \ \  \__/  \ \  \\ \  \|___ \  \_| 
 \ \  \    \ \   __\  \ \  \  __ \ \   __\  \ \  \\ \  \   \ \  \  
  \ \  \____\ \  \_|__ \ \  \|\  \\ \  \_|__ \ \  \\ \  \   \ \  \ 
   \ \_______\ \_______\\ \_______\\ \_______\\ \__\\ \__\   \ \__\
    \|_______|\|_______| \|_______| \|_______| \|__| \|__|    \|__|
    """
    )
