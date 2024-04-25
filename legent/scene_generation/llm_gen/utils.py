import json
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon
import random
from difflib import SequenceMatcher


def get_wall_length(wall_vertices):
    x1, y1 = wall_vertices[0]
    x2, y2 = wall_vertices[1]
    length = abs(x1 - x2) + abs(y1 - y2)
    return length


def get_asset_info(asset_name, asset_list):
    for prefab in asset_list:
        if prefab['name'] == asset_name:
            return prefab


def get_asset_name(object_type, object_type_to_names):
    return random.choice(object_type_to_names[object_type])


def get_instance(instance_name, position, rotation, scale, instance_type, size, **kwargs):
    instance = {}
    instance["prefab"] = instance_name
    instance["position"] = position
    instance["rotation"] = rotation
    instance["scale"] = scale
    instance["type"] = instance_type
    instance["size"] = size
    for key, value in kwargs.items():
        instance[key] = value
    return instance


def midpoint(p1, p2):
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

def load_json(json_file):
    with open(json_file, 'r') as file:
        json_dict = json.load(file)
    return json_dict

def dump_json(json_dict, json_file):
    with open(json_file, 'w', encoding="utf-8") as file:
        json.dump(json_dict, file, ensure_ascii=False, indent=4)
    print(f"Saved into {json_file}")

def sequence_sim(a, b):
    return SequenceMatcher(None, a, b).ratio()

def similar(nlp, a, b):
    similarity = nlp(a).similarity(nlp(b))
    return similarity

def convert_word(word):
    new_word = ""
    for char in word:
        if char.isupper():
            new_word += " " + char.lower()
        else:
            new_word += char
    return new_word.strip()

def find_most_similar_word(word, word_list, nlp):
    if type(word_list) == dict: word_list = list(word_list.keys())
    if word in word_list:
        return word
   
    word = convert_word(word)
    max_semantic_similarity = 0
    random.shuffle(word_list)
    best_match = word_list[0]

    for w in word_list:
        semantic_similarity = similar(nlp, word, convert_word(w))
        if semantic_similarity > max_semantic_similarity:
            max_semantic_similarity, best_match = semantic_similarity, w
    if max_semantic_similarity>0.45:
        print(f"substitue {word} for {best_match}")
        return best_match


def check_collision(polygon1, polygon2):
    poly1 = Polygon(polygon1["bbox"])
    poly2 = Polygon(polygon2["bbox"])
    return poly1.intersects(poly2)


def check_collision_multiple(polygons):
    mp_list = []
    for m in range(len(polygons)):
        for p in range(m + 1, len(polygons)):
            if check_collision(polygons[m], polygons[p]):
                if polygons[m]["movable"] or polygons[p]["movable"]:
                    mp_list.append((m, p))
    if not mp_list:
        return False
    else:
        return random.choice(mp_list)

# plots
def plot_multiple_polygons(polygons, box, save_path=None, save=False):
    plt.figure()
    
    box_x = [vertex[0] for vertex in box]
    box_y = [vertex[1] for vertex in box]
    plt.plot(box_x + [box_x[0]], box_y + [box_y[0]], 'k-', linewidth=2)
    for polygon in polygons:
        
        x = [vertex[0] for vertex in polygon["bbox"]]
        y = [vertex[1] for vertex in polygon["bbox"]]
        plt.plot(x + [x[0]], y + [y[0]])
        # Calculate center of the square
        center_x = sum(x) / len(x)
        center_y = sum(y) / len(y)
        
        # Add text to the center of the square
        text= polygon["id"] if "id" in polygon else "door"
        plt.text(center_x, center_y, text, horizontalalignment='center', verticalalignment='center')
        if "position" in polygon:
            plt.scatter(polygon["position"][0], polygon["position"][2])

    
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.title('Multiple polygons')
    plt.grid(True)
    if save:plt.savefig(save_path)
    else:plt.show()


