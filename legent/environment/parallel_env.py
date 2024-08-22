from typing import Dict, NamedTuple, List
from multiprocessing import Process, Pipe, Queue
from multiprocessing.connection import Connection
from queue import Empty as EmptyQueueException
from legent.protobuf.communicator_pb2 import ActionProto, ObservationProto
from legent.environment.env import Environment
from legent.utils.config import DEFAULT_GRPC_PORT


class EnvResponse(NamedTuple):
    worker_id: int
    observations: ObservationProto


class EnvWorker:
    def __init__(self, process: Process, worker_id: int, conn: Connection):
        self.process = process
        self.worker_id = worker_id
        self.conn = conn
        self.waiting_obs = False
        self.alive = True

    def send(self, actions: ActionProto) -> None:
        self.conn.send(actions)

    def recv(self) -> EnvResponse:
        return self.conn.recv()


def worker(parent_conn: Connection, step_queue: Queue, worker_id: int, run_options: Dict) -> None:
    try:
        # Each worker has its own Environment.
        run_options["port"] = DEFAULT_GRPC_PORT + worker_id
        env = Environment(file_name=run_options["file_name"], run_options=run_options)
        while True:
            # The parent_conn only needs to use recv() and does not need to send(), as return values are conveyed through the step_queue.
            actions: ActionProto = parent_conn.recv()
            if actions.type == "STEP" or actions.type == "RESET":
                observations = env.step(actions)
                step_queue.put(EnvResponse(worker_id, observations))
            elif actions.type == "CLOSE":
                break
    except Exception as e:
        raise
    finally:
        env.close()
        parent_conn.close()
        step_queue.put(EnvResponse(worker_id, ObservationProto(type="EXITED")))
        step_queue.close()


class ParallelEnvironment:
    def __init__(self, file_name, num_envs: int = 1, run_options: Dict = {}):
        run_options["file_name"] = file_name
        self.num_envs = num_envs

        self.env_workers: List[EnvWorker] = []
        self.step_queue: Queue = Queue()
        # create env workers
        for worker_id in range(num_envs):
            parent_conn, child_conn = Pipe()
            child_process = Process(
                target=worker,
                args=(child_conn, self.step_queue, worker_id, run_options)
            )
            child_process.start()
            env_worker = EnvWorker(child_process, worker_id, parent_conn)
            self.env_workers.append(env_worker)
        self.workers_alive = self.num_envs

        self.actions = [None for i in range(num_envs)]
        self.reset()
        # welcome()

    def check_waiting(self):
        for worker_id in range(self.num_envs):
            env_worker = self.env_workers[worker_id]
            if not env_worker.alive:
                continue
            if self.actions[worker_id] != None:
                assert not env_worker.waiting_obs
            else:
                assert env_worker.waiting_obs

    def worker_act(self, worker_id: int, actions: ActionProto):
        self.actions[worker_id] = actions

    def worker_reset(self, worker_id):
        self.actions[worker_id] = ActionProto(type="RESET")

    def worker_close(self, worker_id):
        self.actions[worker_id] = ActionProto(type="CLOSE")

    def step(self) -> Dict[int, ObservationProto]:
        """
        Step the environment. Execute actions on specified environments and return observations that have been completed up to now.

        Note that the observations paired with the actions may not be included in the current returns (may be included in the next call or later).
        The actions and observations should be externally paired by using the worker_id.

        Args:
            worker_actions (Dict[int, Dict]): A dictionary that maps worker_ids to actions. The worker_id-th environment will execute worker_actions[worker_id]. 
                The worker_id that is not included indicates that no action should be executed, and the worker_id-th environment continues to wait for observations.

        Returns:
            Dict[int, ObservationProto]: A dictionary that maps worker_ids to observations. Worker_obs[worker_id] is the observations of worker_id-th environment.
                Returning {} indicates that all environments have been closed.
        """
        self.check_waiting()

        # Queue steps for any workers which aren't in the "waiting_obs" state.
        for worker_id in range(self.num_envs):
            env_worker = self.env_workers[worker_id]
            if not env_worker.alive:
                continue
            if self.actions[worker_id] != None:
                # assign action to env_worker according to worker_id
                env_worker.send(self.actions[worker_id])
                env_worker.waiting_obs = True
        self.actions = [None for i in range(self.num_envs)]

        worker_obs: Dict[int, ObservationProto] = {}
        # Poll the step queue for completed steps from environment workers until we retrieve
        # 1 or more, which we will then return as ObservationProto dict
        while len(worker_obs) < 1:
            try:
                while True:
                    step: EnvResponse = self.step_queue.get_nowait()
                    assert step.worker_id not in worker_obs
                    self.env_workers[step.worker_id].waiting_obs = False
                    worker_obs[step.worker_id] = step.observations
                    if step.observations.type == "EXITED":
                        self.env_workers[step.worker_id].alive = False
                        self.workers_alive -= 1
                        if self.workers_alive == 0:
                            return {}
            except EmptyQueueException:
                pass
        return worker_obs

    def reset(self) -> None:
        for worker_id in range(self.num_envs):
            self.worker_reset(worker_id)

    def close(self) -> None:
        self.step_queue.close()
        # Sanity check to kill zombie workers and report an issue if they occur.
        if self.workers_alive > 0:
            for env_worker in self.env_workers:
                if env_worker.process.is_alive():
                    env_worker.process.terminate()
                    print("A SubprocessEnvManager worker did not shut down correctly so it was forcefully terminated.")
        self.step_queue.join_thread()
