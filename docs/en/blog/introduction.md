# Introducing LEGENT (Alpha Version)

Date: 2024-04-24

Welcome to the introduction of LEGENT, our latest venture into scalable embodied AI. LEGENT is a 3D interactive virtual environment that are suitable for researchers to explore embodied AI in the virtual world. 

LEGENT can provide 

- (1) embodied trajectories demonstration via key-board and mouse

- (2) language interaction with agents and environemtn through the API of large multimodal models. 

- (3) scaling scene generation for training embodied agents.

This blog aims to guide you through the initial setup and exploration of LEGENT. The advanced functionalities are detailed in [blogs](http://127.0.0.1:8888/documentation/getting_started/introduction/) and [paper](https://arxiv.org/pdf/2404.18243).



## I. Getting Started with LEGENT

To launch LEGENT, follow the steps outlined in our [Installation Guide](../../../documentation/getting_started/installation). This process will set up a default scene to get you started quickly.

### a. Exploring the Default Scene

Type ```legend launch --scene 0``` is enough for the default scene. A small window will pop up which displays the scene inside a two-story villa. The all human-made scenes are listed in ```scene_index.jsonl```. 

You can use ```W```, ```A```, ```S```, ```D``` to walk around the house, and use the mouse to adjust the viewing angle. You can click on the small objects around you to pick them up. If the object is out of reach, this will not take effect. You can put the object in your hand into a designated place by clicking on the place. Use ```Space``` to jump.

There is a robot in the room. For the default functionality, it is not intelligent and can only form actions based on rules. For example, you can press ```enter``` to enter the command mode, and type ```goto_user()``` to let the robot come to you.

You can press `V` to adopt the perspective of the user/robot/god. (You can try switching to the robot view and then type ```goto_user()``` :)

The first-person/third-person views can be switched using `C`. The third-person view is currently only supported for the user perspective.


### b. Randomize an Scene and Saving Scene

LEGENT's environment is highly customizable and allows for the large-scale random generation of scenes. 

To switch to a randomly generated scene, you have two options:

1. Terminate the original scene and relaunch using `legent launch`.

2. Press the `Enter` key to open an interface where you can type `#RESET` to initiate a new scene.

For a specific scene setup, use the following command:
```bash
legent launch --scene <scene_id>
```

If the generated scene meets your expectations, type ```#SAVESCENE``` or ```#SAVESCENE("name")``` in the interface.
The scene will be saved as a JSON file in the specified project folder.


## IV. Interaction with Your Language Commands
Press Enter to access the language interaction interface, where you can execute various commands.

### a. System Functions
You can perform a system reset by entering #RESET in the interface.
Some basic `goto` function are provided.

- `goto_user()`
- `goto(id)` where `id` is a number that corresponds to a objects' index. E.g., `goto(3)`.çç

### b. Text-API Integration
To integrate complex commands via a ChatGPT-like function, submit your API key here. Then, input your command in natural language within the interface.

### c. Advancing with 3D Vision API
Our goal is to bridge the gap between simulated and real environments using 3D vision API. Although not yet perfected, the development is ongoing, and we expect to leverage large-scale data from LEGENT for training our model. Stay tuned!

