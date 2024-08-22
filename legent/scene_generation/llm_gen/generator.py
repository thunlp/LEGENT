from legent import load_json, store_json, Environment, ResetInfo, SaveTopDownView
from legent.scene_generation.llm_gen.doorway import DoorwayGenerator
from legent.scene_generation.llm_gen.floor_plan import FloorPlanGenerator
from legent.scene_generation.llm_gen.floor_object_selection import FloorObjectGenerator
from legent.scene_generation.llm_gen.small_object_selection import SmallObjectGenerator
import os
import numpy as np
from datetime import datetime
import spacy
from legent.environment.env_utils import get_default_env_data_path
from langchain_openai import OpenAI
from legent import load_json, store_json, Environment, ResetInfo, SaveTopDownView, Observation
from legent.scene_generation.llm_gen.llm import llm
from argparse import ArgumentParser


class LLMGenerator:
    def __init__(self, query, asset_dir, save_dir, openai_api_key, scene_name=None, single_room=False):
        self.query = query
        create_time = str(datetime.now()).replace(" ", "-").replace(":", "-").replace(".", "-")
        if not scene_name:
            self.scene_name = ''.join([word[0] for word in query.split()])+"-"+create_time
        else:
            self.scene_name = scene_name

         # initialize llm
        self.llm = OpenAI(model_name="gpt-4-1106-preview", openai_api_key=openai_api_key, max_tokens=2048)
        self.asset_list = load_json(f"{asset_dir}/addressables.json")['prefabs']
        self.object_type_to_names = load_json(f"{asset_dir}/llm_gen/object_type_to_names.json")
        self.available_large_objects = load_json(f"{asset_dir}/llm_gen/available_large_objects.json")
        self.available_small_objects = load_json(f"{asset_dir}/llm_gen/available_small_objects.json")
        # download with `python -m spacy download en_core_web_md` (42.8MB)
        self.nlp = spacy.load("en_core_web_md")

        single_room_requirements = "I only need one room"
        if single_room: 
            self.additional_requirements_room = single_room_requirements
            self.additional_requirements_door = single_room_requirements
        else: 
            self.additional_requirements_room = "N/A"
            self.additional_requirements_door = "N/A"
        self.additional_requirements_floor_object = "N/A"
        self.additional_requirements_small_object = "N/A"

        self.scene_folder = f"{save_dir}/{self.scene_name}"
        os.makedirs(self.scene_folder, exist_ok=True)
        self.scene_path = f"{self.scene_folder}/scene.json"
        
        self.floor_generator = FloorPlanGenerator(self.llm, self.asset_list, self.object_type_to_names)
        self.doorway_generator = DoorwayGenerator(self.llm, self.object_type_to_names, self.asset_list)
        self.floor_object_generator = FloorObjectGenerator(self.llm, self.available_large_objects, self.asset_list, self.nlp)
        self.small_object_generator = SmallObjectGenerator(self.llm, self.available_small_objects, self.asset_list, self.nlp)
        

    def get_predefined_scene(self, regenerate=True):
        if os.path.exists(self.scene_path):scene = load_json(self.scene_path)
        else:scene = {}
        if "query" not in scene:
            scene["query"] = self.query
        scene["scene_name"] = self.scene_name 

        if regenerate:
            scene["rooms"] = []
            scene["instances"] = []
            scene["center"] = []
            scene["walls"] = []
            scene["doors"] = []
            scene["floor_objects"] = []
            scene["small_objects"] = []
        return scene


    def generate_rooms(self, scene, additional_requirements_room):
        # add floor plan
        scene["rooms"], scene["center"] = self.floor_generator.generate_rooms(scene, additional_requirements_room)
        store_json(scene, self.scene_path)
        for room in scene["rooms"]:
            scene["instances"].extend(room["instances"])
        return scene


    def generate_walls_doors_windows(self, scene, additional_requirements_door):
        scene = self.doorway_generator.generate_doors(scene, additional_requirements_door)
        store_json(scene, self.scene_path)
        scene["instances"].extend(scene["walls"])
        scene["instances"].extend(scene["doors"])
        return scene


    def generate_floor_objects(self, scene, additional_requirements_floor_object):
        scene = self.floor_object_generator.generate_objects(scene, additional_requirements_floor_object, plot=False)
        store_json(scene, self.scene_path)
        scene["instances"].extend(scene["floor_objects"])
        return scene


    def generate_small_objects(self, scene, additional_requirements_small_object, replacement=False):
        scene = self.small_object_generator.generate_objects(scene, additional_requirements_small_object, replacement=replacement)
        store_json(scene, self.scene_path)
        scene["instances"].extend(scene["small_objects"])
        return scene
    

    def generate_scene(self, take_photo=True, replacement=False):
        # this is a scene with instances only, need to add player and agent and camera
        scene = self.get_predefined_scene()

        # generate rooms
        scene = self.generate_rooms(scene, self.additional_requirements_room)
        scene = self.generate_walls_doors_windows(scene, self.additional_requirements_door)
        scene = self.generate_floor_objects(scene, self.additional_requirements_floor_object)
        scene = self.generate_small_objects(scene, self.additional_requirements_small_object, replacement=replacement)
    
        scene["instances"] = [instance for instance in scene["instances"] if "prefab" in instance]
        scene = self.complete_scene(scene)

        # save for view
        store_json(scene, f'{self.scene_folder}/{self.scene_name}.json')
        if take_photo:
            env = Environment(env_path="auto", camera_resolution_width=1024, camera_resolution_height=1024, camera_field_of_view=120)

            try:
                photo_path = f'{os.path.abspath(self.scene_folder)}/{self.scene_name}.png'
                print(f"About to save scene {self.scene_name} to {photo_path}")
                obs = env.reset(ResetInfo(scene=load_json(f'{self.scene_folder}/{self.scene_name}.json'), api_calls=[SaveTopDownView(absolute_path=photo_path)]))
                print("Scene saved successfully")
            finally:
                env.close()

        return scene


    def complete_scene(self, predefined_scene):
        # Complete a predefined scene
        # add player, agent, interactable information etc.

        position = [2, 0.1, 2] 
        rotation = [0, np.random.uniform(0, 360), 0]
        player = {
            "prefab": "",
            "position": position,
            "rotation": rotation,
            "scale": [1, 1, 1],
            "parent": -1,
            "type": ""
        }
        
        position = [2.5, 0.1, 2.5]
        rotation = [0, np.random.uniform(0, 360), 0]
        agent = {
            "prefab": "",
            "position": position,
            "rotation": rotation,
            "scale": [1, 1, 1],
            "parent": -1,
            "type": ""
        }


        infos = {
            "prompt": "",
            "instances": predefined_scene["instances"],
            "player": player,
            "agent": agent,
            "center": predefined_scene["center"],
        }
        return infos


