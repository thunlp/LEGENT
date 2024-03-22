from legent import Environment, AgentClient, GPT4VAgentClient
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--ssh",
    type=str,
    default=None,
    help="""
ssh="<username>@<host>".
If you use a non-standard ssh port: "<username>@<host>:<ssh_port>".
If you use password: "<username>@<host>:<ssh_port>,<password>".
""",
)
parser.add_argument("--api_key", type=str, default=None, help="api key")
parser.add_argument("--base_url", type=str, default=None, help="base url")
args = parser.parse_args()
#if args.ssh is None and args.api_key is None:
#    parser.error("At least one of --ssh or --api_key must be provided.")


def interact():
    env = Environment(env_path="auto")
    if True:
        agent = AgentClient(ssh=args.ssh)
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