# main function important
def move_polygons_until_no_collision(polygons, m, n, box, plot=False):
    
    directions = get_initial_move_direction(polygons[m], polygons[n])
   
    reaches_box = 0 # count the number of times it reaches the boundary
    while check_collision(polygons[m], polygons[n]):
        if plot:
            plot_multiple_polygons(polygons,box)
        for i in [m, n]:
            if not polygons[i]["movable"]: continue
            else:
                # print(polygons[i]["bbox"])
                polygons[i] = move_polygon(polygons[i], directions[i==n]/5)
                # print(directions[i==n])
                # print(polygons[i]["bbox"])
                if not within_box(polygons[i], box):

                    polygons[i] = move_polygon(polygons[i], -directions[i==n]/5)
                    # print(polygons[i]["bbox"])
                    
                    directions[i==n] = change_direction(directions[i==n])
                    
                    reaches_box+=1
        if reaches_box>10:
            # print("Both polygons reach the wall!")
            # print(polygons[m]["bbox"], polygons[n]["bbox"])
            return False
    # print("moved two polygons")
    return polygons

# main function important
def move_multiple_polygons_until_no_collision(multiple_polygons, box, plot=True):  
    s = 0
    while True:
        if s>100:
            return False
        if plot:
            plot_multiple_polygons(multiple_polygons, box)
        collision = check_collision_multiple(multiple_polygons)
        
        if collision:
            i, j = collision
            multiple_polygons = move_polygons_until_no_collision(multiple_polygons,i,j, box, plot=plot)
            s += 1
            
            if not multiple_polygons:
                return i, j
        else:
            break
    # print("No collision finally!")
    return multiple_polygons



def change_direction(direction):
    if direction[0] == 0:
        direction[0] = random.choice([1,-1])* random.randint(1,2)
        direction[1] = 0
    elif direction[1] == 0:
        direction[0] = 0
        direction[1] = random.choice([1,-1])* random.randint(1,2)
    return direction


def get_initial_move_direction(polygon1, polygon2):
    centroid1 = np.mean(polygon1["bbox"], axis=0)
    centroid2 = np.mean(polygon2["bbox"], axis=0)
    distance = centroid1 - centroid2
    wall_vertices_list = []
    if "wall_vertices" in polygon1:
        wall_vertices_list.append(polygon1["wall_vertices"])
    if "wall_vertices" in polygon2:
        wall_vertices_list.append(polygon2["wall_vertices"])
    
    # which wall is which object on?
    # on vertical wall
    try:
        wall_vertices = random.choice(wall_vertices_list)
        if wall_vertices[0][0] == wall_vertices[1][0]:
            direction = distance[:]
            direction[0] = 0
            if direction[1] > 0:
                direction[1] = 1
            else:
                direction[1] = -1
            return [direction, -direction]

        # on horizontal wall
        elif wall_vertices[0][1] == wall_vertices[1][1]:
            direction = distance[:]
            direction[1] = 0
            if direction[0] < 0:
                direction[0] = 1
            else:
                direction[0] = -1
            return [direction, -direction]
    except:
        pass
    direction = distance[:]
    if abs(direction[0]) > abs(direction[1]):
        direction[1] = 0
        if abs(direction[0])<1 and  direction[0] <= 0:
            direction[0] =  - 1
        elif abs(direction[0])<1 and  direction[0] >= 0:
            direction[0] = 1
    else:
        direction[0] = 0
        if abs(direction[1])<1 and  direction[1] <= 0:
            direction[1] =  - 1
        elif abs(direction[1])<1 and  direction[1] >= 0:
            direction[1] = 1
    return [direction, -direction]


def move_polygon(polygon, direction):   
    polygon["bbox"] =  [(vertex[0] + direction[0], vertex[1] + direction[1]) for vertex in polygon["bbox"]] 
    return polygon


def multiple_within_box(polygons, bbox):
    for polygon in polygons:
        if within_box(polygon, bbox):
            return True
    return False


def within_box(polygon, bbox):
    if Polygon(bbox).contains(Polygon(polygon["bbox"])):
        return True
    else:
        return False


