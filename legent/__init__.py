from legent.server.server import serve, launch, set_scenes_dir
from legent.utils.io import load_json, store_json, save_image, scene_string, time_string, get_latest_folder, get_latest_folder_with_suffix
from legent.environment.env import Environment
from legent.action.action import Action, ResetInfo, ActionFinish
from legent.action.observation import Observation
from legent.server.scene_generator import generate_scene
import argparse
import os
from legent.environment.env_utils import download_env
from legent.dataset.task import TaskCreator
from legent.dataset.controller import Controller
from legent.dataset.trajectory import TrajectorySaver
from legent.agent.agent import AgentClient
from legent.agent.gpt4v_agent import GPT4VAgentClient
from legent.dataset.eval import task_done
from legent.action.action import parse_action
from legent.action.api import SaveTopDownView


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("function", help="serve or play")

    parser.add_argument(
        "--time_scale",
        default=1.0,
        action="store",
        help="time scale to accelerate the game",
    )
    parser.add_argument(
        "--use_default_scene",
        default=False,
        action="store_true",
        help="use default scene on initialization",
    )
    parser.add_argument(
        "--scenes",
        default="",
        action="store",
        help="user pre-defined scene files under a directory rather than instantly generated scene files",
    )
    parser.add_argument(
        "--env_path",
        default="",
        action="store",
        help="the executable file of the game client",
    )
    parser.add_argument(
        "--ssh",
        default="",
        action="store",
        help="username@host:port",
    )
    
    parser.add_argument('--thu', action='store_true', help='download from tsinghua cloud rather than huggingface hub')
    
    args = parser.parse_args()
    if args.function == "serve":
        serve(args.use_default_scene)
    elif args.function == "launch":
        launch(args.env_path, args.ssh, args.use_default_scene)
    elif args.function == "download":
        download_env(args.thu)
        download_env(args.thu, download_env_data=True)