from legent import Environment, Observation, store_json, ResetInfo, load_json, save_image
import os
from legent.utils.config import EVAL_FOLDER
from legent import get_latest_folder_with_suffix, time_string, task_done, AgentClient, ActionFinish, Action, GPT4VAgentClient
from prompt_template import *
import argparse


parser = argparse.ArgumentParser()
parser.add_argument(
    "--ssh",
    type=str,
    default=None,
    help=r"""
ssh="<username>@<host>".
If you use a non-standard ssh port: "<username>@<host>:<ssh_port>".
If you use password: "<username>@<host>:<ssh_port>,<password>". If there is special character in <password>, please use escape character like this: \"
""",
)
parser.add_argument("--remote_model_port", type=int, default=50050, help="remote model port")
parser.add_argument("--api_key", type=str, default=None, help="api key")
parser.add_argument("--base_url", type=str, default=None, help="base url")
parser.add_argument("--task", type=str, default="come", choices=["come", "where"], help="task")
args = parser.parse_args()
if args.ssh is None and args.api_key is None:
    print("No --ssh or --api_key parameters provided. Ensure your model and environment are running locally.")
if args.api_key is None:
    agent = AgentClient(ssh=args.ssh, remote_model_port=args.remote_model_port)
    model_name = "model"
else:
    prompt = {"come": GPT4V_PROMPT_COME, "where": GPT4V_PROMPT_WHERE}[args.task]
    agent: GPT4VAgentClient = GPT4VAgentClient(api_key=args.api_key, base_url=args.base_url, prompt=prompt)
    model_name = "gpt4v"
env = Environment(env_path="auto", camera_resolution=448, run_options={"port": 50054})
success_count = 0
eval_folder = get_latest_folder_with_suffix(EVAL_FOLDER, args.task)
save_path = f"{eval_folder}/results/{time_string()}-{model_name}"
start_episode, end_episode = 0, 10  # 0, 10
MAX_STEPS = 25
failed_cases = []
try:
    for i in range(start_episode, end_episode):
        print("\n" + "==" * 4 + f"Start episode {i}" + "==" * 4)
        task_setting = load_json(f"{eval_folder}/tasks/{i:04d}.json")
        obs: Observation = env.reset(ResetInfo(scene=task_setting["scene"]))
        obs.text = task_setting["task"]
        traj_save_dir = f"{save_path}/traj{i:04d}"
        os.makedirs(traj_save_dir)
        step = 0
        done = False
        while step < MAX_STEPS:
            action: Action = agent.act(obs)
            obs = env.step(action)
            if action.json_actions.startswith("INVALID ACTION"):
                save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
                print("INVALID", action.json_actions)
                step += 1
            elif action.to_string() != "":
                save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
                print(f"step {step}, action: {action.to_string()}")
                task_type = task_setting["task"].split(" ")[0].lower()
                done, info = task_done(task_type, action, obs, task_setting)
                store_json({"step": step, "action": action.to_string(), "done_after_action": done, "info_after_action": info}, f"{traj_save_dir}/{step:04d}a.json")
                step += 1
                if done:
                    success_count += 1
                    print("Task accomplished.")
                if isinstance(action, ActionFinish) or action.text!="" or done:
                    save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
                    break
        if not done:
            failed_cases.append(i)
            print("Task failed.")
finally:
    env.close()
    agent.close()
result = {"Success Rate": f"{success_count}/{end_episode-start_episode}", "failed cases": failed_cases}
print(result)
store_json(result, f"{save_path}/result.json")
