from legent.server.scene_generator import generate_scene, complete_scene
from legent.environment.env import Environment
from legent.environment.env_utils import get_default_env_data_path, launch_executable, get_default_env_path
from legent.utils.io import log, log_green, load_json, load_json_from_toolkit, parse_ssh, SSHTunnel
from flask import Flask, jsonify, request
import requests
from multiprocessing import Process
import subprocess
import socket
import time
import os
import json
from typing import Dict
import pkg_resources


PORT_FOR_CLIENT = 9876
app = Flask(__name__)


@app.route("/")
def create_world():
    config = get_config()
    if "next_scene" in config:
        response = config['next_scene']
        # del config['next_scene'] # use the same scene all the time
    elif "scenes_file" in config:
        scene = load_json(config["scenes_file"][config["scenes_id"]])
        if "prompt" in scene:
            response = scene
        else:
            response = complete_scene(scene) 
        config["scenes_id"] = (config["scenes_id"] + 1) % len(config["scenes_file"])
    else:
        response = generate_scene(config["object_counts"])
        log("generate a new scene")
    return jsonify(response)


@app.route("/config")
def create_config():
    config = get_config()
    log(f"request env config: {config}")
    response = {
        "id": config["id"],
        "time_scale": config["time_scale"],  # 20.0 is suitable for training
        "max_steps": config["max_steps"],  # 0 means infinite
    }
    return jsonify(response)


@app.route("/set_scenes_dir")
def _set_scenes_dir():
    scenes = request.args.get("scenes")
    config = get_config()

    if scenes:
        config["scenes"] = scenes
        config["scenes_file"] = get_files_under(config["scenes"])
        config["scenes_id"] = 0
    else:
        if "scenes_file" in config:
            del config["scenes_file"]
    return jsonify({"status": "ok"})


@app.route("/set_next_scene")
def _set_next_scene():
    scene = request.get_json()
    config = get_config()
    config["next_scene"] = scene
    return jsonify({"status": "ok"})


@app.route("/set_object_counts")
def set_object_counts():
    object_counts = request.get_json().get("object_counts", {})
    config = get_config()
    config["object_counts"] = object_counts
    return jsonify({"status": "ok"})


# api provided for trainning code
def set_scenes_dir(scene_files_dir: str = "") -> bool:
    try:
        response = requests.get(
            f"http://localhost:{PORT_FOR_CLIENT}/set_scenes_dir",
            params={"scenes": scene_files_dir},
        )
        return json.loads(response.text)["status"] == "ok"
    except Exception:
        return False
    

def set_next_scene(scene):
    try:
        response = requests.get(
            f"http://localhost:{PORT_FOR_CLIENT}/set_next_scene",
            json=scene,
        )
        return json.loads(response.text)["status"] == "ok"
    except Exception:
        return False
    

# api provided for trainning code
def set_object_counts(object_counts: Dict[str, int]) -> bool:
    try:
        response = requests.get(
            f"http://localhost:{PORT_FOR_CLIENT}/set_object_counts",
            headers={'Content-Type': 'application/json'},
            json={"object_counts": object_counts}
        )
        return json.loads(response.text)["status"] == "ok"
    except Exception:
        return False


def get_files_under(path):
    files = [
        file
        for file in os.listdir(path)
        if not os.path.isdir(os.path.join(path, file)) and str(file).endswith(".json")
    ]
    files = [os.path.join(config["scenes"], file) for file in sorted(files)]
    return files


DEFAULT_CONFIG = {
    "id": 0,
    "time_scale": 1.0,  # 20.0 is suitable for training
    "max_steps": 500,
    "scenes": "",
    "object_counts": {}
}


def init_config():
    global config
    try:
        config = load_json("env_config.json")
        if config["scenes"]:
            config["scenes_file"] = get_files_under(config["scenes"])
            config["scenes_id"] = 0
    except Exception:
        config = DEFAULT_CONFIG
    config["object_counts"] = {}
    return config


def get_config():
    try:
        return config
    except Exception:
        return init_config()


def serve_main():
    # Disable Flask logging
    import flask.cli

    import logging
    flask.cli.show_server_banner = lambda *args: None
    logging.getLogger("werkzeug").disabled = True

    log_green("scene server started")
    app.run(debug=True, use_reloader=False, port=PORT_FOR_CLIENT, host="0.0.0.0")
    
    
def serve(use_default_scene):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        in_use = s.connect_ex(("localhost", PORT_FOR_CLIENT)) == 0
    if in_use:
        log("scene server already started, skip")
        return None
    else:
        server = Process(target=serve_main)
        server.start()
        if use_default_scene:
            time.sleep(0.1)
            set_next_scene(load_json(f'{get_default_env_data_path()}/scene-default.json'))
        return server
    

def launch(executable_path, ssh:str, use_default_scene, use_env=False, launch_scene_server=True):
    if launch_scene_server:
        server = serve(use_default_scene)
    if ssh:
        host, port, username, password = parse_ssh(ssh)
        ssh_tunnel = SSHTunnel(host, port, username, password, 50051, 50051)
    
    time.sleep(0.5)
    log("launching the client...")
    if not executable_path:
        executable_path = get_default_env_path()
    if use_env:
        env = Environment(executable_path)
    else:
        process = launch_executable(executable_path, [])  # Launch the executable file

    try:
        while True:
            if use_env:
                env.step()
            else:
                if process.poll() is not None: # client is closed manually
                    break
    finally:
        log("exit")
        if server:
            server.terminate()
            server.join()
        if use_env:
            env.close()
        else:
            process.terminate()
        if ssh:
            ssh_tunnel.close()

