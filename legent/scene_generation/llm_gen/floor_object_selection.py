from colorama import Fore
from langchain.prompts import PromptTemplate
from legent.scene_generation.llm_gen import prompts
from legent.scene_generation.llm_gen.utils import find_most_similar_word, move_polygons_many_times
import re
import random
from shapely import Polygon, Point
from legent.scene_generation.llm_gen.utils import get_asset_info, get_wall_length, get_instance


class FloorObjectGenerator():
    def __init__(self, llm, available_large_objects, asset_list, nlp):
        self.json_template = {"instances": []} 
        self.floor_object_template = PromptTemplate(input_variables=["input", "object_categories", "room", "object_wall_vertices", "additional_requirements"], template=prompts.floor_object_selection_prompt)
        self.llm = llm
        self.floor_height = 0.1
        self.available_large_objects = available_large_objects
        self.asset_list = asset_list
        self.nlp = nlp
        

    def generate_objects(self, scene, additional_requirements="N/A", plot=False):
        # get floor object plan if not provided        
        scene = self.get_available_wall_vertices(scene)
        object_wall_vertices = ""
        for room in scene["rooms"]:
            object_wall_vertices += f"\n[{room['id']}]\n"
            object_wall_vertices += "\n".join([str(wall["id"]) + " | " + ", ".join(str(i) for i in wall["vertices_points"]) for wall in room["object_wall_vertices"]]).replace("[", "(").replace("]", ")")
        object_categories_and_size = ", ".join([obj_type for obj_type in self.available_large_objects])
        floor_object_prompt = self.floor_object_template.format(input=scene["query"], object_categories=object_categories_and_size, room=room["id"], object_wall_vertices=object_wall_vertices, additional_requirements=additional_requirements)
        print(f"User: {floor_object_prompt}\n")
        if "raw_floor_object_plans" not in scene:
            raw_floor_object_plan = self.llm(floor_object_prompt)
            scene["raw_floor_object_plans"] = raw_floor_object_plan
        else:
            raw_floor_object_plan = scene["raw_floor_object_plans"]
        print(f"{Fore.GREEN}AI: Here is the floor object selection plan:\n{raw_floor_object_plan}{Fore.RESET}")
        # parse doorway plan
        scene["floor_object_plan"] = self.parse_plan(scene) 
        floor_object_placement = self.place_floor_objects(scene)
        scene["floor_objects"] = self.replace_floor_objects(floor_object_placement, scene)
        scene["floor_objects"] = floor_object_placement
        return scene


    def extract_output(self, text):
        parts = re.split(r'\[|\]', text)
        parts = [part.strip() for part in parts if part.strip()]
        room_dict = {}
        
        for i in range(0, len(parts), 2):
            room_name = parts[i]
            room_details = parts[i+1]
            room_details_clean = room_details.strip()
            room_dict[room_name] = room_details_clean
        
        return room_dict


    def parse_plan(self, scene):
        try:
            parsed_plans = []
            room_dict = self.extract_output(scene["raw_floor_object_plans"])
            for room_name, room_details in room_dict.items():
                wall_objects = room_details.split("\n")
                for wall_object in wall_objects:
                    wall_id, wall_vertices, object_info = wall_object.split("|")
                    object_list = [object.strip() for object in object_info.split(",")]
                    wall_id = wall_id.strip()
                    room = [room for room in scene["rooms"] if room["id"] == room_name][0]
                    object_wall_vertices = room["object_wall_vertices"]
                    try:
                        wall_id = int(wall_id)
                        rotation = [wall["rotation"] for wall in object_wall_vertices if wall["id"] == wall_id][0]
                    except:
                        rotation = [0, 0, 0]

                    parsed_plan =  {
                        "wall_id": wall_id,
                        "wall_vertices": wall_vertices.strip(),
                        "object_list": object_list,
                        "rotation": rotation,
                        "room_bbox": room["vertices"],
                        "room_id": room_name,
                    }
                    parsed_plans.append(parsed_plan)
            return parsed_plans
        except Exception as e:
            print(f"{Fore.RED}Invalid floor object plan:{Fore.RESET}", scene["raw_floor_object_plans"])
            print(f"{Fore.RED}Error:{Fore.RESET}", e)
            return None    
    

    def generate_random_floats(self, n, max_value):
        # Generate n random numbers
        random_floats = [random.uniform(0, max_value) for _ in range(n)]
        total = sum(random_floats)
        if total < max_value:
            return random_floats
        else:
            # Scale the numbers to fit the max_value constraint
            scale = max_value / total
            scaled_floats = [x * scale for x in random_floats]
            epsilon = sum(scaled_floats) - max_value
            scaled_floats[0] -= epsilon  # Subtract the epsilon from the first number
            return scaled_floats
        

    def get_min_max_coordinates(self, vertices):
        if not vertices or len(vertices) < 4:
            raise ValueError("Invalid vertices. A room must have at least 4 vertices.")

        # Initialize min and max values for x and y
        min_x = min(vertices, key=lambda v: v[0])[0]
        max_x = max(vertices, key=lambda v: v[0])[0]
        min_y = min(vertices, key=lambda v: v[1])[1]
        max_y = max(vertices, key=lambda v: v[1])[1]

        return min_x, max_x, min_y, max_y
    


    def sequential_placer(self, wall_vertices, instance_info):
        wall_length = max(abs(wall_vertices[0][1]-wall_vertices[1][1]), abs(wall_vertices[0][0]-wall_vertices[1][0]))
        instance_lengths = [instance['size']["x"] for instance in instance_info]
        while sum(instance_lengths) > wall_length and instance_lengths:
            instance_info.pop(-1)
            instance_lengths = [subline['size']["x"] for subline in instance_info]
        
        # If all sublines are removed, raise an error
        if not instance_lengths:
            # print(f"{Fore.RED}No sublines can fit on the wall: {wall_vertices}.{Fore.RESET}")
            return None
        
        remaining_length = wall_length - sum(instance_lengths)
        
        # Randomly choose starting points for the sublines on the remaining line
        starting_points = self.generate_random_floats(len(instance_info), remaining_length)
        starting_points.sort()  # Ensure the starting points are in order
        # Place each subline and calculate their positions and center points
        current_position = min(wall_vertices[0][1], wall_vertices[1][1]) if wall_vertices[0][0] == wall_vertices[1][0] else min(wall_vertices[0][0], wall_vertices[1][0])
        for start_point, subline_dict in zip(starting_points, instance_info):
            adjusted_start_point = current_position + start_point
            end_point = adjusted_start_point + subline_dict['size']['x']
            center_point = (adjusted_start_point + end_point) / 2
            current_position = end_point
            subline_dict["position"] = center_point
            
            assert center_point >= min(wall_vertices[0][1], wall_vertices[1][1]) and center_point <= max(wall_vertices[0][1], wall_vertices[1][1]) if wall_vertices[0][0] == wall_vertices[1][0] else center_point >= min(wall_vertices[0][0], wall_vertices[1][0]) and center_point <= max(wall_vertices[0][0], wall_vertices[1][0])
        return instance_info
    

    def place_floor_objects(self, scene):
        instances = []
        unique_objects = []
        for plan in scene["floor_object_plan"]:
            wall_vertices = self.extract_vertices(plan["wall_vertices"])
            room_vertices = plan["room_bbox"]
            min_x, max_x, min_y, max_y = self.get_min_max_coordinates(room_vertices)
            floor_height = self.floor_height
            wall_id = plan["wall_id"]
            wall_width = scene["walls"][0]["size"]["z"]
            objects_on_wall = []
            rotation = plan["rotation"]
                      
                    
            for original_object_category in plan["object_list"]:
                object_category = find_most_similar_word(original_object_category, self.available_large_objects, self.nlp)
                if not object_category:
                    # print(f"{Fore.RED}No objects found for:{Fore.RESET}", original_object_category)
                    continue

                # get object_id
                object_id = object_category+"0"
                if object_id not in unique_objects:
                    unique_objects.append(object_id)
                else:
                    last_object = [item for item in unique_objects if item[:-1]==object_category][-1]
                    object_id = object_category+str(int(last_object[-1])+1)
                

                # get the instance that is smaller than the wall and save the possible names
                average_size = self.available_large_objects[object_category]["average_size"]
                if len(wall_vertices)==2:
                    possible_names = []
                    wall_length = get_wall_length(wall_vertices)
                    if average_size[1] <= wall_length:
                        for name in self.available_large_objects[object_category]["names"]:
                            instance_info = get_asset_info(name, self.asset_list)
                            if instance_info and instance_info["size"]["x"] <= wall_length:
                                possible_names.append(name)
                    else:
                        # print(f"{Fore.RED}Removed {object_category}!{Fore.RESET}")
                        continue   
                else:
                    possible_names = [name for name in self.available_large_objects[object_category]["names"] if get_asset_info(name, self.asset_list)]

                
                if not possible_names:
                    continue

                instance_name = random.choice(possible_names)
                instance_info = get_asset_info(instance_name, self.asset_list)
                size = instance_info["size"]
                scale = [1, 1, 1]   
                
                objects_on_wall.append({"instance_name": instance_name, 
                                        "interactable": instance_info["type"],
                                        "size": size, 
                                        "scale": scale,
                                        "placeable_surfaces": instance_info["placeable_surfaces"],
                                        "object_id": object_id})
            


            if len(wall_vertices)==2:
                
                final_objects_on_wall = self.sequential_placer(wall_vertices, objects_on_wall)
                if final_objects_on_wall:
                    for object in final_objects_on_wall:
                        size = object["size"]
                        
                        bbox = []
                        # then adjust the position
                        if wall_id == 1:
                            final_position = [wall_vertices[0][0] + size["z"]/2 + wall_width/2, size["y"]/2 + floor_height, object["position"]]
                        if wall_id == 2:
                            final_position = [object["position"], size["y"]/2 + floor_height, wall_vertices[0][1] - size["z"]/2 - wall_width/2] 
                        if wall_id == 3:
                            final_position = [wall_vertices[0][0] - size["z"]/2 - wall_width/2, size["y"]/2 + floor_height, object["position"]]
                        if wall_id == 4:
                            final_position = [object["position"], size["y"]/2 + floor_height, wall_vertices[0][1] + size["z"]/2 + wall_width/2]
                        # if verticle wall
                        if wall_id in [1,3]:
                            bbox.append([final_position[0]-size["z"]/2, final_position[2]-size["x"]/2])
                            bbox.append([final_position[0]-size["z"]/2, final_position[2]+size["x"]/2])
                            bbox.append([final_position[0]+size["z"]/2, final_position[2]+size["x"]/2])
                            bbox.append([final_position[0]+size["z"]/2, final_position[2]-size["x"]/2])
                        # if horizontal wall
                        else:
                            bbox.append([final_position[0]-size["x"]/2, final_position[2]-size["z"]/2])
                            bbox.append([final_position[0]-size["x"]/2, final_position[2]+size["z"]/2])
                            bbox.append([final_position[0]+size["x"]/2, final_position[2]+size["z"]/2])
                            bbox.append([final_position[0]+size["x"]/2, final_position[2]-size["z"]/2])
                        
                        instance = get_instance(object["instance_name"], final_position, rotation, object["scale"], object["interactable"], size, placeable_surfaces=object["placeable_surfaces"], bbox=bbox, id=object["object_id"], room_id=plan["room_id"])
                        instances.append(instance)

            else:
                for object in objects_on_wall:
                    size = object["size"]
                    
                    if min_x + size["x"]+1 < max_x and min_y + size["x"]+1 < max_y:
                        position_x = random.uniform(min_x + size["x"]/2 + 1/2, max_x - size["x"]/2 - 1/2)
                        position_y = random.uniform(min_y + size["x"]/2 + 1/2, max_y - size["x"]/2 - 1/2)
                        bbox = []
                        final_position = [position_x, size["y"]/2 + floor_height, position_y]
                        bbox.append([final_position[0]-size["x"]/2, final_position[2]-size["z"]/2])
                        bbox.append([final_position[0]-size["x"]/2, final_position[2]+size["z"]/2])
                        bbox.append([final_position[0]+size["x"]/2, final_position[2]+size["z"]/2])
                        bbox.append([final_position[0]+size["x"]/2, final_position[2]-size["z"]/2])     
                        instance = get_instance(object["instance_name"], final_position, rotation, object["scale"], object["interactable"], size, placeable_surfaces=object["placeable_surfaces"], bbox=bbox, id=object["object_id"], room_id=plan["room_id"])
                        instances.append(instance)
                    else:
                        # print(f"{Fore.RED}No space for {object_category} in the room:{Fore.RESET}")
                        continue
                
            
        return instances
    

    def replace_floor_objects(self, floor_object_instances, scene):
        all_rooms_instances = []
        for room in scene["rooms"]:
            room_bbox = room["vertices"]
            room_id = room["id"]
            room_object_instances = [instance for instance in floor_object_instances if "room_id" in instance and instance["room_id"]==room_id]
            door_instances = [door for door in scene["doors"] if "room" in door and door["room"]==room_id]
            for instance in room_object_instances:
                instance["movable"] = True
                if instance["id"] in ["Bed0", "Sofa0"]:
                    instance["keep"] = True
                else:
                    instance["keep"] = False

            for instance in door_instances:
                instance["movable"] = False
                instance["keep"] = True
                instance["bbox"] = self.get_door_bbox_according_to_center(instance["door_center"], instance["door_wall_vertices"], room_bbox, door_length=1.2)
            room_object_instances.extend([instance for instance in door_instances if "bbox" in instance])
            
            all_instances = move_polygons_many_times(room_object_instances, room_bbox)
            for instance in all_instances:
                if "id" in instance:
                    x = [vertex[0] for vertex in instance["bbox"]]
                    y = [vertex[1] for vertex in instance["bbox"]]
                    center_x = sum(x) / len(x)
                    center_y = sum(y) / len(y)
                    instance["position"] = [center_x, instance["position"][1], center_y]
            all_instances = [instance for instance in all_instances if "id" in instance]
            all_rooms_instances.extend(all_instances)
        return all_rooms_instances


    def get_door_bbox_according_to_center(self, door_center, door_wall_vertices, room_bbox, door_length):
        door_vertices = [[],[],[],[]]
        door_length = door_length+0.22
        # vertical door
        if door_wall_vertices[0][0] == door_wall_vertices[1][0]:
            if Polygon(room_bbox).contains(Point([door_center[0]+door_length, door_center[1]])):
                door_vertices[0] = [door_center[0], door_center[1]-door_length/2]
                door_vertices[1] = [door_center[0], door_center[1]+door_length/2]
                door_vertices[3] = [door_center[0]+door_length, door_center[1]-door_length/2]
                door_vertices[2] = [door_center[0]+door_length, door_center[1]+door_length/2]
            else:
                door_vertices[3] = [door_center[0], door_center[1]-door_length/2]
                door_vertices[2] = [door_center[0], door_center[1]+door_length/2]
                door_vertices[0] = [door_center[0]-door_length, door_center[1]-door_length/2]
                door_vertices[1] = [door_center[0]-door_length, door_center[1]+door_length/2]
        elif door_wall_vertices[0][1] == door_wall_vertices[1][1]:     
            if Polygon(room_bbox).contains(Point([door_center[0], door_center[1]+door_length])):
                door_vertices[0] = [door_center[0]-door_length/2, door_center[1]]
                door_vertices[3] = [door_center[0]+door_length/2, door_center[1]]
                door_vertices[1] = [door_center[0]-door_length/2, door_center[1]+door_length]
                door_vertices[2] = [door_center[0]+door_length/2, door_center[1]+door_length]
            else:
                door_vertices[1] = [door_center[0]-door_length/2, door_center[1]]
                door_vertices[2] = [door_center[0]+door_length/2, door_center[1]]
                door_vertices[0] = [door_center[0]-door_length/2, door_center[1]-door_length]
                door_vertices[3] = [door_center[0]+door_length/2, door_center[1]-door_length]
        return door_vertices

    
    
    def get_available_wall_vertices(self, scene):
        for room in scene["rooms"]:
            object_wall_vertices = []
            room_vertices = room["vertices"]
            doors = [door for door in scene["doors"] if "room" in door and door["room"]==room["id"]]
            
            
            for i in range(4):
                if i==3:i = -1

                # get rotation
                if i == 0:rotation = [0, 90, 0]
                elif i == 1:rotation = [0, 180, 0]
                elif i == 2:rotation = [0, -90, 0]
                else:rotation = [0, 0, 0]

                vertices_points = [(room_vertices[i+1][0],room_vertices[i+1][1]), (room_vertices[i][0],room_vertices[i][1])]
                if i==-1:i = 3
                add_whole_wall = True

                # get multiple doors on a wall
                sublines = []
                
                for door in doors:
                    subline = self.get_door_subline(vertices_points, door["door_center"], door["door_size"])
                    if subline:
                        sublines.append(subline)
                

                if sublines:
                    multiple_parts = self.get_separated_lines(vertices_points, sublines)
                    for part in multiple_parts:
                        object_wall_vertices.append({"vertices_points": part, "rotation":rotation, "id":i+1})
                    add_whole_wall = False
                if add_whole_wall:
                    object_wall_vertices.append({"vertices_points": vertices_points, "rotation":rotation, "id":i+1})
                
            room["object_wall_vertices"] = object_wall_vertices
            # print(f"{Fore.YELLOW}{object_wall_vertices}{Fore.RESET}")
        return scene


    # separate a line by a subline
    def get_separated_lines(self, line, sublines):
        line = sorted(line)
        output_lines = []

        # test if vertical line
        if line[0][0] == line[1][0] == sublines[0][0][0]:
            subpoints = []

            for subline in sublines:
                subpoints.extend([subline[0][1], subline[1][1]])
            
            subpoints = sorted(subpoints)
            subpoints.append(line[1][1])

            start = line[0][1]
            for point in subpoints:
                end = point
                if end > start:
                    output_lines.append([[line[0][0], start], [line[0][0], end]])
                start = point
        
        elif line[0][1] == line[1][1] == sublines[0][0][1]:
            subpoints = []

            for subline in sublines:
                subpoints.extend([subline[0][0], subline[1][0]])
            
            subpoints = sorted(subpoints)
            subpoints.append(line[1][0])

            start = line[0][0]
            for point in subpoints:
                end = point
                if end > start:
                    output_lines.append([[start, line[0][1]], [end, line[0][1]]])
                start = point
        if output_lines:
            for l in sublines:
                if l in output_lines:
                    output_lines.remove(l)
        return output_lines


    def get_door_subline(self, line, point, door_size):
        x1, y1 = line[0]
        x2, y2 = line[1]
        x, y = point

        # Check if the line is vertical
        if x1 == x2:
            if x == x1 and y >= min(y1, y2) and y <= max(y1, y2):
                return [[x1,round((y-door_size/2),1)], [x2, round((y+door_size/2),1)]]
        # Check if the line is horizontal
        if y1 == y2:
            if y == y1 and x >= min(x1, x2) and x <= max(x1, x2):
                return [[round((x-door_size/2),1), y1], [round((x+door_size/2),1), y2]]

    
    def extract_points(self, input_string):
        pattern = re.compile(r'\((-?[\d\.]+), *(-?[\d\.]+)\)')
        matches = pattern.findall(input_string)
        vertices = [[float(x), float(y)] for x, y in matches][0]
        return vertices


    def extract_vertices(self, input_string):
        pattern = re.compile(r'\((-?[\d\.]+), *(-?[\d\.]+)\)')
        matches = pattern.findall(input_string)
        vertices = [(float(x), float(y)) for x, y in matches]
        return vertices