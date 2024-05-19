<div align="center"><img src="misc/LEGENT-logo.webp" alt="LEGENT" width="300" height="300"/></div>
    
<h3 align="center">
    <p>Open Platform for Embodied Agents</p>
</h3>

<h4 align="center">
    <p>
    【
        <!-- <a href="https://github.com/thunlp/LEGENT/blob/main/docs/README.md">Documentation</a> | -->
        <a href="https://docs.legent.ai/">Documentation</a> |
        <a href="https://arxiv.org/pdf/2404.18243">Paper</a> |
        <a href="https://huggingface.co/spaces/LEGENT/LEGENT">Playable Demo</a> |
        <a href="https://docs.legent.ai/blog/introduction">Quick Start</a> | 
        <a href="https://discord.gg/FenHQRyFN7">Discord</a>
    】
    </p>
</h4>

---

### Updates

* [2024/05] A simple [web demo](https://huggingface.co/spaces/LEGENT/LEGENT) is accessible on HuggingFace Space🤗.
Let's dive into the immersive interactive world!

### Introduction

In the future, robots will perceive the environment as we do, communicate with us through natural language and help us with our tasks. The platform is dedicated to developing robots that can chat, see, and act from virtual worlds to the real world.
We aim to facilitate research in this field for anyone interested. LEGENT is a pioneering solution combining large models with embodied agents, prioritizing ease of use and scalability. The platform focuses on developing:

* An easy-to-use environment that simulates a physical world, where an agent can interact with humans through language, receive egocentric vision, and perform physical actions.

* Automated generation of training data, including the generation of scenes, tasks, and agent trajectories. The platform is tailored to train large multimodal models as embodied models, using generated data from simulated worlds at scale. LEGENT serves as the data engine for embodied models in **robotics** and **games**, as well as for world models.

### Demonstration

Interact with the embodied agent in realistic scenes.


<https://github.com/thunlp/LEGENT/assets/50205889/20657124-e2e6-434f-9315-bcbdce26e1f3>


Interact with the embodied agent in stylized scenes.


<https://github.com/thunlp/LEGENT/assets/50205889/e667bf3d-1dc5-4ed7-95b7-b3bf6ab60fdf>



### Features

* **Language Interaction**. Use natural language as the human-robot interaction interface.


* **Fundamental Physics**. The simulation incorporates gravity, friction, and collision dynamics.

* **Diverse Rendering**. By adjusting assets and rendering features, LEGENT can achieve photorealistic rendering and stylized rendering. 
Instructions for trying out these scenes can be found [here](https://docs.legent.ai/documentation/getting_started/play/#default-scenes).

  <https://github.com/thunlp/LEGENT/assets/50205889/bcce2f73-8e8d-420a-85a2-0d7491840e48>



* **Interactable Objects**. Agents and humans can manipulate various 3D objects.

  <https://github.com/thunlp/LEGENT/assets/50205889/b2392a4e-0c26-489a-b608-2c11f45c619f>
  
* **Scalable Assets**. LEGENT supports importing (1) your own 3D objects, (2) objects from academic datasets, and (3) objects created by generative models. Learn more [here](https://docs.legent.ai/documentation/data/object_assets/).

  <https://github.com/thunlp/LEGENT/assets/50205889/d5b35c51-4da3-4392-a87e-262ba70a9713>

  <https://github.com/thunlp/LEGENT/assets/50205889/b90c7ac4-73c6-4dfc-bbd8-9e4cd5051548>

* **Humanoid Animation**. Body movement and nonverbal expression are also important for embodied agents. LEGENT will continue to enhance support in this aspect.


* **Scene Generation**. LEGENT integrates advanced scene generation algorithms to support scalable training.

  <https://github.com/thunlp/LEGENT/assets/50205889/fafaa02e-1050-4dab-a43f-701bca1477b7>

* **Trajectory Generation**. Automatic generation of training data for training multimodal models into language-grounded embodied models. A minimal example of a trajectory:
  
  <img src="https://github.com/thunlp/LEGENT/assets/50205889/14a58d07-a28b-45c5-b5f8-323d0690d9cc" width="160" height="160" alt="0000">
  <img src="https://github.com/thunlp/LEGENT/assets/50205889/137bacc9-c144-4ab3-a3bf-97ac216ebac1" width="160" height="160" alt="0001">
  <img src="https://github.com/thunlp/LEGENT/assets/50205889/c0dd17d1-1b62-431d-8db3-96b9a90e8f60" width="160" height="160" alt="0002">
  <img src="https://github.com/thunlp/LEGENT/assets/50205889/1a2e20e0-6bd7-4ff4-873f-93e2eef551f5" width="160" height="160" alt="0003">

  ```json
  {
    "id": "20240509-223825-320898",
    "interactions": [
        {
            "from": "human",
            "text": "Where is the orange?"
        },
        {
            "from": "agent",
            "trajectory": [
                {
                    "image": "20240509-223825-320898/0000.png",
                    "action": "rotate_right(18)"
                },
                {
                    "image": "20240509-223825-320898/0001.png",
                    "action": "move_forward(2.0)"
                },
                {
                    "image": "20240509-223825-320898/0002.png",
                    "action": "move_forward(1.8), rotate_right(30)"
                },
                {
                    "image": "20240509-223825-320898/0003.png",
                    "action": "speak(\"It's on the sofa.\")"
                }
            ]
        }
    ]
  }
  ```

* **User-friendly**. LEGENT requires no complex installation and can run cross-platform on both PCs and servers. It is as intuitive as a game while also supporting complex research needs.

### Note

LEGENT is currently organizing code and documents and improving existing features. It will be more convenient to use once this process is complete. If you want a more stable version, please stay tuned!
