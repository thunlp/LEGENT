# Single-Image VLA


Here, the training and deployment example can only handle single-image input, taking [LLaVA](https://github.com/haotian-liu/LLaVA) as an example base model. To quickly illustrate the process, the training and deployment example only uses the task of "come here". However, to enable the model to have a general capability, it should be trained on a variety of tasks.

!!! warning "Note"
    Embodied models should have the capability to input multiple sequential images or videos to get a good understanding of the environment. If we use a single-image model, it means that the agent cannot perceive and memorize the observation history well. Without the observation history, the agent will encounter many problems, such as getting easily stuck. The problems are not very significant for tasks where the camera does not move a lot, such as robotic arm operations, but it has a major impact on tasks that involve navigation.


## Training

Install dependencies:

``` bash
pip install -e ".[llava]"
pip install flash-attn --no-build-isolation
```

Generate the training data we need.

??? abstract "Data Generation"
    You can put the training data on the server using one of the following three methods:

    1. Generate trajectory on your personal computer and upload to the remote server manually.
   
    2. Generate trajectory on the remote server using Xvfb.
    
    3. Using ssh.
    
        On the remote server, run:

        ``` bash
        python scripts/create_traj_come.py
        ```

        On your personal computer, run:

        ```
        legent launch --ssh <username>@<host>:<ssh_port>,<password>
        ```

        The dataset will be saved at `.legent/dataset` on the remote server.
    
Prepare the training data to LLaVA format.

``` bash
python scripts/llava/prepare_dataset.py
```

Download the model.

``` bash
python scripts/llava/download_model.py
```

The model will be downloaded to `.legent/models/base/llava-v1.5-7b`.

Train the model by running:

``` bash
bash scripts/llava/train.sh
```

The save path will be printed.

## Deployment

On the remote server, deploy the model by running:

``` bash
MODEL_PATH=<model_path> python scripts/llava/serve.py
```

On your personal computer, launch the client by running:

``` python
from legent import Environment, AgentClient

env = Environment(env_path="auto")
agent = AgentClient(ssh="<username>@<host>:<ssh_port>")
obs = env.reset()
try:
    while True:
        action = agent.act(obs)
        obs = env.step(action)
finally:
    env.close()
    agent.close()
```

In the chatbox, input "Come here" and see what happens.
