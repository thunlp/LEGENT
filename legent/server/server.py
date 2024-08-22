from legent.environment.env import Environment
from legent.environment.env_utils import launch_executable, get_default_env_path

from legent.server.chat_server import serve_chat
from legent.server.scene_server import serve_scene
from legent.utils.config import DEFAULT_GRPC_PORT
from legent.utils.io import log, parse_ssh, SSHTunnel
import time


def launch(executable_path, ssh: str, scene, use_env=False, launch_scene_server=True, chat_api_key=None, chat_base_url=None):
    scene_server, chat_server = None, None
    if launch_scene_server:
        scene_server = serve_scene(scene)
    if chat_api_key:
        chat_server = serve_chat(chat_api_key, chat_base_url)
    if ssh:
        host, port, username, password = parse_ssh(ssh)
        ssh_tunnel = SSHTunnel(host, port, username, password, DEFAULT_GRPC_PORT, DEFAULT_GRPC_PORT)

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
                if process.poll() is not None:  # client is closed manually
                    break
    finally:
        log("exit")
        if scene_server:
            scene_server.terminate()
            scene_server.join()
        if chat_server:
            chat_server.terminate()
            chat_server.join()
        if use_env:
            env.close()
        else:
            process.terminate()
        if ssh:
            ssh_tunnel.close()
