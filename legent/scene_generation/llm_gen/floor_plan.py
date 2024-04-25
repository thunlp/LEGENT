import ast
import copy
import math
from colorama import Fore
from langchain.prompts import PromptTemplate
from shapely.geometry import LineString, Point, Polygon
from legent.scene_generation.llm_gen import prompts
from legent.scene_generation.llm_gen.utils import get_asset_info, get_asset_name, get_instance
from legent.scene_generation.llm_gen.utils import midpoint


class FloorPlanGenerator():
    def __init__(self, llm, asset_list, object_type_to_names):
        self.json_template = {"instances": []} 
        self.floor_plan_template = PromptTemplate(input_variables=["input", "additional_requirements"], template=prompts.floor_plan_prompt)
        self.llm = llm
        self.asset_list = asset_list
        self.object_type_to_names = object_type_to_names

    def generate_rooms(self, scene, additional_requirements="N/A"):
        # get floor plan if not provided
        floor_plan_prompt = self.floor_plan_template.format(input=scene["query"], additional_requirements=additional_requirements)
        print(f"User: {floor_plan_prompt}\n")
        if "raw_floor_plan" not in scene:
            raw_floor_plan = self.llm(floor_plan_prompt)
            scene["raw_floor_plan"] = raw_floor_plan
        else:
            raw_floor_plan = scene["raw_floor_plan"]
        
        print(f"{Fore.GREEN}AI: Here is the floor plan:\n{raw_floor_plan}{Fore.RESET}")
        return self.get_plan(scene["raw_floor_plan"])


    def get_plan(self, raw_plan):
        parsed_plan = self.parse_raw_plan(raw_plan)
        
        # assign materials
        vertices = []
        for i in range(len(parsed_plan)):
            instance_name = get_asset_name("Floor", self.object_type_to_names)
            instance_size = get_asset_info(instance_name, self.asset_list)["size"]
            rotation = [0, 0, 0]
            position, scale = self.vertices2postion_scale(parsed_plan[i]["vertices"], instance_size)
            instance = get_instance(instance_name, position, rotation, scale, "kinematic", instance_size)
            parsed_plan[i]["instances"].append(instance)

            vertices.extend(parsed_plan[i]["vertices"])

        center_x = max(vertex[0] for vertex in vertices)/2
        center_z = max(vertex[1] for vertex in vertices)/2

        center = [center_x, 1.5*(abs(center_x)+abs(center_z)), center_z]
        return parsed_plan, center
    
    def vertices2postion_scale(self, vertices, instance_size):
        mid_point = midpoint(vertices[0], vertices[2])
        position = [mid_point[0], 0.05, mid_point[1]]
        scale_x = (vertices[2][0]- vertices[0][0])/ instance_size['x']
        scale_z = (vertices[2][1]- vertices[0][1]) / instance_size['z']
        scale = [scale_x, 0.1/instance_size['y'], scale_z]

        return position, scale
    

    def sort_vertices(self, vertices):
        # Calculate the centroid of the polygon
        cx = sum(x for x, y in vertices) / max(len(vertices), 1)
        cy = sum(y for x, y in vertices) / max(len(vertices), 1)

        # Sort the vertices in clockwise order
        vertices_clockwise = sorted(vertices, key=lambda v: (-math.atan2(v[1]-cy, v[0]-cx)) % (2*math.pi))

        # Find the vertex with the smallest x value
        min_vertex = min(vertices_clockwise, key=lambda v: v[0])

        # Rotate the vertices so the vertex with the smallest x value is first
        min_index = vertices_clockwise.index(min_vertex)
        vertices_clockwise = vertices_clockwise[min_index:] + vertices_clockwise[:min_index]

        return vertices_clockwise

    def parse_raw_plan(self, raw_plan):
        parsed_plan = []
        room_types = []
        plans = [plan.lower() for plan in raw_plan.split("\n") if "|" in plan]
        for i, plan in enumerate(plans):
            room_type, vertices = plan.split("|")
            room_type = room_type.strip().replace("'", "") # remove single quote

            if room_type in room_types: room_type += f"-{i}"
            room_types.append(room_type)

            vertices = ast.literal_eval(vertices.strip())
            # change to float
            vertices = [(float(vertex[0]), float(vertex[1])) for vertex in vertices]

            current_plan = copy.deepcopy(self.json_template)
            current_plan["id"] = room_type
            current_plan["roomType"] = room_type
            current_plan["vertices"]= self.sort_vertices(vertices)
            parsed_plan.append(current_plan)

        # get full vertices: consider the intersection with other rooms
        all_vertices = []
        for room in parsed_plan:
            all_vertices += room["vertices"]
        all_vertices = list(set(map(tuple, all_vertices)))

        valid, msg = self.check_validity(parsed_plan)

        if not valid: print(f"{Fore.RED}AI: {msg}{Fore.RESET}"); raise ValueError(msg)
        else: print(f"{Fore.GREEN}AI: {msg}{Fore.RESET}"); return parsed_plan
    
   
    def check_interior_angles(self, vertices):
        n = len(vertices)
        for i in range(n):
            a, b, c = vertices[i], vertices[(i + 1) % n], vertices[(i + 2) % n]
            angle = abs(math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0])))
            if angle < 90 or angle > 270:
                return False
        return True
    
    def check_validity(self, rooms):
        room_polygons = [Polygon(room["vertices"]) for room in rooms]
        # for rectangle in room_polygons:
        #     minx, miny, maxx, maxy = rectangle.bounds
        #     if maxx - minx < 2.5 or maxy - miny < 2.5:
        #         return False, "All rooms must have a width and length of at least 2.5 meters."

        # check interior angles
        for room in rooms:
            if not self.check_interior_angles(room["vertices"]):
                return False, "All interior angles of the room must be greater than or equal to 90 degrees."
                
        if len(room_polygons) == 1: 
            return True, "The floor plan is valid. (Only one room)"
                
        # check overlap, connectivity and vertex inside another room
        for i in range(len(room_polygons)):
            has_neighbor = False
            for j in range(len(room_polygons)):
                if i != j:
                    if room_polygons[i].equals(room_polygons[j]) or room_polygons[i].contains(room_polygons[j]) or room_polygons[j].contains(room_polygons[i]) or room_polygons[j].overlaps(room_polygons[i]):
                        return False, "Room polygons must not overlap."
                    intersection = room_polygons[i].intersection(room_polygons[j])
                    if isinstance(intersection, LineString):
                        has_neighbor = True
                    for vertex in rooms[j]["vertices"]:
                        if Polygon(rooms[i]["vertices"]).contains(Point(vertex)):
                            return False, "No vertex of a room can be inside another room."
                        
            if not has_neighbor:
                return False, "Each room polygon must share an edge with at least one other room polygon."

        return True, "The floor plan is valid."