from legent.server.scene_generator import generate_scene, complete_scene

from legent.environment.env_utils import get_default_env_data_path
from legent.utils.io import log, log_green, load_json, store_json

import requests
from multiprocessing import Process
import socket
import os
import json
from typing import Dict


PORT_FOR_CLIENT = 9876

PARAMS_BUFFER = "scene_server_params_buffer.json"


def write_params_buffer(scene):
    store_json({"scene": scene}, PARAMS_BUFFER)


def read_params_buffer():
    if not os.path.exists(PARAMS_BUFFER):
        return None
    params = load_json(PARAMS_BUFFER)
    os.remove(PARAMS_BUFFER)
    return params


def serve_main():
    from flask import Flask, jsonify, request

    app = Flask(__name__)

    params = read_params_buffer()

    @app.route("/")
    def get_scene():
        config = get_config()
        if params:
            response = params["scene"]
        else:
            if "next_scene" in config:
                response = config["next_scene"]
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
        print(config["next_scene"])
        return jsonify({"status": "ok"})

    @app.route("/set_object_counts")
    def set_object_counts():
        object_counts = request.get_json().get("object_counts", {})
        config = get_config()
        config["object_counts"] = object_counts
        return jsonify({"status": "ok"})

    def get_files_under(path):
        files = [file for file in os.listdir(path) if not os.path.isdir(os.path.join(path, file)) and str(file).endswith(".json")]
        files = [os.path.join(config["scenes"], file) for file in sorted(files)]
        return files

    DEFAULT_CONFIG = {"id": 0, "time_scale": 1.0, "max_steps": 500, "scenes": "", "object_counts": {}}  # 20.0 is suitable for training

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

    # Disable Flask logging
    import flask.cli
    import logging

    flask.cli.show_server_banner = lambda *args: None
    logging.getLogger("werkzeug").disabled = True

    log_green("scene server started")
    app.run(debug=True, use_reloader=False, port=PORT_FOR_CLIENT, host="0.0.0.0")


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


def set_object_counts(object_counts: Dict[str, int]) -> bool:
    try:
        response = requests.get(f"http://localhost:{PORT_FOR_CLIENT}/set_object_counts", headers={"Content-Type": "application/json"}, json={"object_counts": object_counts})
        return json.loads(response.text)["status"] == "ok"
    except Exception:
        return False


def serve_scene(scene):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        in_use = s.connect_ex(("localhost", PORT_FOR_CLIENT)) == 0
    if in_use:
        log("scene server already started, skip")
        return None
    else:
        read_params_buffer()
        if scene:
            if os.path.exists(scene):
                write_params_buffer(load_json(scene))
            else:
                if scene=="1":
                    scene_json = load_json(f"{get_default_env_data_path()}/scene-default.json")
                    scene_json["instances"] = scene_json["instances"][:1]
                    scene_json["instances"][0]["prefab"] = "Scene_Interior_Realistic"
                    write_params_buffer(scene_json)
                else:
                    write_params_buffer(load_json(f"{get_default_env_data_path()}/scene-default.json"))
        server = Process(target=serve_main)
        server.start()
        return server
