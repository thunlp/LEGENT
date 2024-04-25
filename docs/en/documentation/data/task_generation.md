# Task Generation

To make embodied agents more generalizable, it's important to have a wide variety of training data, so generating different tasks automatically is very useful.
For embodied agents, the two essential elements of a task are the world state and the task description. A task expressed in a certain world state gives it a grounded meaning. If it is to be used for evaluation, the task also requires a method for determining task completion. If used for training, the task requires a solution.
The outputs of task generation for training are (scene, task, solution) triplets.

To create a task, there are two approaches: first, generate a scene, and then generate a task with the scene as a condition; or first, generate a task, and then generate a scene with the task as a condition. This ensures that the task is meaningful within the context of the scene.


Currently only several task types have been implemented :

* Come here (`come`)

* Go to something / Stand next to something (`goto`)

* Pick up something (`take`)

* Bring me something (`bring`)

* Put something on something (`put`)

* Where is something (`where`)

* Is there something on something (`exist`)

This can be considered a VLA (Vision-Language-Action) version of "[T5](https://arxiv.org/abs/1910.10683)", integrating several tasks for joint training. The platform is developing a broader range of automatic task generation to transform "T5" into "[FLAN-T5](https://arxiv.org/abs/2210.11416)" and to bring it a step closer to an embodied "ChatGPT".


## Generate a task conditioned on a scene

The advantage of this approach is that a single scene can often accommodate many tasks. For high quality scenes, Large language models can generate a list of tasks conditioned on the scene, making full use of the information within it. Large language models are goot at generating brief task texts but are not good at producing long and precisely formatted scene files. Moreover, this approach does not impose any requirements on the scene generation algorithm.

We are developing three methods for creating a task: hardcoding, prompting and chatting.

* Hardcoding refers to creating specific tasks by randomly selecting objects involved and formulate the tasks by template strings. For example, when generating a `goto` task, an object such as an apple is selected, leading to the task being formulated as "Go to the apple".

* Prompting refers to creating single-turn tasks by providing a scene and task type, along with some examples of generating tasks to large language models. Large language models generate instruction following or question answering tasks conditioned on a scene. If the large language model has a sufficient understanding of physical space, the prompting method should be able to create a wide variety of tasks, not limited to several task types mentioned above.

* Chatting involves large language models playing both the role of the user and the role of the annotator. The large language models have complete access to the environmental state. The user, based on the environmental state, poses questions to the annotator, who then annotates the solution and executes it within the environment. This process can be iteratively performed to obtain task data in various forms. (Not implemented)

Here is a example on how to generate tasks conditioned scenes.

``` python
from legent import TaskCreator

creator = TaskCreator()
creator.create_tasks(task_types=['come', 'goto'], method="hardcoding", scene_num=10)
```

This code will generate 10 training samples for each of the `come` and `goto` tasks, and save the samples in the `.legent/tasks/hardcoding` folder.

For prompting, try:

``` python
from legent import TaskCreator

api_key = <Your ChatGPT API key>
base_url = <Base URL> # None means the official url
creator = TaskCreator(api_key=api_key, base_url=base_url)
creator.create_tasks(task_types=['goto'], method="prompting", scene_num=1)
```

You will see an output similar to the following including the designed prompt and ChatGPT's response. The samples will be saved in the `.legent/tasks/prompting` folder.

```
Send to ChatGPT:
You are in a room with the following objects(in table format):
object_id       name    position_x      position_y(vertical distance from ground)       position_z
0       Floor   -2.50   0.00    -2.50
1       WallFloor1      -3.75   1.25    -2.50
2       WallFloor1      -2.50   1.25    -3.75
3       Floor   -2.50   0.00    0.00
4       WallFloor1      -3.75   1.25    0.00
5       Floor   -2.50   0.00    2.50
6       WallFloor1      -3.75   1.25    2.50
7       WallFloor1      -2.50   1.25    3.75
8       Floor   0.00    0.00    -2.50
9       WallFloor1      1.25    1.25    -2.50
10      WallFloor1      0.00    1.25    -3.75
11      Floor   0.00    0.00    0.00
12      WallFloor1      1.25    1.25    0.00
13      Floor   0.00    0.00    2.50
14      WallFloor1      1.25    1.25    2.50
15      WallFloor1      0.00    1.25    3.75
16      Library -1.57   1.09    1.19
17      KitchenChair    -1.40   0.57    -2.72
18      Library -2.96   1.09    -1.20
19      Library 0.13    1.09    -2.02
20      Pot     -2.20   0.15    -0.21
21      Orange  -0.47   0.15    2.81
22      Plate   -2.86   0.11    -0.36
23      Plate   -0.50   0.11    0.19
24      Potato  0.02    0.14    1.18
25      Sandwich        -2.44   0.09    0.19
26      Sandwich        -3.30   0.09    -0.46
27      Cup     -2.11   0.13    0.67
28      Bacon   -2.31   0.06    -3.53
29      Garlic  -2.57   0.15    3.47
30      Cupcake -2.28   0.12    0.33
31      Cup     -3.35   0.13    0.39
You need to Ask the robot to go to something.
You need to propose 1 independent tasks and corresponding solutions, in the format of "Task: task; Plan: plan; Solution: solution.", with no line breaks between the three (use ';' to seperate). One sentence in Plan should match one function call in Solution.
For example (The examples are from other scenes. The number means object_id):
Task: Stand next to the table.; Plan: Go to the table.; Solution: goto(32)
Task: Can you move to the Christmas tree? I want to take a picture for you.; Plan: Go to the Christmas tree.; Solution: goto(44)
Task: Go to the Mushroom.; Plan: Go to the Mushroom.; Solution: goto(67)

Received from ChatGPT:
Task: Can you move to the KitchenChair?; Plan: Go to the KitchenChair.; Solution: goto(17)
```

## Generate a scene conditioned on a task

This approach requires a conditional scene generation algorithm. The advantage of this approach is that it can easily generate a large number of samples for a specific task, as long as the scene generation algorithm can meet the conditions of these specific tasks.

For instance, if you want to train the model specifically for the task "Go to a pumpkin," to equip the model with this particular ability across various scenes, you can use the following code to construct the task and scenes.

``` python
from legent import generate_scene

tasks = []
for i in range(100):
    task = {
        "task": "Go to the Pumpkin.",
        "plan": ["Go to the Pumpkin."]
    }
    scene = generate_scene({"LowPolyInterior_Pumpkin": 1}) # Ensure that the generated scene contains a pumpkin.
    object_id = {instance['prefab']: i for i, instance in enumerate(scene['instances'])}['LowPolyInterior_Pumpkin']
    task['solution'] = [f"goto({object_id})"]
    task['scene'] = scene
    
    tasks.append(task)
```