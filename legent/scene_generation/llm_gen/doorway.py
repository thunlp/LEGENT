from colorama import Fore
from langchain.prompts import PromptTemplate
from legent.scene_generation.llm_gen import prompts
from legent import store_json
from legent.scene_generation.llm_gen.utils import midpoint, get_instance, get_wall_length, get_asset_info
import re
import random


class DoorwayGenerator():
    def __init__(self, llm, object_type_to_names, asset_list):
        self.doorway_template = PromptTemplate(input_variables=["input", "common_walls", "additional_requirements"], template=prompts.doorway_prompt)
        self.llm = llm
        self.object_type_to_names = object_type_to_names
        self.asset_list = asset_list
                

    def generate_doors(self, scene, additional_requirements="N/A"):
        scene = self.parse_adjacent_walls(scene)
        walls_to_place_doors = self.get_walls_to_place_doors(scene)

        doorway_prompt = self.doorway_template.format(input=scene["query"], common_walls=walls_to_place_doors, additional_requirements=additional_requirements)
        print(f"User: {doorway_prompt}\n")
        # get doorway plan if not provided
        if "door_plans" not in scene:
            raw_doorway_plan = self.llm(doorway_prompt)
            scene["raw_doorway_plan"] = raw_doorway_plan
            scene["door_plans"] = self.parse_door_plan(raw_doorway_plan, walls_to_place_doors) 
        else:
            raw_doorway_plan = scene["raw_doorway_plan"]
        # parse doorway plan
        print(f"{Fore.GREEN}AI: Here is the door plan:\n{raw_doorway_plan}{Fore.RESET}")
       
        # place the door and wall_door first, which do no need scaling
        scene["doors"] = self.place_door_for_each_wall(scene)
        #place all walls and subwalls
        instances = self.place_wall_for_each_room(scene)
        scene["walls"] = instances
    
        return scene
    

    def get_walls_to_place_doors(self, scene):
        common_walls = "\n".join(
            [
                f"{wall['room_1']} | {wall['room_2']} | {wall['vertices'][0]}, {wall['vertices'][1]}"
                for wall in scene["common_walls"] if get_wall_length(wall["vertices"]) > 1
            ]
        )

        for room in scene["rooms"]:
            for whole_wall in room["whole_walls"]:
                if get_wall_length(whole_wall["vertices_points"]) > 1:
                    common_walls += f"\nexterior | {room['id']} | {whole_wall['vertices_points'][0]}, {whole_wall['vertices_points'][1]}"

        return common_walls
    

    def get_wall_position_and_scale(self, vertices, size, scale_z, pos_scale):
        x, z = midpoint(vertices[0], vertices[1])
        position = [x+size['z']/2*pos_scale[0], size['y']/2+0.1, z+size['z']/2*pos_scale[1]]

        scale_x = max(abs(vertices[0][1]- vertices[1][1]), abs(vertices[0][0]- vertices[1][0]))
        scale = [scale_x / size['x'], 1, scale_z]
        return position, scale


    def place_wall_for_each_room(self, scene):
        instances = []
        for j in range(len(scene["rooms"])):
            wall_material_name = random.choice(self.object_type_to_names["one_type_one_wall"])[:-1]+"1"
            wall_material_name = wall_material_name[:-1]+"1"
            
            size = get_asset_info(wall_material_name, self.asset_list)["size"]
            scene["rooms"][j]["all_walls"] = scene["rooms"][j]["subwalls"] + scene["rooms"][j]["whole_walls"] 

            for i in range(len(scene["rooms"][j]["all_walls"])):
                place_wall = True
                # place all_walls
                subwall_vertices = []
                rotation = scene["rooms"][j]["all_walls"][i]["rotation"]
                scale_z = scene["rooms"][j]["all_walls"][i]["scale_z"]
                pos_scale = scene["rooms"][j]["all_walls"][i]["pos_scale"]
                
                for k in range(len(scene["doors"])):
                    if "prefab" in scene["doors"][k]:
                        continue

                    door_wall_vertices = scene["doors"][k]["door_wall_vertices"]
                    
                    if door_wall_vertices:
                        if self.is_line_in_longer_line(door_wall_vertices, scene["rooms"][j]["all_walls"][i]["vertices_points"]):
                            if scene["doors"][k]["door_type"] == "open":
                                place_wall = False
                            else:
                                subwall_vertices = self.get_subwall_vertice(door_wall_vertices, scene["doors"][k]["door_center"], scene["doors"][k]["door_wall_size"]['x'])
                if place_wall:
                    if subwall_vertices:
                        for p in range(3):
                            if p == 1:
                                wall_material_name = wall_material_name[:-1]+"2"
                                size = get_asset_info(wall_material_name, self.asset_list)["size"]


                            vertices_points = subwall_vertices[p]
                            position, scale = self.get_wall_position_and_scale(vertices_points, size, scale_z, pos_scale)
                            if p == 1:
                                scale = [1, 1, scale_z]
                            instance = get_instance(wall_material_name, position, rotation, scale, "kinematic", size, wall_id=f"{scene['rooms'][j]['id']}-{i}-{p}")
                            instances.append(instance)
                            wall_material_name = wall_material_name[:-1]+"1"
                    else:
                        position, scale = self.get_wall_position_and_scale(scene["rooms"][j]["all_walls"][i]["vertices_points"], size, scale_z, pos_scale)
                        instance = get_instance(wall_material_name, position, rotation, scale, "kinematic", size, wall_id=f"{scene['rooms'][j]['id']}-{i}")
                        instances.append(instance)

        return instances



    def get_subwall_vertice(self, door_wall_vertices, door_center, door_size):
        door_wall_vertices = sorted(door_wall_vertices)
        is_vertical_wall = door_wall_vertices[0][0] == door_wall_vertices[1][0]
        door_wall_vertices.sort(key=lambda v: v[not is_vertical_wall])
        door_start, door_end = door_center[is_vertical_wall] - door_size / 2, door_center[is_vertical_wall] + door_size / 2

        return [
            [(door_wall_vertices[0][0], door_wall_vertices[0][1]), (door_wall_vertices[0][0], door_start)],
            [(door_wall_vertices[0][0], door_start), (door_wall_vertices[0][0], door_end)],
            [(door_wall_vertices[0][0], door_end), (door_wall_vertices[1][0], door_wall_vertices[1][1])]
        ] if is_vertical_wall else [
            [(door_wall_vertices[0][0], door_wall_vertices[0][1]), (door_start, door_wall_vertices[0][1])],
            [(door_start, door_wall_vertices[0][1]), (door_end, door_wall_vertices[0][1])],
            [(door_end, door_wall_vertices[0][1]), (door_wall_vertices[1][0], door_wall_vertices[1][1])]
        ]


    def parse_door_plan(self, raw_plan,common_walls):
        try:
            door_plans = []
            
            plans = [plan.lower() for plan in raw_plan.split("\n") if "|" in plan]
            for plan in plans:
                room_1, room_2, door_wall_vertices, door_type = plan.split("|")
                
                if door_wall_vertices.strip() in common_walls:
                    door_wall_vertices = self.extract_vertices(door_wall_vertices.strip())
                    wall_length = get_wall_length(door_wall_vertices)
                    if room_1.strip() == "exterior" or room_2.strip() == "exterior":
                        if wall_length > 2.5:
                            door_type = "doorway"
                        else:
                            continue
                    if wall_length < 2.5:
                        door_type = "open"
                        
                    door_plan =  {
                        "room_1": room_1.strip(),
                        "room_2": room_2.strip(),
                        "door_wall_vertices": door_wall_vertices,
                        "door_type": door_type.strip(),
                    }
                    door_plans.append(door_plan)
                else:
                    print(f"{Fore.RED}Invalid door plan:{Fore.RESET}", plan)
            return door_plans
        except:
            print(f"{Fore.RED}Invalid door plan:{Fore.RESET}", raw_plan)
            return None    


    def get_all_walls(self, room_vertices, room_id):
        all_walls = []
        for i in range(4):
            if i==3:i = -1
            # get wall rotation
            if i == 0:rotation = [0, 90, 0]
            elif i == 1:rotation = [0, 180, 0]
            elif i == 2:rotation = [0, -90, 0]
            else:rotation = [0, 0, 0]

            vertices_points = sorted([room_vertices[i+1], room_vertices[i]])
            if i == -1: i = 3
            all_walls.append({"vertices_points": vertices_points, "room":room_id, "scale_z":1,"pos_scale":(0,0), "rotation":rotation, "id":i+1})
        return all_walls


    def is_line_in_longer_line(self, line1, line2):
        x1, y1 = line1[0]
        x2, y2 = line1[1]
        x3, y3 = line2[0]
        x4, y4 = line2[1]

        length_line1 = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        length_line2 = ((x4 - x3)**2 + (y4 - y3)**2)**0.5

        return length_line2 >= length_line1 and all(
            min(x3, x4) <= x <= max(x3, x4) and min(y3, y4) <= y <= max(y3, y4)
            for x, y in [line1[0], line1[1]]
        )
               
    def parse_adjacent_walls(self, scene):
        # get all original walls for each room
        for j in range(len(scene["rooms"])):
            
            room_vertices = scene["rooms"][j]["vertices"] 
            all_walls = self.get_all_walls(room_vertices, scene["rooms"][j]["id"])
            
            
            scene["rooms"][j]["original_walls"] = all_walls[:]
            scene["rooms"][j]["subwalls"] = []
            scene["rooms"][j]["whole_walls"] = all_walls[:]


        # get the adjacent walls between rooms, you should note that only one wall can be adjacent between rooms
        common_walls = []
        for m in range(len(scene["rooms"])):
            for n in range(m+1, len(scene["rooms"])):
                for wall1 in scene["rooms"][m]["original_walls"]:
                    for wall2 in scene["rooms"][n]["original_walls"]:
                        
                        common_part, [uncommon_part_wall1, uncommon_part_wall2] = self.common_and_uncommon_parts(wall1["vertices_points"], wall2["vertices_points"])
                        if common_part:
                            common_walls.append({"room_1": scene["rooms"][m]["id"], "room_2": scene["rooms"][n]["id"], "vertices": common_part})
                            
                            pos_scale = self.get_pos_scale_according_to_rotation(wall1["rotation"])
                            scene["rooms"][m]["subwalls"].append({"vertices_points": common_part, "scale_z":0.5,"pos_scale":pos_scale, "rotation":wall1["rotation"]})
                            
                            pos_scale = self.get_pos_scale_according_to_rotation(wall2["rotation"])
                            scene["rooms"][n]["subwalls"].append({"vertices_points": common_part, "scale_z":0.5,"pos_scale":pos_scale, "rotation":wall2["rotation"]})
                            
                            if wall1 in scene["rooms"][m]["whole_walls"]:
                                scene["rooms"][m]["whole_walls"].remove(wall1)
                            if wall2 in scene["rooms"][n]["whole_walls"]:
                                scene["rooms"][n]["whole_walls"].remove(wall2)

                            if uncommon_part_wall1:
                                for uncommon_part_wall1_i in uncommon_part_wall1:
                                    scene["rooms"][m]["subwalls"].append({"vertices_points": uncommon_part_wall1_i, "scale_z":1,"pos_scale":(0,0), "rotation":wall1["rotation"]})
                                    
                            if uncommon_part_wall2:
                                for uncommon_part_wall2_i in uncommon_part_wall2:
                                    scene["rooms"][n]["subwalls"].append({"vertices_points": uncommon_part_wall2_i, "scale_z":1,"pos_scale":(0,0), "rotation":wall2["rotation"]})       
                            
        scene["common_walls"] = common_walls
        # # Output
        for room in scene["rooms"]:
            unique_vertice_points = []
            for wall in room["subwalls"]:
                if wall["vertices_points"] not in unique_vertice_points and wall["scale_z"] != 1:
                    unique_vertice_points.append(wall["vertices_points"])
                
            for wall in room["subwalls"]:
                if wall["vertices_points"] in unique_vertice_points and wall["scale_z"] == 1:
                    room["subwalls"].remove(wall)

        return scene
    

    def get_pos_scale_according_to_rotation(self, rotation):
        if rotation[1] == 90: pos_x,pos_z = 0.5,0
        if rotation[1] == 180: pos_x,pos_z = 0,-0.5
        if rotation[1] == -90: pos_x,pos_z = -0.5,0
        if rotation[1] == 0: pos_x,pos_z = 0,0.5
        return (pos_x, pos_z)


    def common_and_uncommon_parts(self, wall1, wall2):
        wall1 = sorted(wall1)
        wall2 = sorted(wall2)
        # Check if walls are parallel
        if wall1[0][0] == wall1[1][0] == wall2[0][0] == wall2[1][0]:
            # Find common part
            common_ends = [max(wall1[0][1], wall2[0][1]), min(wall1[1][1], wall2[1][1])]
            # If no common
            if common_ends[0] >= common_ends[1]:
                common_ends = None
                return None, [None, None]
            else:
                common_part = [(wall1[0][0], common_ends[0]), (wall1[0][0], common_ends[1])]
                # for wall1
                uncommon_part_1 = []
                if wall1[0][1] < common_ends[0]:
                    part_1 = [wall1[0], (wall1[0][0], common_ends[0])]
                    uncommon_part_1.append(part_1)
                if wall1[1][1] > common_ends[1]:
                    part_2 = [(wall1[0][0], common_ends[1]), wall1[1]]
                    uncommon_part_1.append(part_2)
                # for wall2
                uncommon_part_2 = []
                if wall2[0][1] < common_ends[0]:
                    part_1 = [wall2[0], (wall2[0][0], common_ends[0])]
                    uncommon_part_2.append(part_1)
                if wall2[1][1] > common_ends[1]:
                    part_2 = [(wall2[0][0], common_ends[1]), wall2[1]]
                    uncommon_part_2.append(part_2)
                return common_part, [uncommon_part_1, uncommon_part_2]

            

        elif wall1[0][1] == wall1[1][1] == wall2[0][1] == wall2[1][1]:
            # Find common part
            common_ends = [max(wall1[0][0], wall2[0][0]), min(wall1[1][0], wall2[1][0])]
            if common_ends[0] >= common_ends[1]:
                common_ends = None
                return None, [None, None]
            else:
                common_part = [(common_ends[0], wall1[0][1]), (common_ends[1], wall1[0][1])] 
                # common_part = [(wall1[0][0], common_ends[0]), (wall1[0][0], common_ends[1])]
                # for wall1
                uncommon_part_1 = []
                if wall1[0][0] < common_ends[0]:
                    part_1 = [wall1[0], (common_ends[0], wall1[0][1])]
                    uncommon_part_1.append(part_1)
                if wall1[1][0] > common_ends[1]:
                    part_2 = [(common_ends[1], wall1[0][1]), wall1[1]]
                    uncommon_part_1.append(part_2)
                # for wall2
                uncommon_part_2 = []
                if wall2[0][0] < common_ends[0]:
                    part_1 = [wall2[0], (common_ends[0], wall2[0][1])]
                    uncommon_part_2.append(part_1)
                if wall2[1][0] > common_ends[1]:
                    part_2 = [(common_ends[1], wall2[0][1]), wall2[1]]
                    uncommon_part_2.append(part_2)
                return common_part, [uncommon_part_1, uncommon_part_2]

        else:
            # If the walls don't overlap, return None for common part and uncommon parts
            return None, [None, None]
    

    def place_door_for_each_wall(self, scene):
        # get every detailed info for each wall
        instances = []
        for j in range(len(scene["door_plans"])):
            door_type = scene["door_plans"][j]["door_type"]
            door_wall_vertices = scene["door_plans"][j]["door_wall_vertices"]
            if door_type != "open":
                # Unpack the vertices for readability
                (x1, y1), (x2, y2) = door_wall_vertices

                # Calculate minimum and maximum based on the orientation of the wall
                if x1 == x2:  # Vertical wall
                    minimum, maximum = sorted([y1, y2])
                else:  # Horizontal wall
                    minimum, maximum = sorted([x1, x2])

                # Add buffer of 1.25 from each end to avoid placing the door at the edge
                buffer = 1.25
                minimum += buffer
                maximum -= buffer

                # Generate door center based on the wall orientation
                if "door_center" in scene["door_plans"][j]:
                    door_center = scene["door_plans"][j]["door_center"]
                else:
                    door_center = [x1, random.uniform(minimum, maximum)] if x1 == x2 else [random.uniform(minimum, maximum), y1]
                    scene["door_plans"][j]["door_center"] = door_center
            
            for m in range(1,3):
                room = scene["door_plans"][j][f"room_{m}"]
                if room == "exterior":
                    pass
                
                else:
                    # if open then no wall here:
                    if door_type == "open":
                        mid_point = midpoint(door_wall_vertices[0], door_wall_vertices[1])
                        door_center = [mid_point[0], mid_point[1]]
                        door_size = max(abs(door_wall_vertices[0][0]-door_wall_vertices[1][0]), abs(door_wall_vertices[0][1]-door_wall_vertices[1][1]))
                        instances.append({"door_wall_vertices":door_wall_vertices, "door_center":door_center, "door_type":door_type, "door_size":door_size, "room":room})  
                    else:
                        wall_material_name = random.choice(self.object_type_to_names["one_type_one_wall"])[:-1]+"1"
                        door_wall_size = get_asset_info(wall_material_name[:-1]+"2", self.asset_list)["size"] 
                        instances.append({"door_wall_vertices":door_wall_vertices,"door_center":door_center, "door_type":door_type, "door_size":1.2, "wall_material_name":wall_material_name, "door_wall_size":door_wall_size, "room":room}) 
                

            if door_type == "doorway":
                if door_wall_vertices[0][0] == door_wall_vertices[1][0]:rotation = [0, 90, 0]
                else:rotation = [0, 0, 0]
                scale = [1, 1, 1]
                door_name = random.choice(self.object_type_to_names["Door"])
                size = get_asset_info(door_name, self.asset_list)["size"]
                position = [door_center[0], size["y"]/2+0.1, door_center[1]]
                door_instance = get_instance(door_name, position, rotation, scale, "kinematics", size, door_type=door_type, door_center=door_center, door_wall_vertices=door_wall_vertices)
                instances.append(door_instance) 
            
        return instances
    
    def extract_vertices(self, input_string):
        pattern = re.compile(r'\((-?[\d\.]+), *(-?[\d\.]+)\)')
        matches = pattern.findall(input_string)
        vertices = [[float(x), float(y)] for x, y in matches]
        return vertices