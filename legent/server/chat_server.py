from legent.dataset.task import ChatAnnotator
from legent.utils.io import log, log_green, load_json, store_json
from multiprocessing import Process
import socket
import os


PORT_FOR_CLIENT = 7899

PARAMS_BUFFER = "chat_server_params_buffer.json"


def write_params_buffer(api_key, base_url):
    store_json({"api_key": api_key, "base_url": base_url}, PARAMS_BUFFER)


def read_params_buffer():
    if not os.path.exists(PARAMS_BUFFER):
        return None
    params = load_json(PARAMS_BUFFER)
    os.remove(PARAMS_BUFFER)
    return params


def serve_main():
    from flask import Flask, request, Response

    app = Flask(__name__)

    params = read_params_buffer()

    chat_annotator = ChatAnnotator(api_key=params["api_key"], base_url=params["base_url"], add_history=False)

    @app.route("/annotate_solution", methods=["POST"])
    def annotate_solution():
        global messages
        json_data = request.json
        user_chat = json_data["chat"]
        game_states = json_data["game_states"]
        solution = chat_annotator.annotate_solution(user_chat, game_states)
        logging.info(f"Chat: {user_chat} Solution: {solution}")
        response = Response(solution, mimetype="text/plain")
        return response

    # Disable Flask logging
    import flask.cli
    import logging

    flask.cli.show_server_banner = lambda *args: None
    logging.getLogger("werkzeug").disabled = True

    log_green("chat server started")
    app.run(debug=True, use_reloader=False, port=PORT_FOR_CLIENT, host="0.0.0.0")


def serve_chat(api_key, base_url):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        in_use = s.connect_ex(("localhost", PORT_FOR_CLIENT)) == 0
    if in_use:
        log("chat server already started, skip")
        return None
    else:
        read_params_buffer()
        if api_key:
            write_params_buffer(api_key, base_url)
        server = Process(target=serve_main)
        server.start()
        return server
