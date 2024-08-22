from legent.server.server import serve_scene, launch
from legent.utils.io import load_json, store_json, save_image, scene_string, time_string, get_latest_folder, get_latest_folder_with_suffix, pack_scenes, unpack_scenes, find_files_by_extension
from legent.environment.env import Environment
from legent.action.action import Action, ResetInfo, ActionFinish
from legent.action.observation import Observation
from legent.server.scene_generator import generate_scene
import argparse
from legent.environment.env_utils import download_env
from legent.dataset.task import TaskCreator
from legent.dataset.controller import Controller
from legent.dataset.trajectory import TrajectorySaver
from legent.agent.agent import AgentClient
from legent.agent.gpt4v_agent import GPT4VAgentClient
from legent.dataset.eval import task_done
from legent.action.action import parse_action
from legent.action.api import SaveTopDownView, TakePhotoWithVisiblityInfo
from legent.asset.utils import get_mesh_size, get_mesh_vertical_size, convert_obj_to_gltf
import time


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("function", help="serve/launch/download")
    parser.add_argument(
        "--scene",
        default="",
        action="store",
        help="Use the specified scene file",
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
        help="username@host:port,password",
    )
    parser.add_argument(
        "--api_key",
        default=None,
        action="store",
        help="ChatGPT API key for chatting",
    )
    parser.add_argument(
        "--base_url",
        default=None,
        action="store",
        help="",
    )
    parser.add_argument("--thu", action="store_true", help="download from tsinghua cloud rather than huggingface hub")
    parser.add_argument("--dev", action="store_true", help="download dev version from tsinghua cloud")

    args = parser.parse_args()
    if args.function == "serve":
        serve_scene(args.scene)
        while True:
            time.sleep(60)
            pass
    elif args.function == "launch":
        launch(args.env_path, args.ssh, args.scene, False, True, args.api_key, args.base_url)
    elif args.function == "download":
        download_env(args.thu, download_dev_version=args.dev)
        download_env(args.thu, download_env_data=True)
