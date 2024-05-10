from colorama import Fore
from langchain.prompts import PromptTemplate
from legent.scene_generation.llm_gen import prompts
from legent.scene_generation.llm_gen.utils import find_most_similar_word, move_polygons_many_times, get_instance, get_asset_info
import re
import random
from itertools import groupby
import random


class SmallObjectGenerator():
    def __init__(self, llm, available_small_objects, asset_list, nlp):
        self.json_template = {"instances": []} 
        self.small_object_template = PromptTemplate(input_variables=["input", "receptacles", "small_objects", "additional_requirements"], template=prompts.small_object_selection_prompt)
        self.llm = llm
        self.available_small_objects = available_small_objects
        self.asset_list = asset_list
        self.nlp = nlp

    def generate_objects(self, scene, additional_requirements="N/A", replacement=False):
        if "raw_small_object_plan" not in scene:
            receptacles = self.group_dicts_by_room_id(scene["floor_objects"])
            object_categories_and_size = ", ".join([obj_type for obj_type in self.available_small_objects])
            small_object_prompt = self.small_object_template.format(receptacles=receptacles, small_objects=object_categories_and_size, input=scene["query"], additional_requirements=additional_requirements)
            print(f"User: {small_object_prompt}\n")
                
            raw_small_object_plan = self.llm(small_object_prompt)
            scene["raw_small_object_plan"] = raw_small_object_plan
        else:
            raw_small_object_plan = scene["raw_small_object_plan"]
        
        
        print(f"{Fore.GREEN}AI: Here is the small object selection plan:\n{raw_small_object_plan}{Fore.RESET}")
        # parse doorway plan
        scene["small_object_plan"] = self.parse_plan(scene["raw_small_object_plan"]) 
        small_object_placement = self.place_small_objects(scene)
        if replacement:
             scene["small_objects"] = self.replace_small_objects(small_object_placement)
        else:
            scene["small_objects"] = small_object_placement

        return scene


    def group_dicts_by_room_id(self, floor_objects):
        floor_objects = [obj for obj in floor_objects if obj["size"]["y"]<2.5 and obj["size"]["x"]>0.3 and obj["size"]["z"]>0.3]
        # print(f"{Fore.GREEN}{[obj['prefab'] for obj in floor_objects]}{Fore.RESET}")
        floor_objects.sort(key=lambda x: x.get('room_id', None))
        grouped_floor_objects = {key: [i["id"] for i in list(group)] for key, group in groupby(floor_objects, key=lambda x: x.get('room_id', None))}
        return grouped_floor_objects


    def replace_small_objects(self, small_object_placement):
        final_objects = []
        unique_surfaces = {}
        for instance in small_object_placement:
            if str(instance["surface"]) not in unique_surfaces:
                unique_surfaces[str(instance["surface"])] = instance["surface"], instance["receptacle_id"]
        for index, item in unique_surfaces.items():
            surface, receptacle_id = item
            one_surface_multiple_instances = [instance for instance in small_object_placement if instance["surface"]==surface]
            one_surface_multiple_instances = move_polygons_many_times(one_surface_multiple_instances, surface)
            final_objects.extend(one_surface_multiple_instances)


        for instance in final_objects:
            x = [vertex[0] for vertex in instance["bbox"]]
            y = [vertex[1] for vertex in instance["bbox"]]
            center_x = sum(x) / len(x)
            center_y = sum(y) / len(y)
            instance["position"] = [center_x, instance["position"][1], center_y]
        return final_objects



    def parse_plan(self, raw_plan):
        try:
            room_plans = [i for i in re.split(r'\[([^\]]+)\]', raw_plan)[::2] if i]
            room_ids = [i for i in re.split(r'\[([^\]]+)\]', raw_plan)[1::2] if i]
            parsed_plans = []

            for i in range(len(room_plans)):
                objects_strs = [i for i in room_plans[i].split("\n") if i]
                for object_str in objects_strs:
                    receptacle_id = object_str.split(":")[0]
                    room_id = room_ids[i]
                    
                    matches = re.findall(r'\s*\(([^,]+),\s*(\d+)\)\s*', object_str)
                    for match in matches:
                        object_category,quantity = match
                        parsed_plan = {
                            "receptacle_id":receptacle_id,
                            "room_id": room_id,
                            "object_category": object_category.strip(),
                            "quantity": int(quantity.strip()),
                        }
                        parsed_plans.append(parsed_plan)                    
            return parsed_plans
        except:
            print(f"{Fore.RED}Invalid small object plan:{Fore.RESET}", raw_plan)
            return None    
    

    def place_small_objects(self, scene):
        instances = []
        for object in scene["small_object_plan"]:
            original_object_category = object["object_category"]
            object_category = find_most_similar_word(original_object_category, self.available_small_objects, self.nlp)
            if not object_category:
                # print(f"{Fore.RED}No objects found for:{Fore.RESET}", original_object_category)
                continue
            try:
                receptacle_instance = [item for item in scene["floor_objects"] if item["id"]==object["receptacle_id"] and item["room_id"]==object["room_id"]][0]
                receptacle_position, receptacle_rotation, placeable_surfaces = receptacle_instance["position"], receptacle_instance["rotation"], receptacle_instance["placeable_surfaces"]
                
                def random_chance(chance):
                    return random.random() < chance
                if object["quantity"]>2:
                    quantity = 2
                else:
                    quantity = object["quantity"]
                    
                for i in range(quantity):
                    instance_name = random.choice(self.available_small_objects[object_category]["names"])
                    instance_info = get_asset_info(instance_name, self.asset_list)
                    if instance_info:
                        position, rotation, surface, bbox = self.random_spawn(receptacle_position, receptacle_rotation, placeable_surfaces, instance_info["size"])
                        if position and rotation:
                            # position, rotation = self.old_random_spawn(receptacle_instance["size"], receptacle_instance["bbox"], receptacle_rotation, instance_info["size"])
                            scale = [1, 1, 1]
                            if object_category == "Clock":
                                scale = [0.2, 0.2, 1]
                            keep= False
                            movable=True

                            instance = get_instance(instance_name, position, rotation, scale, "interactable", instance_info["size"], surface=surface, object_category=object_category, receptacle_id=receptacle_instance["id"], movable=movable, keep=keep, bbox=bbox, id=i)
                            instances.append(instance)
                        else:
                            # print(f"{Fore.RED}Wrong object:{Fore.RESET}", instance_info)
                            continue
                
            except:
                continue
        return instances


    def random_spawn(self, receptacle_position, receptacle_rotation, placeable_surfaces, object_size):
        placeable_surface = random.choice(placeable_surfaces)
        
        
        rotation = receptacle_rotation
        if rotation[1] == 90:
            if -placeable_surface["z_max"]+object_size["z"] < -placeable_surface["z_min"]:
                x = random.uniform(-placeable_surface["z_max"]+object_size["z"]/2, -placeable_surface["z_min"]-object_size["z"]/2)
                z = random.uniform(-placeable_surface["x_max"]+object_size["x"]/2, -placeable_surface["x_min"]-object_size["x"]/2)
                surface = [[receptacle_position[0]-placeable_surface["z_max"], receptacle_position[2]-placeable_surface["x_max"]],
                           [receptacle_position[0]-placeable_surface["z_max"], receptacle_position[2]-placeable_surface["x_min"]],
                           [receptacle_position[0]-placeable_surface["z_min"], receptacle_position[2]-placeable_surface["x_min"]],
                           [receptacle_position[0]-placeable_surface["z_min"], receptacle_position[2]-placeable_surface["x_max"]]]
                bbox_x_min, bbox_x_max, bbox_z_min, bbox_z_max = -object_size["z"], object_size["z"], -object_size["x"], object_size["x"]
        elif rotation[1] == -90:
            if placeable_surface["z_min"]+object_size["z"] < placeable_surface["z_max"]:
                x = random.uniform(placeable_surface["z_min"]+object_size["z"]/2, placeable_surface["z_max"]-object_size["z"]/2)
                z = random.uniform(placeable_surface["x_min"]+object_size["x"]/2, placeable_surface["x_max"]-object_size["x"]/2)
                surface = [[receptacle_position[0]+placeable_surface["z_min"], receptacle_position[2]+placeable_surface["x_min"]],
                           [receptacle_position[0]+placeable_surface["z_min"], receptacle_position[2]+placeable_surface["x_max"]],
                           [receptacle_position[0]+placeable_surface["z_max"], receptacle_position[2]+placeable_surface["x_max"]],
                           [receptacle_position[0]+placeable_surface["z_max"], receptacle_position[2]+placeable_surface["x_min"]]]
                bbox_x_min, bbox_x_max, bbox_z_min, bbox_z_max = -object_size["z"], object_size["z"], -object_size["x"], object_size["x"]
        elif rotation[1] == 0:
            if placeable_surface["x_min"]+object_size["x"] < placeable_surface["x_max"]:
                x = random.uniform(placeable_surface["x_min"]+object_size["x"]/2, placeable_surface["x_max"]-object_size["x"]/2)
                z = random.uniform(placeable_surface["z_min"]+object_size["z"]/2, placeable_surface["z_max"]-object_size["z"]/2)
                surface = [[receptacle_position[0]+placeable_surface["x_min"], receptacle_position[2]+placeable_surface["z_min"]],
                           [receptacle_position[0]+placeable_surface["x_min"], receptacle_position[2]+placeable_surface["z_max"]],
                           [receptacle_position[0]+placeable_surface["x_max"], receptacle_position[2]+placeable_surface["z_max"]],
                           [receptacle_position[0]+placeable_surface["x_max"], receptacle_position[2]+placeable_surface["z_min"]]]
                bbox_x_min, bbox_x_max, bbox_z_min, bbox_z_max = -object_size["x"], object_size["x"], -object_size["z"], object_size["z"]
        else:
            if -placeable_surface["x_max"]+object_size["x"] < -placeable_surface["x_min"]:
                x = random.uniform(-placeable_surface["x_max"]+object_size["x"]/2, -placeable_surface["x_min"]-object_size["x"]/2)
                z = random.uniform(-placeable_surface["z_max"]+object_size["z"]/2, -placeable_surface["z_min"]-object_size["z"]/2)
                surface = [[receptacle_position[0]-placeable_surface["x_max"], receptacle_position[2]-placeable_surface["z_max"]],
                           [receptacle_position[0]-placeable_surface["x_max"], receptacle_position[2]-placeable_surface["z_min"]],
                           [receptacle_position[0]-placeable_surface["x_min"], receptacle_position[2]-placeable_surface["z_min"]],
                           [receptacle_position[0]-placeable_surface["x_min"], receptacle_position[2]-placeable_surface["z_max"]]]
                bbox_x_min, bbox_x_max, bbox_z_min, bbox_z_max = -object_size["x"], object_size["x"], -object_size["z"], object_size["z"]
        if x and z:
            

            position = x  + receptacle_position[0], object_size["y"]/2 + receptacle_position[1] + placeable_surface["y"], z + receptacle_position[2]

            bbox = [[position[0]+bbox_x_min, position[2]+bbox_z_min],
                    [position[0]+bbox_x_min, position[2]+bbox_z_max],
                    [position[0]+bbox_x_max, position[2]+bbox_z_max],
                    [position[0]+bbox_x_max, position[2]+bbox_z_min]]
            return position, rotation, surface, bbox
        else:
            return None, None