def move_polygons_many_times(polygons, box, plot=False):
    result = []
    if plot:plot_multiple_polygons(polygons, box)
    s = 0
    while True:
        s += 1
        if s > 100:
            break
        result = move_multiple_polygons_until_no_collision(polygons, box, plot=plot)
        if type(result) == list:
            break
        elif not result:
            list_of_indexes = [i for i in range(len(polygons)) if not polygons[i]["keep"]]
            if len(list_of_indexes) > 0:
                polygons.pop(random.choice(list_of_indexes))
                continue
            else:
                break

        for m in result:
            if polygons[m]["movable"] and not polygons[m]["keep"]:
                polygons.pop(m)
                # print(f"Removed the polygon: {polygons[m]['bbox']}")
                break
            # elif polygons[m]["movable"] and polygons[m]["keep"]:
            #     list_of_movable = [i for i in range(len(polygons)) if polygons[i]["movable"] and i != m]
            #     polygons = swap_position(polygons, m, random.choice(list_of_movable))
            #     break
    return result


# def swap_position(polygons, i, j):
#     original_position = polygons[i]["position"][:]
#     polygons[i]["position"] = polygons[j]["position"]
#     polygons[j]["position"] = original_position

#     direction = [polygons[i]["position"][0] - original_position[0], polygons[i]["position"][2] - original_position[2]]

#     polygons[i]["bbox"] =  [(vertex[0] + direction[0], vertex[1] + direction[1]) for vertex in polygons[i]["bbox"]] 

#     polygons[j]["bbox"] =  [(vertex[0] - direction[0], vertex[1] - direction[1]) for vertex in polygons[j]["bbox"]] 
#     return polygons





