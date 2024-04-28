# Introducing LEGENT (Alpha Version)

Date: 2024-04-24

Welcome to the introductory blog for LEGENT, our latest venture into the world of scalable embodied AI. This blog aims to guide you through the initial setup and exploration of LEGENT, paving the way for exciting developments in AI interaction within 3D environments.

## I. What is Embodied AI and What's our Approaches

Embodied AI refers to artificial intelligence systems that interact with their environment in a way that mimics human engagement. These systems are not just virtual; they perceive, understand, and act within their surroundings, offering a richer, more integrated form of AI.


## II. Getting Started with LEGENT

To launch LEGENT, follow the steps outlined in our [Installation Guide](../../../documentation/getting_started/installation). This process will set up a default scene to get you started quickly.

### a. Exploring the Default Scene

Upon launching, LEGENT will present a default scene where you can begin experimenting with its features.


### b. Randomize an Scene and Saving Scene

LEGENT's environment is highly customizable and allows for the large-scale random generation of scenes. 

To switch to a randomly generated scene, you have two options:
1. Terminate the original scene and relaunch using `legent launch`.
2. Press the `Enter` key to open an interface where you can type `#RESET` to initiate a new scene.

For a specific scene setup, use the following command:
```bash
legent launch --scene_path <path_to_the_scene.json>
```

If the generated scene meets your expectations, type #SAVESCENE or #SAVESCENE("name") in the interface.
The scene will be saved as a JSON file in the specified project folder.




## III. Interacting as a Traditional Game Player
Now, dive into a 3D interactive world! Navigate the space, manipulate objects, and explore as you would in a physical environment.

### a. Basic Navigation
Control your movement using W, A, S, D keys. Use Space to jump, C to change your view, and V to switch control bodies.

## IV. Interaction with Your Language Commands
Press Enter to access the language interaction interface, where you can execute various commands.

### a. System Functions
You can perform a system reset by entering #RESET in the interface.

### b. Text-API Integration
To integrate complex commands via a ChatGPT-like function, submit your API key here. Then, input your command in natural language within the interface.

### c. Advancing with 3D Vision API
Our goal is to bridge the gap between simulated and real environments using 3D vision API. Although not yet perfected, the development is ongoing, and we expect to leverage large-scale data from LEGENT for training our model. Stay tuned!

