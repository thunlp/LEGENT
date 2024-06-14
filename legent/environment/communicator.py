import grpc
from typing import Callable, Optional
from multiprocessing import Pipe
import time
from concurrent.futures import ThreadPoolExecutor
from legent.protobuf.communicator_pb2_grpc import CommunicatorServicer, add_CommunicatorServicer_to_server
from legent.protobuf.communicator_pb2 import ActionProto, ObservationProto
import json


class CommunicatorServicerImplementation(CommunicatorServicer):
    def __init__(self):
        self.parent_conn, self.child_conn = Pipe()

    def Initialize(self, request, context):
        self.child_conn.send(request)
        return self.child_conn.recv()

    def GetAction(self, request, context):
        self.child_conn.send(request)
        return self.child_conn.recv()


# Function to call while waiting for a connection timeout.
# This should raise an exception if it needs to break from waiting for the timeout.
PollCallback = Callable[[], None]


class RpcCommunicator:
    def __init__(self, port: int):
        """
        Python side of the grpc communication. Python is the server and game is the client

        :int port: Port number to communicate with game environment.
        """
        self.port = port
        self.server = None
        self.unity_to_external = None
        self.is_open = False
        self.create_server()

    def create_server(self):
        """
        Creates the GRPC server.
        """
        try:
            # Establish communication grpc
            self.server = grpc.server(
                thread_pool=ThreadPoolExecutor(max_workers=10),
                options=(("grpc.so_reuseport", 1),),
            )
            self.unity_to_external = CommunicatorServicerImplementation()
            add_CommunicatorServicer_to_server(
                self.unity_to_external, self.server
            )
            # Using unspecified address, which means that grpc is communicating on all IPs
            # This is so that the docker container can connect.
            self.server.add_insecure_port("[::]:" + str(self.port))
            self.server.start()
            self.is_open = True
        except Exception:
            raise Exception(
                "Worker In Use:\n"
                f"Couldn't start communication because port {self.port} is still in use. "
                "You may need to manually close a previously opened environment "
                "or use a different port."
            )

    def poll_for_timeout(self, poll_callback: Optional[PollCallback] = None) -> None:
        """
        Polls the GRPC parent connection for data, to be used before calling recv.  This prevents
        us from hanging indefinitely in the case where the environment process has died or was not
        launched.

        Additionally, a callback can be passed to periodically check the state of the environment.
        This is used to detect the case when the environment dies without cleaning up the connection,
        so that we can stop sooner and raise a more appropriate error.
        """
        # TODO: remove timeout 
        timeout_wait = 600  # Timeout (in seconds) to wait for a response before exiting.
        deadline = time.monotonic() + timeout_wait
        callback_timeout_wait = timeout_wait // 200
        while time.monotonic() < deadline:
            if self.unity_to_external.parent_conn.poll(callback_timeout_wait):
                # Got an acknowledgment from the connection
                return
            if poll_callback:
                # Fire the callback - if it detects something wrong, it should raise an exception.
                poll_callback()

        # Got this far without reading any data from the connection, so it must be dead.
        raise Exception("Time out. The game environment took too long to respond.\n")

    def initialize(
        self, poll_callback: Optional[PollCallback] = None, env_config={}
    ) -> ObservationProto:
        self.poll_for_timeout(poll_callback)
        init_obs = self.unity_to_external.parent_conn.recv()
        inputs = ActionProto(type="INIT", json_actions=json.dumps(env_config))
        self.unity_to_external.parent_conn.send(inputs)
        self.unity_to_external.parent_conn.recv()
        return init_obs

    def exchange(
        self, inputs: ActionProto, poll_callback: Optional[PollCallback] = None
    ) -> Optional[ObservationProto]:
        self.unity_to_external.parent_conn.send(inputs)
        self.poll_for_timeout(poll_callback)
        output = self.unity_to_external.parent_conn.recv()
        return output

    def close(self):
        """
        Sends a shutdown signal to the unity environment, and closes the grpc connection.
        """
        if self.is_open:
            message_input = ActionProto(type="CLOSE")
            self.unity_to_external.parent_conn.send(message_input)
            self.unity_to_external.parent_conn.close()
            self.server.stop(False)
            self.is_open = False