def play_with_scene(scene_name):
    """
    Play with the scene
    """
    scene_path = f"{os.getcwd()}/scenes/{scene_name}/{scene_name}.json"
    env = Environment(env_path="auto", camera_resolution_width=1024, camera_resolution_height=1024, camera_field_of_view=120)
    try:
        obs: Observation = env.reset(ResetInfo(scene=load_json(scene_path)))
        while True:
            obs = env.step()
    finally:
        env.close()


if __name__ == "__main__":
    
    parser = ArgumentParser()
    parser.add_argument("--query", help = "Query to generate scene from.", default = "a living room")
    parser.add_argument("--scene_name", help = "Name of the scene to generate.", default = None)
    parser.add_argument("--openai_api_key", help = "OpenAI API key.", default = None)
    parser.add_argument("--asset_dir", help = "Directory to load assets from.", default = f"{get_default_env_data_path()}")
    parser.add_argument("--save_dir", help = "Directory to save scene to.", default = f"{os.getcwd()}/scenes")
    parser.add_argument("--generate_image", help = "Whether to generate an image of the scene.", default = "True")
    parser.add_argument("--single_room", help = "Whether to generate a single room scene.", default = False)
    parser.add_argument("--replacement", help = "Whether to allow replacement of objects.", default = True)
    
    args = parser.parse_args()
    scene_generator = LLMGenerator(args.query, 
                                asset_dir=args.asset_dir,
                                save_dir=args.save_dir,
                                openai_api_key=args.openai_api_key,
                                scene_name=args.scene_name,
                                single_room=args.single_room) # remember to turn on or turn off the single room requirement
    scene = scene_generator.generate_scene(take_photo=args.generate_image, replacement=args.replacement)

