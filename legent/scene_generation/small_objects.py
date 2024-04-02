import copy
import json
import random
from collections import defaultdict
from typing import Dict, List

import numpy as np

from legent.scene_generation.objects import ObjectDB
from legent.scene_generation.room import Room
from legent.server.rect_placer import RectPlacer
from legent.utils.io import log

MAX_OBJECT_NUM_ON_RECEPTACLE = 3

MAX_PLACE_ON_SURFACE_RETRIES = 10

SMALL_OBJECT_MIN_MARGIN = 0.1


def prefab_fit_surface(prefab_size, surface, receptacle):
    px, py, pz = prefab_size.values()
    sx = surface["surface"]["x_max"] - surface["surface"]["x_min"]
    sz = surface["surface"]["z_max"] - surface["surface"]["z_min"]
    if (
        receptacle["receptacle"]["rotation"][1] != 0
        and receptacle["receptacle"]["rotation"][1] != 180
    ):
        sx, sz = sz, sx
    total_num = receptacle["small_object_num"]
    if px < (sx * 0.9) and pz < (sz * 0.9) and total_num < MAX_OBJECT_NUM_ON_RECEPTACLE:
        return True
    return False


def add_small_objects(
    objects: List[Dict[str, any]],
    odb: ObjectDB,
    rooms: Dict[int, Room],
    max_object_types_per_room: int = 10000,
    placer_bbox=(0, 0, 0, 0),
    object_counts: Dict[str, int] = {},
    specified_object_instances: Dict[str, int] = {},
    receptacle_object_counts: Dict[str, int] = {},
):

    small_objects = []
    placer = RectPlacer(placer_bbox)

    objects_per_room = defaultdict(list)
    for obj in objects:
        room_id = obj["room_id"]
        objects_per_room[room_id].append(obj)
    objects_per_room = dict(objects_per_room)
    receptacles_per_room = {
        room_id: [
            obj
            for obj in objects
            if odb.OBJECT_TO_TYPE[obj["prefab"]] in odb.RECEPTACLES
            and obj["is_receptacle"]
        ]
        for room_id, objects in objects_per_room.items()
    }

    log(f"receptacle_object_counts: {receptacle_object_counts}")
    specified_small_object_types = set()
    failed_objects = {}
    if receptacle_object_counts:

        # add specified_small_object_types
        for k, v in receptacle_object_counts.items():
            for objects in v["objects"]:
                for kk, vv in objects.items():
                    specified_small_object_types.add(kk.lower())
        failed_objects = {k: [] for k in receptacle_object_counts}

        # If receptacle_object_counts is specified, we will first place the objects in receptacle_object_counts
        for k, v in receptacle_object_counts.items():
            to_place_recptacles = [
                obj for obj in specified_object_instances if obj["receptacle_type"] == k
            ]

            for i in range(len(v["objects"])):
                if i >= len(to_place_recptacles):
                    break
                receptacle = to_place_recptacles[i]
                objects = v["objects"][i]

                receptacle = {"receptacle": receptacle, "small_object_num": 0}

                failed_object_dict = {}

                surfaces = odb.PREFABS[receptacle["receptacle"]["prefab"]][
                    "placeable_surfaces"
                ]
                for kk, vv in objects.items():
                    kk = kk.lower()

                    failed_object_dict[kk] = 0

                    log(
                        f'placing kk: {kk} {vv} times on receptacle {receptacle["receptacle"]["prefab"]}'
                    )
                    for _ in range(vv):
                        prefab_name = random.choice(odb.OBJECT_DICT[kk])
                        prefab = odb.PREFABS[prefab_name]
                        prefab_size = prefab["size"]
                        random.shuffle(surfaces)
                        success_flag = False
                        for surface in surfaces:
                            surface = {"surface": surface, "small_object_num": 0}
                            if prefab_fit_surface(prefab_size, surface, receptacle):
                                small_object = {}
                                small_object["prefab"] = prefab_name

                                x_min = (
                                    (
                                        surface["surface"]["x_min"]
                                        + receptacle["receptacle"]["position"][0]
                                    )
                                    if receptacle["receptacle"]["rotation"][1] == 0
                                    or receptacle["receptacle"]["rotation"][1] == 180
                                    else (
                                        surface["surface"]["z_min"]
                                        + receptacle["receptacle"]["position"][0]
                                    )
                                )
                                x_max = (
                                    (
                                        surface["surface"]["x_max"]
                                        + receptacle["receptacle"]["position"][0]
                                    )
                                    if receptacle["receptacle"]["rotation"][1] == 0
                                    or receptacle["receptacle"]["rotation"][1] == 180
                                    else (
                                        surface["surface"]["z_max"]
                                        + receptacle["receptacle"]["position"][0]
                                    )
                                )
                                z_min = (
                                    (
                                        surface["surface"]["z_min"]
                                        + receptacle["receptacle"]["position"][2]
                                    )
                                    if receptacle["receptacle"]["rotation"][1] == 0
                                    or receptacle["receptacle"]["rotation"][1] == 180
                                    else (
                                        surface["surface"]["x_min"]
                                        + receptacle["receptacle"]["position"][2]
                                    )
                                )
                                z_max = (
                                    (
                                        surface["surface"]["z_max"]
                                        + receptacle["receptacle"]["position"][2]
                                    )
                                    if receptacle["receptacle"]["rotation"][1] == 0
                                    or receptacle["receptacle"]["rotation"][1] == 180
                                    else (
                                        surface["surface"]["x_max"]
                                        + receptacle["receptacle"]["position"][2]
                                    )
                                )

                                x_margin = (
                                    prefab_size["x"] / 2 + SMALL_OBJECT_MIN_MARGIN
                                )

                                z_margin = (
                                    prefab_size["z"] / 2 + SMALL_OBJECT_MIN_MARGIN
                                )

                                sample_x_min = x_min + x_margin
                                sample_x_max = x_max - x_margin
                                sample_z_min = z_min + z_margin
                                sample_z_max = z_max - z_margin

                                for _ in range(MAX_PLACE_ON_SURFACE_RETRIES):
                                    x, z = np.random.uniform(
                                        sample_x_min, sample_x_max
                                    ), np.random.uniform(sample_z_min, sample_z_max)

                                    if placer.place(
                                        k,
                                        x,
                                        z,
                                        prefab["size"]["x"]
                                        + 2 * SMALL_OBJECT_MIN_MARGIN,
                                        prefab["size"]["z"]
                                        + 2 * SMALL_OBJECT_MIN_MARGIN,
                                    ):
                                        y = (
                                            receptacle["receptacle"]["position"][1]
                                            + surface["surface"]["y"]
                                            + prefab_size["y"] / 2
                                        )

                                        small_object["position"] = (x, y, z)
                                        small_object["type"] = "interactable"
                                        small_object["parent"] = receptacle[
                                            "receptacle"
                                        ]["prefab"]
                                        small_object["scale"] = [1, 1, 1]
                                        small_object["rotation"] = [0, 0, 0]
                                        small_objects.append(small_object)
                                        surface["small_object_num"] += 1
                                        receptacle["small_object_num"] += 1
                                        success_flag = True
                                        break
                                if success_flag:
                                    log(
                                        f"Small Object {kk} on {receptacle['receptacle']['prefab']}, position:{format(small_object['position'][0],'.4f')},{format(small_object['position'][2],'.4f')}",
                                    )
                                    break
                        if not success_flag:
                            failed_object_dict[kk] += 1
                failed_objects[k].append(failed_object_dict)

    with open("failed_objects.json", "w") as f:
        json.dump(failed_objects, f, indent=4, ensure_ascii=False)

    object_types_in_rooms = {
        room_id: set(odb.OBJECT_TO_TYPE[obj["prefab"]] for obj in objects)
        for room_id, objects in objects_per_room.items()
    }

    receptacle_index = 0
    receptacle_dict = {}

    for room_id, room in rooms.items():
        if room_id not in receptacles_per_room:
            continue
        receptacles_in_room = receptacles_per_room[room_id]
        room_type = room.room_type
        spawnable_objects = []
        for receptacle in receptacles_in_room:

            receptacle_index += 1
            objects_in_receptacle = odb.RECEPTACLES[
                odb.OBJECT_TO_TYPE[receptacle["prefab"]]
            ]
            placeable_surfaces = odb.PREFABS[receptacle["prefab"]]["placeable_surfaces"]
            if not placeable_surfaces:
                continue

            receptacle_dict[receptacle_index] = {
                "receptacle": receptacle,
                "surfaces": [],
                "small_object_num": 0,
            }
            for surface in placeable_surfaces:

                receptacle_dict[receptacle_index]["surfaces"].append(
                    {
                        "surface": surface,
                        "small_object_num": 0,
                    }
                )

            for object_type, p in objects_in_receptacle.items():
                if object_type in specified_small_object_types:
                    continue
                if p < 1:
                    continue
                room_weight = odb.PLACEMENT_ANNOTATIONS.loc[object_type][
                    f"in{room_type}s"
                ]
                if room_weight == 0:
                    continue
                spawnable_objects.append(
                    {
                        "receptacleIndex": receptacle_index,
                        "receptacleId": receptacle["prefab"],
                        "receptacleType": odb.OBJECT_TO_TYPE[receptacle["prefab"]],
                        "receptacle": receptacle,
                        "childObjectType": object_type,
                        "childRoomWeight": room_weight,
                    }
                )

        spawnable_groups = spawnable_objects
        random.shuffle(spawnable_groups)
        objects_types_placed_in_room = set()

        for group in spawnable_groups:
            if len(objects_types_placed_in_room) >= max_object_types_per_room:
                break
            # NOTE: Check if there can be multiple of the same type in the room.
            if (
                group["childObjectType"] in object_types_in_rooms[room_id]
                and not odb.PLACEMENT_ANNOTATIONS.loc[group["childObjectType"]][
                    "multiplePerRoom"
                ]
            ):
                break

            asset_candidates = odb.OBJECT_DICT[group["childObjectType"]]

            chosen_asset_id = random.choice(asset_candidates)

            prefab = odb.PREFABS[chosen_asset_id]

            receptacle = receptacle_dict[group["receptacleIndex"]]
            surfaces = receptacle["surfaces"]

            success_flag = False
            for surface in surfaces:
                if prefab_fit_surface(prefab["size"], surface, receptacle):
                    small_object = copy.deepcopy(group["receptacle"])
                    small_object["prefab"] = chosen_asset_id

                    x_min = (
                        (
                            surface["surface"]["x_min"]
                            + receptacle["receptacle"]["position"][0]
                        )
                        if receptacle["receptacle"]["rotation"][1] == 0
                        or receptacle["receptacle"]["rotation"][1] == 180
                        else (
                            surface["surface"]["z_min"]
                            + receptacle["receptacle"]["position"][0]
                        )
                    )
                    x_max = (
                        (
                            surface["surface"]["x_max"]
                            + receptacle["receptacle"]["position"][0]
                        )
                        if receptacle["receptacle"]["rotation"][1] == 0
                        or receptacle["receptacle"]["rotation"][1] == 180
                        else (
                            surface["surface"]["z_max"]
                            + receptacle["receptacle"]["position"][0]
                        )
                    )
                    z_min = (
                        (
                            surface["surface"]["z_min"]
                            + receptacle["receptacle"]["position"][2]
                        )
                        if receptacle["receptacle"]["rotation"][1] == 0
                        or receptacle["receptacle"]["rotation"][1] == 180
                        else (
                            surface["surface"]["x_min"]
                            + receptacle["receptacle"]["position"][2]
                        )
                    )
                    z_max = (
                        (
                            surface["surface"]["z_max"]
                            + receptacle["receptacle"]["position"][2]
                        )
                        if receptacle["receptacle"]["rotation"][1] == 0
                        or receptacle["receptacle"]["rotation"][1] == 180
                        else (
                            surface["surface"]["x_max"]
                            + receptacle["receptacle"]["position"][2]
                        )
                    )

                    x_margin = prefab["size"]["x"] / 2 + SMALL_OBJECT_MIN_MARGIN

                    z_margin = prefab["size"]["z"] / 2 + SMALL_OBJECT_MIN_MARGIN

                    sample_x_min = x_min + x_margin
                    sample_x_max = x_max - x_margin
                    sample_z_min = z_min + z_margin
                    sample_z_max = z_max - z_margin

                    for _ in range(MAX_PLACE_ON_SURFACE_RETRIES):
                        x, z = np.random.uniform(
                            sample_x_min, sample_x_max
                        ), np.random.uniform(sample_z_min, sample_z_max)

                        if placer.place(
                            chosen_asset_id,
                            x,
                            z,
                            prefab["size"]["x"] + 2 * SMALL_OBJECT_MIN_MARGIN,
                            prefab["size"]["z"] + 2 * SMALL_OBJECT_MIN_MARGIN,
                        ):
                            y = (
                                receptacle["receptacle"]["position"][1]
                                + surface["surface"]["y"]
                                + odb.PREFABS[chosen_asset_id]["size"]["y"] / 2
                            )

                            small_object["position"] = (x, y, z)
                            small_object["type"] = "interactable"
                            small_objects.append(small_object)
                            surface["small_object_num"] += 1
                            receptacle["small_object_num"] += 1
                            success_flag = True
                            break
                    if success_flag:
                        log(
                            f"Small Object {chosen_asset_id} on {receptacle['receptacle']['prefab']}, position:{format(small_object['position'][0],'.4f')},{format(small_object['position'][2],'.4f')}",
                        )
                        break

    return small_objects
