from legent import Environment, AgentClient, GPT4VAgentClient
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
args = parser.parse_args()
if args.ssh is None and args.api_key is None:
    print("No --ssh or --api_key parameters provided. Ensure your model and environment are running locally.")

def interact():
    env = Environment(env_path="auto", run_options={"port": 50054})
    if args.api_key is None:
        agent = AgentClient(ssh=args.ssh, remote_model_port=args.remote_model_port)
    else:
        agent: GPT4VAgentClient = GPT4VAgentClient(api_key=args.api_key, base_url=args.base_url)
    obs = env.reset()
    try:
        while True:
            action = agent.act(obs)
            obs = env.step(action)
    finally:
        env.close()
        agent.close()


interact()
