# Evaluation

Unlike traditional tasks that compare the model's output with the ground truth on datasets, embodied intelligence requires interaction with the environment and uses the world state to determine if a task has been completed. The platform provides manual interaction for qualitative evaluation, as well as automatic quantitative evaluation.

## Interact with your model

By interacting with the model directly in the environment's chat box, we can intuitively experience the model's performance.
After training the model, deploy it by running:

``` bash
MODEL_PATH=<model_path> python scripts/llava/serve.py
```

On your personal computer, launch the client by running:

``` bash
python scripts/interact_with_model.py --ssh <username>@<host>:<ssh_port>,<password>
```

Here `<username>@<host>:<ssh_port>,<password>` is how you login the remote server through SSH. `:<ssh_port>` and `,<password>` are optional.

Chat with the model in the chatbox and see its actions.

## Interact with GPT4-V

On your personal computer, launch the client by running:

``` bash
python scripts/interact_with_model.py --api_key <api_key> --base_url <base_url>
```

Here `--api_key <api_key> --base_url <base_url>` is how you use the GPT4-V API. `--base_url <base_url>` is optional.

Chat with GPT4-V in the chatbox and see its actions.

## Evaluate your model

To fairly compare models and ensure the reproducibility of experiments, we first generate some task settings and then consistently use these settings for subsequent evaluations.

Generate task settings. Use `--task come` for "Come here" task and `--task where` for "Where is the orange" task. 

```bash
python scripts/create_eval.py --task come --num 10
```

The generated task settings will be saved at  `.legent/eval`.

After training and deploying the model, run the following script on your personal computer:

```bash
python scripts/eval_model.py --task come --ssh <username>@<host>:<ssh_port>,<password>
```

All the informations and results will be saved at `'.legent/eval/.../results/...-model'`

## Evaluate GPT4-V

run the following script on your personal computer:

```bash
python scripts/eval_model.py --task come --api_key <api_key> --base_url <base_url>
```

All the informations and results will be saved at `'.legent/eval/.../results/...-gpt4v'`