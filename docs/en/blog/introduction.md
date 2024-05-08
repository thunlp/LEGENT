# Introducing LEGENT (Alpha Version)

Date: 2024-05-08

Welcome to the introduction of LEGENT, our latest venture into scalable embodied AI. LEGENT is a 3D interactive environment that is suitable for researchers to explore embodied AI in the simulated world. 

## I. What is Embodied AI and What's our Approaches

Embodied AI refers to artificial intelligence systems that interact with their environment in a way that mimics human engagement. These systems are not just virtual; they perceive, understand, and act within their surroundings, offering a richer, more integrated form of AI.

LEGENT provides:

1. Content-rich simulated worlds that create diverse embodied experiences.

2. An intuitive interface for human-robot and human-environment interaction via keyboard and mouse, as well as language interaction through APIs of large language models or multimodal models.

3. Scalable data generation (**scene**-task-trajectory) for training embodied agents.


This blog aims to guide you through the initial setup and exploration of LEGENT, covering only a small portion of its features. The advanced functionalities are detailed in the [documentation](/documentation/getting_started/introduction/) and [paper](https://arxiv.org/pdf/2404.18243).

## II. Getting Started with LEGENT

To launch LEGENT, follow the steps outlined in our [Installation Guide](/documentation/getting_started/installation). This process will set up a default scene to get you started quickly.

### a. Exploring the Default Scene

Type ```legend launch --scene 0``` is enough for the default scene. A small window will pop up which displays the scene inside a two-story villa. All the human-made scenes are listed [here](https://github.com/thunlp/LEGENT/blob/main/scene_index.jsonl). 

You can use ```W```, ```A```, ```S```, ```D``` to walk around the house, and use the mouse to adjust the perspective. You can click on the small objects around you to pick them up. If the object is out of reach, this will not take effect. You can put the object in your hand into a designated place by clicking on the place. Use ```Space``` to jump.

There is a robot in the room. For the default functionality, it is not intelligent and can only perform actions based on rules. For example, you can press ```enter``` to enter the command mode, and type ```goto_user()``` to let the robot come to you.

You can press `V` to adopt the perspective of the user/robot/god. (You can try switching to the robot view and then type ```goto_user()``` :)

The first-person/third-person views can be switched using `C`. The third-person view is currently only supported for the user perspective.


### b. Randomize an Scene and Saving Scene

LEGENT's environment is highly customizable and allows for the large-scale random generation of scenes. 

To switch to a randomly generated scene:

1. Terminate the original scene and relaunch using `legent launch`.

2. Press the `Enter` key to open the chatbox where you can type `#RESET` to initiate another new scene.

If the generated scene meets your expectations, send ```#SAVE``` in the chatbox.
The scene will be saved as a JSON file in the specified project folder.

For initiating a specific scene, use `legent launch --scene <scene_file_path>`.

## III. Interaction with Your Language Commands
Press Enter to open the chatbox, where you can execute various commands.

### a. System Functions
You can perform a system reset by entering `#RESET` in the interface.
Some basic function are provided.

- `goto_user()`
- `goto(id)` where `id` is a number that corresponds to a objects' index. E.g., `goto(3)`.çç

### b. Text-API Integration

To enable the agent to respond to complex natural language commands, you can submit your ChatGPT API key here (To Edit). Then, input your command in natural language within the chatbox.

### c. Advancing with Multimodal API
Our goal is to bridge the gap between simulated and real environments using multimodal API. Although not yet perfected, the development is ongoing, and we expect to leverage large-scale data from LEGENT for training our model. Stay tuned!

