# Introducing LEGENT (Alpha Version)

Date: 2024-05-09

Welcome to the introduction of LEGENT, our latest venture into scalable embodied AI. LEGENT is a 3D interactive environment suitable for researchers and anyone interested to explore embodied AI in the simulated world. 

## I. What is Embodied AI and What's our Approaches

Embodied AI refers to artificial intelligence systems that interact with their environment in a way that mimics human engagement. These systems are not just virtual; they perceive, understand, and act within their surroundings, offering a richer, more integrated form of AI.

LEGENT provides:

1. Content-rich simulated worlds that offer diverse embodied experiences.

2. An intuitive interface for human-robot and human-environment interaction via keyboard and mouse, as well as language interaction through APIs of large language models or multimodal models.

3. Scalable data generation (**scene**-task-trajectory) for training embodied agents.

This blog aims to guide you through the initial setup and exploration of LEGENT (without requiring you to write any code), covering only a small portion of its features. The advanced functionalities are detailed in the [documentation](/documentation/environment/basic_usage/) and [paper](https://arxiv.org/pdf/2404.18243).

## II. Getting Started with LEGENT

To launch LEGENT, follow the steps outlined in our [Installation Guide](/documentation/getting_started/installation). This process will set up a default scene to get you started quickly.

### a. Exploring the Default Scene

Type ```legent launch --scene 0``` in the terminal is enough for launching the default scene. A window will pop up which displays the scene inside a two-story villa.

You can use ```W```, ```A```, ```S```, ```D``` to walk around the house, and use the mouse to adjust the perspective. You can click on the small objects around you to pick them up. If the object is out of reach, this will not take effect. You can put the object in your hand into a designated place by clicking on the place. Use ```I```, ```K``` , ```J```, ```L``` , ```U```, ```O``` to adjust the pose the held object. You can also click on doors and drawers to open or close them.

There is a robot agent in the room. In the default settings, it is not intelligent and can only perform actions based on rules. For example, you can press ```Enter``` to open the chatbox, and send ```goto_user()``` to let the robot come to you.

You can press `V` to change the perspective of the user/robot/god. (You can try switching to the robot view and then type ```goto_user()``` :)

The first-person/third-person views can be switched using `C`. The third-person view is currently only supported for the user perspective.


### b. Randomizing and Saving Scenes

LEGENT's environment is highly customizable and allows for the large-scale random generation of scenes. 

To switch to a randomly generated scene:

1. Terminate the original scene and relaunch using `legent launch`.

2. Press the `Enter` key to open the chatbox where you can type `#RESET` to initiate another new scene.

If the generated scene meets your expectations, send ```#SAVE``` in the chatbox.
The scene will be saved as a JSON file in the `.legent/saved_scenes` folder.

For initiating a specific scene, use `legent launch --scene <scene-file-path or built-in-scene-id>`. All the built-in scenes are listed [here](https://github.com/thunlp/LEGENT/blob/main/scene_index.jsonl).

## III. Interaction with Your Language Commands
Press ```Enter``` to open the chatbox, where you can execute various commands.

### a. Built-in Functions
Some built-in function are provided to control the robot.

- `move_forward(distance)`. `move_forward(1.5)` will make the agent move forward 1.5 meters.
- `rotate_right(angle)`. `rotate_right(-45)` will make the agent rotate to the left 45 degrees.
- `goto_user()`. Let the agent come to you.
- `goto(id)` where `id` the object ID. E.g., `goto(3)` will make the agent move forward 3 meters. (Press T to open the log panel, where you can see the ID of the object you are pointing)
- `grab()`. Let the agent grab the object.
- `release()`. Let the agent release the object.

### b. Text-API Integration

To enable the agent to respond to complex natural language commands, you can use your ChatGPT API key by runing `legent launch --scene 0 --api_key <your_api_key>`.
Then, open the chatbox and send any text to the agent. See what happens.

### c. Advancing with Multimodal API

The text agent seems to perform well, but the downside is that it cannot function in unannotated environments where internal world states are inaccessible (such as other environments or the real world). Our goal is to achieve generalization across different environments and bridge the gap between virtual and real environments using embodied multimodal models. Although not powerful yet, the development is ongoing, and we expect to leverage large-scale data from LEGENT for training the models. Stay tuned!

