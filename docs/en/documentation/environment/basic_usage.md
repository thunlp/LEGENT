# Basic Usage

Start an environment with the following code. This code will launch the environment, establish a connection between python and the environment, and keep the environment running.

``` python
from legent import Environment
path_to_executable = "<Your path to the environment client>" # ".legent/env/client/LEGENT-<platform>-<version>" for example
env = Environment(env_path=path_to_executable) # or env_path="auto" to start the latest client in .legent/env/client.
try:
    env.reset()
    while True:
        env.step()
finally:
    env.close()
```

??? "Launch the environment manuually"

    It is equal to run the following code and start the executable file in `.legent/env/client` mannually.
    
    ``` python
    from legent import Environment
    env = Environment(env_path=None)
    try:
        env.reset()
        while True:
            env.step()
    finally:
        env.close()
    ```

## Run a standard action-observation loop

Once the environment is initialized, it can receive an action and return the observation after the action is completed. In this example, we initialize a random scene by calling `env.reset()` and keep the robot moving forward.

``` python
from legent import Environment, Action

env = Environment(env_path="auto")
try:
    obs = env.reset()
    while True:
        action = Action(move_forward=1) # keep moving forward
        obs = env.step(action)
finally:
    env.close()
```

All the actions can be found [here](/documentation/environment/action).

## Get the Observations

In the following example, when the user sends a chat message (pressing the `Enter` key to open the chat box), we can obtain the user's input from `obs.text`, and then make a reply.

```python
from legent import Environment, Action, Observation

env = Environment(env_path="auto")
try:
    obs: Observation = env.reset()
    while True:
        action = Action()
        if obs.text != "":
            action.text = "I don't understand."
        obs = env.step(action)
finally:
    env.close()
```

When the program is running, you send a message in the chat box, and the agent is supposed to reply to you.


You can also save what the agent sees using the following code.

``` python
from legent import save_image
save_image(obs.image, "agent_view.png")
```

All the observations can be found [here](/documentation/environment/observation).


## Remote communication through ssh

Install platform toolkit on the remote server as well.

On the remote server, run:

``` python
from legent import Environment, Action

env = Environment(env_path=None)
try:
    # Do anything here.
    # For example, we send a message to the client
    env.reset()
    env.step(Action(text = "I'm on the remote server."))
    while True:
        env.step()
finally:
    env.close()
```

On your personal computer, run:

``` shell
legent launch --ssh <username>@<host>:<ssh_port>
```

## Test the speed

The environment is expected to run at 60 steps per second. This number may vary due to different machine performance. Below is the code to test the speed of the environment on your machine.

``` python
from legent import Environment
from tqdm import tqdm
from time import time
env = Environment(env_path="auto")
try:
    obs = env.reset()
    steps = 1000
    start = time()
    for i in tqdm(range(steps)):
        obs = env.step()
    print(f'{steps/(time()-start):.2f} step/s')
finally:
    env.close()
```