if __name__ == "__main__":
    # floor_object_instances = [{'prefab': 'LowPolyInterior2_Refrigerator2_C2', 'position': [7.624999649822712, 1.0000002533197403, 5.0], 'rotation': [0, -90, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 0.6000000238418579, 'y': 1.8000000715255737, 'z': 0.6000002026557922}, 'placeable_surfaces': [{'y': 0.9000001549720764, 'x_min': -0.2990000247955322, 'x_max': -0.2990001142024994, 'z_min': 0.2990000247955322, 'z_max': 0.2990001142024994}], 'bbox': [[7.324999548494816, 4.699999988079071], [7.324999548494816, 5.300000011920929], [7.924999751150608, 5.300000011920929], [7.924999751150608, 4.699999988079071]], 'id': 'Refrigerator0', 'room_id': 'kitchen', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior2_Oven4_01', 'position': [7.617431350052357, 0.5564330071210861, 4.3], 'rotation': [0, -90, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 0.5999999046325684, 'y': 0.9128655791282654, 'z': 0.6151368021965027}, 'placeable_surfaces': [{'y': 0.4285675585269928, 'x_min': -0.05979998782277107, 'x_max': 0.08360955119132996, 'z_min': 0.11959997564554214, 'z_max': 0.25082871317863464}], 'bbox': [[7.309862948954105, 4.000000047683716], [7.309862948954105, 4.599999952316284], [7.924999751150608, 4.599999952316284], [7.924999751150608, 4.000000047683716]], 'id': 'Oven0', 'room_id': 'kitchen', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior_KitchenTable_03', 'position': [6.5, 0.5359568148851395, 5.400165714323521], 'rotation': [0, 180, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 1.5638622045516968, 'y': 0.8719131946563721, 'z': 1.0496680736541748}, 'placeable_surfaces': [{'y': 0.43595659732818604, 'x_min': -0.7809311151504517, 'x_max': -0.4686936140060425, 'z_min': 0.7809311151504517, 'z_max': 0.46869364380836487}, {'y': 0.43595659732818604, 'x_min': -0.6987278461456299, 'x_max': -0.5238340497016907, 'z_min': 0.6987278461456299, 'z_max': 0.5238340497016907}], 'bbox': [[5.718068897724152, 4.875331677496433], [5.718068897724152, 5.924999751150608], [7.281931102275848, 5.924999751150608], [7.281931102275848, 4.875331677496433]], 'id': 'KitchenTable0', 'room_id': 'kitchen', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior_InteractiveSink_02', 'position': [7.6, 0.6201651245355606, 4.3801756128668785], 'rotation': [0, 0, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 1.112493872642517, 'y': 1.0403298139572144, 'z': 0.6103507280349731}, 'placeable_surfaces': [{'y': 0.36287224292755127, 'x_min': -0.5552469491958618, 'x_max': -0.30417537689208984, 'z_min': -0.32145875692367554, 'z_max': 0.30417537689208984}, {'y': 0.36287224292755127, 'x_min': 0.3214587867259979, 'x_max': -0.30417537689208984, 'z_min': 0.5552469491958618, 'z_max': 0.30417537689208984}], 'bbox': [[7.043753063678741, 4.075000248849392], [7.043753063678741, 4.685350976884365], [8.156246936321258, 4.685350976884365], [8.156246936321258, 4.075000248849392]], 'id': 'InteractiveSink0', 'room_id': 'kitchen', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior2_KitchenCorner1_C2_01', 'position': [7.624999739229679, 0.5425002425909042, 4.65], 'rotation': [0, -90, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 0.6000000238418579, 'y': 0.8850000500679016, 'z': 0.6000000238418579}, 'placeable_surfaces': [{'y': 0.44249996542930603, 'x_min': -0.2990000247955322, 'x_max': -0.2990000247955322, 'z_min': 0.2990000247955322, 'z_max': 0.2990000247955322}], 'bbox': [[7.32499972730875, 4.349999988079071], [7.32499972730875, 4.950000011920929], [7.924999751150608, 4.950000011920929], [7.924999751150608, 4.349999988079071]], 'id': 'KitchenCorner0', 'room_id': 'kitchen', 'movable': True, 'keep': False}, {'door_wall_vertices': [[5.0, 4.0], [8.0, 4.0]], 'door_center': [6.5, 4.0], 'door_type': 'doorway', 'door_size': 1.2, 'wall_material_name': 'LowPolyInterior2_Wall3_C2_01', 'door_wall_size': {'x': 2.5, 'y': 3.0, 'z': 0.15000049769878387}, 'room': 'kitchen', 'movable': False, 'keep': True, 'bbox': [[5.9, 4.0], [5.9, 5.2], [7.1, 5.2], [7.1, 4.0]]}]
    # room_bbox =  [(5.0, 4.0), (5.0, 6.0), (8.0, 6.0), (8.0, 4.0)]
    # move_polygons_many_times(floor_object_instances, room_bbox, plot=True)


    # floor_object_instances = [{'prefab': 'LowPolyInterior2_Sofa8_C2', 'position': [0.8716578111052513, 0.4927326589822769, 1.2], 'rotation': [0, 90, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 2.477860689163208, 'y': 0.8675857782363892, 'z': 1.5933151245117188}, 'placeable_surfaces': [{'y': 0.019234895706176758, 'x_min': -0.9773133993148804, 'x_max': -0.46064385771751404, 'z_min': 0.9773133397102356, 'z_max': 0.12563011050224304}, {'y': 0.019234776496887207, 'x_min': 0.4560796022415161, 'x_max': -0.46064385771751404, 'z_min': 0.9773133397102356, 'z_max': 0.7119041681289673}], 'bbox': [[0.07500024884939194, -0.03893034458160405], [0.07500024884939194, 2.438930344581604], [1.6683153733611107, 2.438930344581604], [1.6683153733611107, -0.03893034458160405]], 'id': 'Sofa0', 'room_id': 'living room', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior2_Fireplace_04', 'position': [0.3484719321131706, 1.4839397221803665, 4.8], 'rotation': [0, 90, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 1.3406096696853638, 'y': 2.8499999046325684, 'z': 0.5469433665275574}, 'placeable_surfaces': [{'y': 1.4249999523162842, 'x_min': -0.5283985733985901, 'x_max': -0.27247166633605957, 'z_min': 0.5283985137939453, 'z_max': 0.09082391113042831}], 'bbox': [[0.07500024884939194, 4.129695165157318], [0.07500024884939194, 5.470304834842682], [0.6219436153769493, 5.470304834842682], [0.6219436153769493, 4.129695165157318]], 'id': 'Fireplace0', 'room_id': 'living room', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior_Library', 'position': [2.5, 1.08806212246418, 5.767186529934406], 'rotation': [0, 180, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 1.1330691576004028, 'y': 2.0582447052001953, 'z': 0.31562644243240356}, 'placeable_surfaces': [{'y': 1.0291223526000977, 'x_min': -0.5655345916748047, 'x_max': -0.15681320428848267, 'z_min': 0.5655345916748047, 'z_max': 0.15681323409080505}], 'bbox': [[1.9334654211997986, 5.6093733087182045], [1.9334654211997986, 5.924999751150608], [3.0665345788002014, 5.924999751150608], [3.0665345788002014, 5.6093733087182045]], 'id': 'Library0', 'room_id': 'living room', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior_Lamp_01', 'position': [4.6628419533371925, 0.8463959246873856, 0.7], 'rotation': [0, -90, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 0.524315595626831, 'y': 1.5749123096466064, 'z': 0.524315595626831}, 'placeable_surfaces': [], 'bbox': [[4.400684155523777, 0.43784220218658443], [4.400684155523777, 0.9621577978134155], [4.924999751150608, 0.9621577978134155], [4.924999751150608, 0.43784220218658443]], 'id': 'Lamp0', 'room_id': 'living room', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior_OfficeTable_01', 'position': [4.5320659056305885, 0.4569094628095627, 3.3], 'rotation': [0, -90, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 1.6116658449172974, 'y': 0.7959393858909607, 'z': 0.7858676910400391}, 'placeable_surfaces': [{'y': 0.39796963334083557, 'x_min': -0.804832935333252, 'x_max': -0.3919338583946228, 'z_min': 0.804832935333252, 'z_max': 0.3919338583946228}], 'bbox': [[4.139132060110569, 2.494167077541351], [4.139132060110569, 4.1058329224586485], [4.924999751150608, 4.1058329224586485], [4.924999751150608, 2.494167077541351]], 'id': 'OfficeTable0', 'room_id': 'living room', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior_KitchenTable_03', 'position': [2.5, 0.49489636719226837, 0.5998342856764793], 'rotation': [0, 0, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 1.5638622045516968, 'y': 0.8719131946563721, 'z': 1.0496680736541748}, 'placeable_surfaces': [{'y': 0.43595659732818604, 'x_min': -0.7809311151504517, 'x_max': -0.4686936140060425, 'z_min': 0.7809311151504517, 'z_max': 0.46869364380836487}, {'y': 0.43595659732818604, 'x_min': -0.6987278461456299, 'x_max': -0.5238340497016907, 'z_min': 0.6987278461456299, 'z_max': 0.5238340497016907}], 'bbox': [[1.7180688977241516, 0.07500024884939194], [1.7180688977241516, 1.1246683225035667], [3.2819311022758484, 1.1246683225035667], [3.2819311022758484, 0.07500024884939194]], 'id': 'KitchenTable0', 'room_id': 'living room', 'movable': True, 'keep': False}, {'door_wall_vertices': [[0.0, 0.0], [0.0, 6.0]], 'door_center': [0.0, 3.0], 'door_type': 'doorway', 'door_size': 1.2, 'wall_material_name': 'LowPolyInterior2_Wall1_C5_01', 'door_wall_size': {'x': 2.5, 'y': 3.0, 'z': 0.15000049769878387}, 'room': 'living room', 'movable': False, 'keep': True, 'bbox': [[0.0, 2.4], [0.0, 3.6], [1.2, 3.6], [1.2, 2.4]]}, {'door_wall_vertices': [[5.0, 0.0], [5.0, 4.0]], 'door_center': [5.0, 2.0], 'door_type': 'doorway', 'door_size': 1.2, 'wall_material_name': 'LowPolyInterior2_Wall1_C5_01', 'door_wall_size': {'x': 2.5, 'y': 3.0, 'z': 0.15000049769878387}, 'room': 'living room', 'movable': False, 'keep': True, 'bbox': [[3.8, 1.4], [3.8, 2.6], [5.0, 2.6], [5.0, 1.4]]}]  
    # room_bbox = [(0.0, 0.0), (0.0, 6.0), (5.0, 6.0), (5.0, 0.0)]
    # move_polygons_many_times(floor_object_instances, room_bbox, plot=True)

    # floor_object_instances = [{'prefab': 'LowPolyInterior2_Bed2_C1', 'position': [6.107031546533108, 0.4750003442168236, 0.7], 'rotation': [0, 90, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 1.6332573890686035, 'y': 0.7500002980232239, 'z': 2.0640625953674316}, 'placeable_surfaces': [{'y': 0.03500008583068848, 'x_min': -0.7297730445861816, 'x_max': -0.2713240683078766, 'z_min': 0.2146390974521637, 'z_max': 0.8139719367027283}, {'y': 0.03499990701675415, 'x_min': -0.7297730445861816, 'x_max': -0.2713240683078766, 'z_min': 0.1287834793329239, 'z_max': 0.9225016236305237}, {'y': 0.032348573207855225, 'x_min': -0.7297730445861816, 'x_max': -0.2713240683078766, 'z_min': 0.7297731041908264, 'z_max': 0.48838314414024353}, {'y': 0.039869457483291626, 'x_min': 0.3863504230976105, 'x_max': -0.2713240683078766, 'z_min': 0.7297731041908264, 'z_max': 0.5969128012657166}], 'bbox': [[5.075000248849392, -0.1166286945343018], [5.075000248849392, 1.5166286945343017], [7.139062844216824, 1.5166286945343017], [7.139062844216824, -0.1166286945343018]], 'id': 'Bed0', 'room_id': 'bedroom', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior_Bed_Table_02', 'position': [5.272717289626598, 0.3079482838511467, 0.2], 'rotation': [0, 90, 0], 'scale': [1, 1, 1], 'type': 'interactable', 'size': {'x': 0.4090394973754883, 'y': 0.4158961772918701, 'z': 0.39543408155441284}, 'placeable_surfaces': [{'y': 0.2079479992389679, 'x_min': -0.20351974666118622, 'x_max': -0.1967170387506485, 'z_min': 0.20351974666118622, 'z_max': 0.1967170387506485}], 'bbox': [[5.075000248849392, -0.0045197486877441295], [5.075000248849392, 0.40451974868774415], [5.470434330403805, 0.40451974868774415], [5.470434330403805, -0.0045197486877441295]], 'id': 'Bed_Table0', 'room_id': 'bedroom', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior_Bed_Table_02', 'position': [5.272717289626598, 0.3079482838511467, 1.2], 'rotation': [0, 90, 0], 'scale': [1, 1, 1], 'type': 'interactable', 'size': {'x': 0.4090394973754883, 'y': 0.4158961772918701, 'z': 0.39543408155441284}, 'placeable_surfaces': [{'y': 0.2079479992389679, 'x_min': -0.20351974666118622, 'x_max': -0.1967170387506485, 'z_min': 0.20351974666118622, 'z_max': 0.1967170387506485}], 'bbox': [[5.075000248849392, 0.9954802513122558], [5.075000248849392, 1.404519748687744], [5.470434330403805, 1.404519748687744], [5.470434330403805, 0.9954802513122558]], 'id': 'Bed_Table1', 'room_id': 'bedroom', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior2_Wardrobe5_C2', 'position': [8.666044600307941, 1.2500001713633537, 2.0], 'rotation': [0, -90, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 1.5, 'y': 2.299999952316284, 'z': 0.5179103016853333}, 'placeable_surfaces': [{'y': 1.149999976158142, 'x_min': -0.7490000128746033, 'x_max': -0.2579551339149475, 'z_min': 0.7490000128746033, 'z_max': 0.2579551637172699}], 'bbox': [[8.407089449465275, 1.25], [8.407089449465275, 2.75], [8.924999751150608, 2.75], [8.924999751150608, 1.25]], 'id': 'Wardrobe0', 'room_id': 'bedroom', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior2_Dresser4_C3', 'position': [7.0, 0.5650002285838127, 0.2881443724036217], 'rotation': [0, 0, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 0.9281148910522461, 'y': 0.9300000667572021, 'z': 0.4262882471084595}, 'placeable_surfaces': [{'y': 0.4650000333786011, 'x_min': -0.4630574584007263, 'x_max': -0.21214410662651062, 'z_min': 0.4630574584007263, 'z_max': 0.212144136428833}], 'bbox': [[6.535942554473877, 0.07500024884939194], [6.535942554473877, 0.5012884959578514], [7.464057445526123, 0.5012884959578514], [7.464057445526123, 0.07500024884939194]], 'id': 'Dresser0', 'room_id': 'bedroom', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior2_Sofa1_C2', 'position': [8.0, 0.5280599817633629, 3.4249996915459633], 'rotation': [0, 180, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 1.7860548496246338, 'y': 0.8561195731163025, 'z': 1.0000001192092896}, 'placeable_surfaces': [{'y': 0.071429044008255, 'x_min': -0.610334575176239, 'x_max': -0.18384213745594025, 'z_min': 0.610334575176239, 'z_max': 0.44647377729415894}], 'bbox': [[7.106972575187683, 2.9249996319413185], [7.106972575187683, 3.924999751150608], [8.893027424812317, 3.924999751150608], [8.893027424812317, 2.9249996319413185]], 'id': 'Sofa0', 'room_id': 'bedroom', 'movable': True, 'keep': False}, {'door_wall_vertices': [[5.0, 0.0], [5.0, 4.0]], 'door_center': [5.0, 2.0], 'door_type': 'doorway', 'door_size': 1.2, 'wall_material_name': 'LowPolyInterior2_Wall2_C7_01', 'door_wall_size': {'x': 2.5, 'y': 3.0, 'z': 0.15000049769878387}, 'room': 'bedroom', 'movable': False, 'keep': True, 'bbox': [[5.0, 1.4], [5.0, 2.6], [6.2, 2.6], [6.2, 1.4]]}, {'door_wall_vertices': [[5.0, 4.0], [8.0, 4.0]], 'door_center': [6.5, 4.0], 'door_type': 'doorway', 'door_size': 1.2, 'wall_material_name': 'LowPolyInterior2_Wall2_C7_01', 'door_wall_size': {'x': 2.5, 'y': 3.0, 'z': 0.15000049769878387}, 'room': 'bedroom', 'movable': False, 'keep': True, 'bbox': [[5.9, 2.8], [5.9, 4.0], [7.1, 4.0], [7.1, 2.8]]}] 
    # room_bbox =  [(5.0, 0.0), (5.0, 4.0), (9.0, 4.0), (9.0, 0.0)]
    # move_polygons_many_times(floor_object_instances, room_bbox, plot=True)

    floor_object_instances = [{'prefab': 'LowPolyInterior2_Bed3_C2', 'position': [7.897189773619175, 0.5284510776400566, 2.0], 'rotation': [0, -90, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 1.6332573890686035, 'y': 0.8569017648696899, 'z': 2.055619955062866}, 'placeable_surfaces': [{'y': -0.018450677394866943, 'x_min': -0.7297730445861816, 'z_min': -0.27021315693855286, 'x_max': 0.2146390974521637, 'z_max': 0.9187247157096863}, {'y': -0.028450578451156616, 'x_min': -0.042927809059619904, 'z_min': -0.9187246561050415, 'x_max': 0.1287834793329239, 'z_max': -0.594468891620636}, {'y': -0.023940175771713257, 'x_min': -0.7297730445861816, 'z_min': -0.27021315693855286, 'x_max': 0.7297731041908264, 'z_max': 0.7025541663169861}], 'bbox': [[6.869379796087742, 1.1833713054656982], [6.869379796087742, 2.8166286945343018], [8.924999751150608, 2.8166286945343018], [8.924999751150608, 1.1833713054656982]], 'id': 'Bed0', 'room_id': 'bedroom', 'movable': True, 'keep': True}, {'prefab': 'LowPolyInterior2_Wardrobe7_C3', 'position': [5.333955429494381, 1.5000013634562492, 0.7], 'rotation': [0, 90, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 0.9999998807907104, 'y': 2.800002336502075, 'z': 0.517910361289978}, 'placeable_surfaces': [{'y': 1.4000011682510376, 'x_min': -0.4989999532699585, 'z_min': -0.2579551637172699, 'x_max': 0.4989999532699585, 'z_max': 0.2579551935195923}], 'bbox': [[5.075000248849392, 0.20000005960464473], [5.075000248849392, 1.1999999403953552], [5.59291061013937, 1.1999999403953552], [5.59291061013937, 0.20000005960464473]], 'id': 'Wardrobe0', 'room_id': 'bedroom', 'movable': False, 'keep': False}, {'prefab': 'LowPolyInterior2_Dresser3_C1', 'position': [5.275000311434269, 0.5614199861884117, 3.3], 'rotation': [0, 90, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 0.8999999761581421, 'y': 0.9228395819664001, 'z': 0.40000012516975403}, 'placeable_surfaces': [{'y': 0.4614197909832001, 'x_min': -0.4490000009536743, 'z_min': -0.1990000605583191, 'x_max': 0.4490000009536743, 'z_max': 0.1990000605583191}], 'bbox': [[5.075000248849392, 2.8500000119209288], [5.075000248849392, 3.749999988079071], [5.475000374019146, 3.749999988079071], [5.475000374019146, 2.8500000119209288]], 'id': 'Dresser0', 'room_id': 'bedroom', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior_OfficeTable_02', 'position': [7.0, 0.497969888150692, 0.46793409436941147], 'rotation': [0, 0, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 1.6116658449172974, 'y': 0.7959393858909607, 'z': 0.7858676910400391}, 'placeable_surfaces': [{'y': 0.39796963334083557, 'x_min': -0.804832935333252, 'z_min': -0.3919338583946228, 'x_max': 0.804832935333252, 'z_max': 0.3919338583946228}], 'bbox': [[6.194167077541351, 0.07500024884939194], [6.194167077541351, 0.860867939889431], [7.805832922458649, 0.860867939889431], [7.805832922458649, 0.07500024884939194]], 'id': 'OfficeTable0', 'room_id': 'bedroom', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior_OfficeChair_02', 'position': [7.0, 0.497969888150692, 0.46793409436941147], 'rotation': [0, 0, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 0.6433289647102356, 'y': 1.0644549131393433, 'z': 0.6426515579223633}, 'placeable_surfaces': [{'y': -0.007408201694488525, 'x_min': -0.20405921339988708, 'z_min': -0.14560261368751526, 'x_max': 0.20405921339988708, 'z_max': 0.2620847821235657}], 'bbox': [[6.678335517644882, 0.14660831540822983], [6.678335517644882, 0.7892598733305931], [7.321664482355118, 0.7892598733305931], [7.321664482355118, 0.14660831540822983]], 'id': 'OfficeChair0', 'room_id': 'bedroom', 'movable': True, 'keep': False}, {'prefab': 'LowPolyInterior2_AirConditioner_01', 'position': [8.5, 0.2595737800002098, 3.8175352290272713], 'rotation': [0, 180, 0], 'scale': [1, 1, 1], 'type': 'kinematic', 'size': {'x': 0.8999999761581421, 'y': 0.31914716958999634, 'z': 0.21492904424667358}, 'placeable_surfaces': [], 'bbox': [[8.050000011920929, 3.7100707069039345], [8.050000011920929, 3.924999751150608], [8.949999988079071, 3.924999751150608], [8.949999988079071, 3.7100707069039345]], 'id': 'AirConditioner0', 'room_id': 'bedroom', 'movable': True, 'keep': False}, {'door_wall_vertices': [[5.0, 0.0], [5.0, 4.0]], 'door_center': [5.0, 2.0], 'door_type': 'doorway', 'door_size': 1.2, 'wall_material_name': 'LowPolyInterior2_Wall1_C8_01', 'door_wall_size': {'x': 2.5, 'y': 3.0, 'z': 0.15000049769878387}, 'room': 'bedroom', 'movable': False, 'keep': True, 'bbox': [[5.0, 1.4], [5.0, 2.6], [6.2, 2.6], [6.2, 1.4]]}, {'door_wall_vertices': [[5.0, 4.0], [8.0, 4.0]], 'door_center': [6.5, 4.0], 'door_type': 'open', 'door_size': 3.0, 'room': 'bedroom', 'movable': False, 'keep': True, 'bbox': [[5.9, 2.8], [5.9, 4.0], [7.1, 4.0], [7.1, 2.8]]}] 
 
    room_bbox = [(5.0, 0.0), (5.0, 4.0), (9.0, 4.0), (9.0, 0.0)]
    move_polygons_many_times(floor_object_instances, room_bbox, plot=True)