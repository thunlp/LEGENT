import copy
import json
import random
from collections import defaultdict
from typing import Dict, List, Literal, Optional, Sequence, Set, Tuple, Union

import numpy as np
import pandas as pd
from attrs import define
from shapely.geometry import Polygon

from legent.scene_generation.doors import default_add_doors
from legent.scene_generation.house import generate_house_structure
from legent.scene_generation.objects import ObjectDB
from legent.scene_generation.room import OrthogonalPolygon, Room
from legent.scene_generation.room_spec import RoomSpec
from legent.scene_generation.small_objects import add_small_objects
from legent.server.rect_placer import RectPlacer
def log(*args, **kwargs):
    pass
from legent.utils.math import look_rotation

from .asset_groups import Asset, AssetGroup
from .constants import (
    MARGIN,
    MAX_INTERSECTING_OBJECT_RETRIES,
    MIN_RECTANGLE_SIDE_SIZE,
    OPENNESS_RANDOMIZATIONS,
    P_CHOOSE_ASSET_GROUP,
    P_CHOOSE_EDGE,
    P_LARGEST_RECTANGLE,
    P_W1_ASSET_SKIPPED,
    PADDING_AGAINST_WALL,
)
from .floorplan import generate_floorplan
from .house import HouseStructure
from .interior_boundaries import sample_interior_boundary
from .types import Vector3

MAX = 7
UNIT_SIZE = 2.5  # The size of a unit in the grid
HALF_UNIT_SIZE = UNIT_SIZE / 2  # Half of the size of a unit in the grid
DEFAULT_FLOOR_PREFAB = "LowPolyInterior_Floor_01"
DEFAULT_WALL_PREFAB = "LowPolyInterior_WallFloor1_09"
MAX_SPECIFIED_RECTANGLE_RETRIES = 10
MAX_SPECIFIED_NUMBER = 20
WALL_THICKNESS = 0.075


class HouseGenerator:
    def __init__(
        self,
        room_spec: Optional[Union[RoomSpec, str]] = None,
        dims: Optional[Tuple[int, int]] = None,
        objectDB: ObjectDB = None,
    ) -> None:
        self.room_spec = room_spec
        self.dims = dims
        self.odb = objectDB
        self.rooms: Dict[str, Room] = dict()

    def generate_structure(self, room_spec):
        house_structure = generate_house_structure(room_spec=room_spec, dims=self.dims)
        return house_structure

    def format_object(self, prefab, position, rotation, scale):

        object = {
            "prefab": prefab,
            "position": [position[0], position[1], position[2]],
            "rotation": [0, rotation, 0],
            "scale": scale,
            "type": "kinematic",
        }
        return object

    def align_wall_height_scale(self, wall_prefab):
        wall_y_size = self.odb.PREFABS[wall_prefab]["size"]["y"]
        scale = 3 / wall_y_size
        return scale

    def add_floors_and_walls(self, house_structure, room_spec, odb, prefabs):
        room_num = len(room_spec.room_type_map)
        room_ids = set(room_spec.room_type_map.keys())
        room2wall = {i: np.random.choice(odb.MY_OBJECTS["wall"][:]) for i in room_ids}
        # wall_with_door_prefab = odb.MY_OBJECTS["wall_with_door"][0]
        DOOR_PREFAB = odb.MY_OBJECTS["door"][0]
        door_x_size = prefabs[DOOR_PREFAB]["size"]["x"]
        door_y_size = prefabs[DOOR_PREFAB]["size"]["y"]
        door_z_size = prefabs[DOOR_PREFAB]["size"]["z"]
        log(
            f"door_x_size: {door_x_size}, door_y_size: {door_y_size}, door_z_size: {door_z_size}"
        )

        WALL_PREFAB = room2wall[random.choice(list(room2wall.keys()))]
        wall_x_size, wall_y_size, wall_z_size = (
            prefabs[WALL_PREFAB]["size"]["x"],
            prefabs[WALL_PREFAB]["size"]["y"],
            prefabs[WALL_PREFAB]["size"]["z"],
        )
        log(
            f"wall_x_size: {wall_x_size}, wall_y_size: {wall_y_size}, wall_z_size: {wall_z_size}"
        )
        room2wall.update({0: DEFAULT_WALL_PREFAB})
        room2floor = {i: np.random.choice(odb.MY_OBJECTS["floor"]) for i in room_ids}
        FLOOR_PREFAB = room2floor[random.choice(list(room2floor.keys()))]
        floor_x_size, floor_y_size, floor_z_size = (
            prefabs[FLOOR_PREFAB]["size"]["x"],
            prefabs[FLOOR_PREFAB]["size"]["y"],
            prefabs[FLOOR_PREFAB]["size"]["z"],
        )
        log(
            f"floor_x_size: {floor_x_size}, floor_y_size: {floor_y_size}, floor_z_size: {floor_z_size}"
        )
        floors = house_structure.floorplan
        # convert 1 in floors to 0
        floors = np.where(floors == 1, 0, floors)
        log(f"floors:\n{floors}")

        doors = default_add_doors(odb, room_spec, house_structure)
        log(f"doors: {doors}")
        door_positions = set(doors.values())
        # exit()

        floor_instances = []
        # generate walls based on the 0-1 boundaries
        for i in range(floors.shape[0]):
            for j in range(floors.shape[1]):
                if floors[i][j] != 0:
                    FLOOR_PREFAB = room2floor[floors[i][j]]

                    x, z = (i + 0.5 - 1) * UNIT_SIZE, (j + 0.5 - 1) * UNIT_SIZE
                    floor_instances.append(
                        {
                            "prefab": FLOOR_PREFAB,
                            "position": [x, -floor_y_size / 2, z],
                            "rotation": [0, 90, 0],
                            "scale": [1, 1, 1],
                            "type": "kinematic",
                        }
                    )

                WALL_PREFAB = room2wall[floors[i][j]]
                wall_x_size, wall_y_size, wall_z_size = (
                    prefabs[WALL_PREFAB]["size"]["x"],
                    prefabs[WALL_PREFAB]["size"]["y"],
                    prefabs[WALL_PREFAB]["size"]["z"],
                )

                WALL_WITH_DOOR_PREFAB = WALL_PREFAB[:-1] + "2"

                a = floors[i][j]
                if i < floors.shape[0] - 1:
                    a_col = floors[i + 1][j]

                    # x轴相邻的格子

                    if a != a_col:
                        x = i + 1 - 1
                        z = j + 0.5 - 1
                        y_rot = 90

                        x = x * UNIT_SIZE
                        z = z * UNIT_SIZE

                        left_x = x - wall_z_size / 4
                        right_x = x + wall_z_size / 4

                        left_wall_prefab = room2wall[floors[i][j]]
                        right_wall_prefab = room2wall[floors[i + 1][j]]

                        scale = [1, 1, 0.5]
                        left_scale = [
                            1,
                            self.align_wall_height_scale(left_wall_prefab),
                            0.5,
                        ]
                        right_scale = [
                            1,
                            self.align_wall_height_scale(right_wall_prefab),
                            0.5,
                        ]

                        left_wall_with_door_prefab = left_wall_prefab[:-1] + "2"
                        right_wall_with_door_prefab = right_wall_prefab[:-1] + "2"

                        left_rotation = 270
                        right_rotation = 90
                        door_rotation = 270

                        door = None
                        if ((i, j), (i + 1, j)) in door_positions:
                            left_wall = self.format_object(
                                left_wall_with_door_prefab,
                                (left_x, 1.5, z),
                                left_rotation,
                                left_scale,
                            )
                            right_wall = self.format_object(
                                right_wall_with_door_prefab,
                                (right_x, 1.5, z),
                                right_rotation,
                                right_scale,
                            )
                            door = self.format_object(
                                DOOR_PREFAB,
                                (x, door_y_size / 2, z),
                                door_rotation,
                                scale,
                            )
                        else:
                            left_wall = self.format_object(
                                left_wall_prefab,
                                (left_x, 1.5, z),
                                left_rotation,
                                left_scale,
                            )
                            right_wall = self.format_object(
                                right_wall_prefab,
                                (right_x, 1.5, z),
                                right_rotation,
                                right_scale,
                            )

                        if floors[i][j] != 0:
                            floor_instances.append(left_wall)
                        if floors[i + 1][j] != 0:
                            floor_instances.append(right_wall)
                        if door:
                            floor_instances.append(door)
                            door_size = prefabs[DOOR_PREFAB]["size"]
                            door_bbox = (
                                x - door_size["x"] / 2 - 1.0,
                                z - door_size["z"] / 2 - 0.3,
                                x + door_size["x"] / 2 + 1.2,  # 1.2 is length of door
                                z + door_size["z"] / 2 + 0.3,
                            )
                            self.placer.insert(DOOR_PREFAB, door_bbox)

                if j < floors.shape[1] - 1:
                    a_row = floors[i][j + 1]
                    if a != a_row:
                        x = i + 0.5 - 1
                        z = j + 1 - 1
                        y_rot = 0

                        x = x * UNIT_SIZE
                        z = z * UNIT_SIZE

                        up_z = z - wall_z_size / 4
                        down_z = z + wall_z_size / 4

                        up_wall_prefab = room2wall[floors[i][j]]
                        down_wall_prefab = room2wall[floors[i][j + 1]]

                        scale = [1, 1, 0.5]
                        up_scale = [
                            1,
                            self.align_wall_height_scale(up_wall_prefab),
                            0.5,
                        ]
                        down_scale = [
                            1,
                            self.align_wall_height_scale(down_wall_prefab),
                            0.5,
                        ]

                        up_wall_with_door_prefab = up_wall_prefab[:-1] + "2"
                        down_wall_with_door_prefab = down_wall_prefab[:-1] + "2"

                        door = None

                        up_rotation = 180
                        down_rotation = 0
                        door_rotation = 180

                        if ((i, j), (i, j + 1)) in door_positions:
                            up_wall = self.format_object(
                                up_wall_with_door_prefab,
                                (x, 1.5, up_z),
                                up_rotation,
                                up_scale,
                            )
                            down_wall = self.format_object(
                                down_wall_with_door_prefab,
                                (x, 1.5, down_z),
                                down_rotation,
                                down_scale,
                            )
                            door = self.format_object(
                                DOOR_PREFAB,
                                (x, door_y_size / 2, z),
                                door_rotation,
                                scale,
                            )
                        else:
                            up_wall = self.format_object(
                                up_wall_prefab,
                                (x, 1.5, up_z),
                                up_rotation,
                                up_scale,
                            )
                            down_wall = self.format_object(
                                down_wall_prefab,
                                (x, 1.5, down_z),
                                down_rotation,
                                down_scale,
                            )
                        if floors[i][j] != 0:
                            floor_instances.append(up_wall)
                        if floors[i][j + 1] != 0:
                            floor_instances.append(down_wall)
                        if door:
                            floor_instances.append(door)
                            door_size = prefabs[DOOR_PREFAB]["size"]
                            door_bbox = (
                                x - door_size["x"] / 2 - 0.3,
                                z - door_size["z"] / 2 - 1.0,
                                x + door_size["x"] / 2 + 1.2,
                                z + door_size["z"] / 2 + 0.3,
                            )
                            self.placer.insert(DOOR_PREFAB, door_bbox)

        return floor_instances, floors

    def add_human_and_agent(self, floors):
        # log(floors)
        def get_bbox_of_floor(x, z):
            x, z = (x - 0.5) * UNIT_SIZE, (z - 0.5) * UNIT_SIZE
            return (
                x - HALF_UNIT_SIZE,
                z - HALF_UNIT_SIZE,
                x + HALF_UNIT_SIZE,
                z + HALF_UNIT_SIZE,
            )

        def random_xz_for_agent(
            eps, floors
        ):  # To prevent being positioned in the wall and getting pushed out by collision detection.
            # ravel the floor
            ravel_floors = floors.ravel()
            # get the index of the floor
            floor_idx = np.where(ravel_floors != 0)[0]
            # sample from the floor index
            floor_idx = np.random.choice(floor_idx)
            # get the x and z index
            x, z = np.unravel_index(floor_idx, floors.shape)
            log(f"human/agent x: {x}, z: {z}")

            # debug:
            # x,z = (x-0.5)*UNIT_SIZE, (z-0.5)*UNIT_SIZE
            # return x,z

            # get the bbox of the floor
            bbox = get_bbox_of_floor(x, z)
            # uniformly sample from the bbox, with eps
            x, z = np.random.uniform(bbox[0] + eps, bbox[2] - eps), np.random.uniform(
                bbox[1] + eps, bbox[3] - eps
            )
            return x, z

        ### STEP 3: Randomly place the player and playmate (AI agent)
        # place the player
        while True:
            x, z = random_xz_for_agent(eps=0.5, floors=floors)
            x_size, z_size = 0.3, 0.3
            # TODO: obtain the precise centerOffset of the character. calculate y based on it.
            player = {
                "prefab": "",
                "position": [x, 0.05, z],
                "rotation": [0, np.random.uniform(0, 360), 0],
                "scale": [1, 1, 1],
                "parent": -1,
                "type": "",
            }
            ok = self.placer.place("playmate", x, z, x_size, z_size)

            if ok:
                log(f"player x: {x}, z: {z}")
                break
            #     self.placer.visualize(
            #         x - x_size / 2,
            #         z - z_size / 2,
            #         x + x_size / 2,
            #         z + z_size / 2,
            #         c="y",
            #     )
        # place the playmate
        while True:
            x, z = random_xz_for_agent(eps=0.5, floors=floors)
            x_size, z_size = 0.3, 0.3
            playmate = {
                "prefab": "",
                "position": [x, 0.05, z],
                "rotation": [0, np.random.uniform(0, 360), 0],
                "scale": [1, 1, 1],
                "parent": -1,
                "type": "",
            }
            ok = self.placer.place("playmate", x, z, x_size, z_size)
            if ok:
                log(f"playmate x: {x}, z: {z}")
                # self.placer.visualize(
                #     x - x_size / 2,
                #     z - z_size / 2,
                #     x + x_size / 2,
                #     z + z_size / 2,
                #     c="y",
                # )
                break

        # player lookat the playmate
        vs, vt = np.array(player["position"]), np.array(playmate["position"])
        vr = look_rotation(vt - vs)
        player["rotation"] = [0, vr[1], 0]

        return player, playmate

    def get_floor_polygons(self, xz_poly_map: dict) -> Dict[str, Polygon]:
        """Return a shapely Polygon for each floor in the room."""
        floor_polygons = dict()
        for room_id, xz_poly in xz_poly_map.items():
            floor_polygon = []
            for (x0, z0), (x1, z1) in xz_poly:
                floor_polygon.append((x0, z0))
            floor_polygon.append((x1, z1))
            floor_polygons[f"room|{room_id}"] = Polygon(floor_polygon)
        return floor_polygons

    def get_rooms(self, room_type_map, floor_polygons):
        for room_id, room_type in room_type_map.items():
            polygon = floor_polygons[f"room|{room_id}"]
            room = Room(
                polygon=polygon,
                room_type=room_type,
                room_id=room_id,
                odb=self.odb,
            )
            self.rooms[room_id] = room

    def sample_and_add_floor_asset(
        self,
        room: Room,
        rectangle: Tuple[float, float, float, float],
        anchor_type: str,
        anchor_delta: int,
        odb: ObjectDB,
        spawnable_assets: pd.DataFrame,
        spawnable_asset_groups: pd.DataFrame,
        priority_asset_types: List[str],
    ):
        set_rotated = None

        # NOTE: Choose the valid rotations
        x0, z0, x1, z1 = rectangle
        rect_x_length = x1 - x0
        rect_z_length = z1 - z0

        # NOTE: add margin to each object.
        # NOTE: z is the forward direction on each object.
        # Therefore, we only add space in front of the object.
        if anchor_type == "onEdge":
            x_margin = 2 * MARGIN["edge"]["sides"]
            z_margin = (
                MARGIN["edge"]["front"] + MARGIN["edge"]["back"] + PADDING_AGAINST_WALL
            )
        elif anchor_type == "inCorner":
            x_margin = 2 * MARGIN["corner"]["sides"] + PADDING_AGAINST_WALL
            z_margin = (
                MARGIN["corner"]["front"]
                + MARGIN["corner"]["back"]
                + PADDING_AGAINST_WALL
            )
        elif anchor_type == "inMiddle":
            # NOTE: add space to both sides
            x_margin = 2 * MARGIN["middle"]
            z_margin = 2 * MARGIN["middle"]

        # NOTE: define the size filters
        if anchor_delta in {1, 7}:
            # NOTE: should not be rotated
            size_filter = lambda assets_df: (
                (assets_df["xSize"] + x_margin < rect_x_length)
                & (assets_df["zSize"] + z_margin < rect_z_length)
            )
            set_rotated = False
        elif anchor_delta in {3, 5}:
            # NOTE: must be rotated
            size_filter = lambda assets_df: (
                (assets_df["zSize"] + z_margin < rect_x_length)
                & (assets_df["xSize"] + x_margin < rect_z_length)
            )
            set_rotated = True
        else:
            # NOTE: either rotated or not rotated works
            size_filter = lambda assets_df: (
                (
                    (assets_df["xSize"] + x_margin < rect_x_length)
                    & (assets_df["zSize"] + z_margin < rect_z_length)
                )
                | (
                    (assets_df["zSize"] + z_margin < rect_x_length)
                    & (assets_df["xSize"] + x_margin < rect_z_length)
                )
            )

        # log(f"spawnable_asset_groups: {spawnable_asset_groups}")
        # log(f"anchor type: {anchor_type}")
        asset_group_candidates = spawnable_asset_groups[
            spawnable_asset_groups[anchor_type] & size_filter(spawnable_asset_groups)
        ]
        # log(f"asset_group_candidates: {asset_group_candidates}")
        asset_candidates = spawnable_assets[
            spawnable_assets[anchor_type] & size_filter(spawnable_assets)
        ]
        # log(f"asset_candidates: {asset_candidates}")

        if priority_asset_types:
            for asset_type in priority_asset_types:
                asset_type = asset_type.lower()
                # log(f"priority asset_type: {asset_type}")
                # NOTE: see if there are any semantic asset groups with the asset
                asset_groups_with_type = asset_group_candidates[
                    asset_group_candidates[f"has{asset_type}"]
                ]
                # log(f"asset groups with type: { asset_groups_with_type}")

                # NOTE: see if assets can spawn by themselves
                can_spawn_alone_assets = odb.PLACEMENT_ANNOTATIONS[
                    odb.PLACEMENT_ANNOTATIONS.index == asset_type
                ]
                # log(f"can_spawn_alone_assets: {can_spawn_alone_assets}")

                can_spawn_standalone = len(can_spawn_alone_assets) and (
                    can_spawn_alone_assets[f"in{room.room_type}s"].iloc[0] > 0
                )
                # log(f"can_spawn_standalone: {can_spawn_standalone}")
                assets_with_type = None
                if can_spawn_standalone:
                    assets_with_type = asset_candidates[
                        asset_candidates["assetType"] == asset_type
                    ]
                    # log(f"assets_with_type: {assets_with_type}")

                # NOTE: try using an asset group first
                if len(asset_groups_with_type) and (
                    assets_with_type is None or random.random() <= P_CHOOSE_ASSET_GROUP
                ):
                    # NOTE: Try using an asset group
                    # log(f"use asset group!")
                    asset_group = asset_groups_with_type.sample()
                    chosen_asset_group = room.place_asset_group(
                        asset_group=asset_group,
                        set_rotated=set_rotated,
                        rect_x_length=rect_x_length,
                        rect_z_length=rect_z_length,
                    )
                    # log(f'chosen_asset_group: {chosen_asset_group}')
                    if chosen_asset_group is not None:
                        return chosen_asset_group

                # NOTE: try using a standalone asset
                if assets_with_type is not None and len(assets_with_type):
                    # NOTE: try spawning in standalone
                    asset = assets_with_type.sample()
                    return room.place_asset(
                        asset=asset,
                        set_rotated=set_rotated,
                        rect_x_length=rect_x_length,
                        rect_z_length=rect_z_length,
                    )
        # NOTE: try using an asset group
        can_use_asset_group = True
        must_use_asset_group = False

        if (
            len(asset_group_candidates)
            and random.random() <= P_CHOOSE_ASSET_GROUP
            and can_use_asset_group
        ) or (must_use_asset_group and len(asset_group_candidates)):

            # NOTE: use an asset group if you can
            asset_group = asset_group_candidates.sample()
            chosen_asset_group = room.place_asset_group(
                asset_group=asset_group,
                set_rotated=set_rotated,
                rect_x_length=rect_x_length,
                rect_z_length=rect_z_length,
            )
            if chosen_asset_group is not None:
                return chosen_asset_group
            return chosen_asset_group

        # NOTE: Skip weight 1 assets with a probability of P_W1_ASSET_SKIPPED
        if random.random() <= P_W1_ASSET_SKIPPED:
            asset_candidates = asset_candidates[
                asset_candidates[f"in{room.room_type}s"] != 1
            ]

        # NOTE: no assets fit the anchor_type and size criteria
        if not len(asset_candidates):
            return None

        # NOTE: this is a sampling by asset type
        asset_type = random.choice(asset_candidates["assetType"].unique())
        asset = asset_candidates[asset_candidates["assetType"] == asset_type].sample()
        return room.place_asset(
            asset=asset,
            set_rotated=set_rotated,
            rect_x_length=rect_x_length,
            rect_z_length=rect_z_length,
        )

    def get_spawnable_asset_group_info(self) -> pd.DataFrame:
        from .asset_groups import AssetGroupGenerator

        asset_groups = self.odb.ASSET_GROUPS

        data = []
        for asset_group_name, asset_group_data in asset_groups.items():
            asset_group_generator = AssetGroupGenerator(
                name=asset_group_name,
                data=asset_group_data,
                odb=self.odb,
            )

            dims = asset_group_generator.dimensions
            group_properties = asset_group_data["groupProperties"]

            # NOTE: This is kinda naive, since a single asset in the asset group
            # could map to multiple different types of asset types (e.g., Both Chair
            # and ArmChair could be in the same asset).
            # NOTE: use the asset_group_generator.data instead of asset_group_data
            # since it only includes assets from a given split.
            asset_types_in_group = set(
                asset_type
                for asset in asset_group_generator.data["assetMetadata"].values()
                for asset_type, asset_id in asset["assetIds"]
            )
            group_data = {
                "assetGroupName": asset_group_name,
                "assetGroupGenerator": asset_group_generator,
                "xSize": dims["x"],
                "ySize": dims["y"],
                "zSize": dims["z"],
                "inBathrooms": group_properties["roomWeights"]["bathrooms"],
                "inBedrooms": group_properties["roomWeights"]["bedrooms"],
                "inKitchens": group_properties["roomWeights"]["kitchens"],
                "inLivingRooms": group_properties["roomWeights"]["livingRooms"],
                "allowDuplicates": group_properties["properties"]["allowDuplicates"],
                "inCorner": group_properties["location"]["corner"],
                "onEdge": group_properties["location"]["edge"],
                "inMiddle": group_properties["location"]["middle"],
            }

            # NOTE: Add which types are in this asset group
            for asset_type in self.odb.OBJECT_DICT.keys():
                group_data[f"has{asset_type}"] = asset_type in asset_types_in_group

            data.append(group_data)

        return pd.DataFrame(data)

    def prefab_fit_rectangle(self, prefab_size, rectangle):
        x0, z0, x1, z1 = rectangle
        rect_x_length = x1 - x0
        rect_z_length = z1 - z0
        prefab_x_length = prefab_size["x"]
        prefab_z_length = prefab_size["z"]
        if (prefab_x_length < rect_x_length * 0.9) and (
            prefab_z_length < rect_z_length * 0.9
        ):
            return 0
        elif (prefab_x_length < rect_z_length * 0.9) and (
            prefab_z_length < rect_x_length * 0.9
        ):
            return 90
        else:
            return -1

    def generate(
        self,
        object_counts: Dict[str, int] = {},
        receptacle_object_counts: Dict[str, Dict[str, int]] = {},
    ):
        odb = self.odb
        prefabs = odb.PREFABS
        room_spec = self.room_spec

        log("starting...")

        house_structure = self.generate_structure(room_spec=room_spec)
        interior_boundary = house_structure.interior_boundary
        x_size = interior_boundary.shape[0]
        z_size = interior_boundary.shape[1]

        min_x, min_z, max_x, max_z = 0, 0, x_size * UNIT_SIZE, z_size * UNIT_SIZE
        self.placer = RectPlacer((min_x, min_z, max_x, max_z))

        floor_instances, floors = self.add_floors_and_walls(
            house_structure, room_spec, odb, prefabs
        )

        floor_polygons = self.get_floor_polygons(house_structure.xz_poly_map)

        self.get_rooms(
            room_type_map=room_spec.room_type_map, floor_polygons=floor_polygons
        )

        player, playmate = self.add_human_and_agent(floors)

        max_floor_objects = 15

        spawnable_asset_group_info = self.get_spawnable_asset_group_info()

        specified_object_instances = []
        specified_object_types = set()
        if receptacle_object_counts:
            # first place the specified receptacles
            for receptacle, d in receptacle_object_counts.items():
                receptacle_type = receptacle
                receptacle = random.choice(odb.OBJECT_DICT[receptacle.lower()])
                specified_object_types.add(odb.OBJECT_TO_TYPE[receptacle])
                count = d["count"]
                prefab_size = odb.PREFABS[receptacle]["size"]
                for _ in range(MAX_SPECIFIED_NUMBER):
                    success_flag = False
                    for room in self.rooms.values():
                        for _ in range(MAX_SPECIFIED_RECTANGLE_RETRIES):
                            rectangle = room.sample_next_rectangle()
                            minx, minz, maxx, maxz = rectangle
                            rect_x = maxx - minx
                            rect_z = maxz - minz
                            rotation = self.prefab_fit_rectangle(prefab_size, rectangle)

                            if rotation == -1:
                                continue
                            else:
                                x_size = (
                                    prefab_size["x"]
                                    if rotation == 0
                                    else prefab_size["z"]
                                )
                                z_size = (
                                    prefab_size["z"]
                                    if rotation == 0
                                    else prefab_size["x"]
                                )
                                minx += x_size / 2 + WALL_THICKNESS
                                minz += z_size / 2 + WALL_THICKNESS
                                maxx -= x_size / 2 + WALL_THICKNESS
                                maxz -= z_size / 2 + WALL_THICKNESS
                                x = np.random.uniform(minx, maxx)
                                z = np.random.uniform(minz, maxz)
                                bbox = (
                                    x - x_size / 2,
                                    z - z_size / 2,
                                    x + x_size / 2,
                                    z + z_size / 2,
                                )
                                if self.placer.place_rectangle(receptacle, bbox):
                                    specified_object_instances.append(
                                        {
                                            "prefab": receptacle,
                                            "position": [x, prefab_size["y"] / 2, z],
                                            "rotation": [0, rotation, 0],
                                            "scale": [1, 1, 1],
                                            "parent": -1,
                                            "type": "receptacle",
                                            "room_id": room.room_id,
                                            "is_receptacle": True,
                                            "receptacle_type": receptacle_type,
                                        }
                                    )
                                    log(
                                        f"Specified {receptacle} into position:{ format(x,'.4f')},{format(z,'.4f')}, bbox:{bbox} rotation:{rotation}"
                                    )
                                    success_flag = True
                                    count -= 1
                                    break
                        if success_flag:
                            break
                    if count == 0:
                        break

        object_instances = []
        for room in self.rooms.values():
            asset = None
            spawnable_asset_groups = spawnable_asset_group_info[
                spawnable_asset_group_info[f"in{room.room_type}s"] > 0
            ]

            floor_types, spawnable_assets = odb.FLOOR_ASSET_DICT[
                (room.room_type, room.split)
            ]

            priority_asset_types = copy.deepcopy(
                odb.PRIORITY_ASSET_TYPES.get(room.room_type, [])
            )
            for i in range(max_floor_objects):
                cache_rectangles = i != 0 and asset is None

                # log("sample rectangle")
                if cache_rectangles:
                    # NOTE: Don't resample failed rectangles
                    room.last_rectangles.remove(rectangle)
                    rectangle = room.sample_next_rectangle(cache_rectangles=True)
                else:
                    rectangle = room.sample_next_rectangle()

                # log(f"rectangle: {rectangle}")
                if rectangle is None:
                    break

                x_info, z_info, anchor_delta, anchor_type = room.sample_anchor_location(
                    rectangle
                )

                asset = self.sample_and_add_floor_asset(
                    room=room,
                    rectangle=rectangle,
                    anchor_type=anchor_type,
                    anchor_delta=anchor_delta,
                    spawnable_assets=spawnable_assets,
                    spawnable_asset_groups=spawnable_asset_groups,
                    priority_asset_types=priority_asset_types,
                    odb=odb,
                )
                # log(f'asset: {asset}')

                if asset is None:
                    continue
                room.sample_place_asset_in_rectangle(
                    asset=asset,
                    rectangle=rectangle,
                    anchor_type=anchor_type,
                    x_info=x_info,
                    z_info=z_info,
                    anchor_delta=anchor_delta,
                )

                # log("place ok!")

                added_asset_types = []
                if "assetType" in asset:
                    added_asset_types.append(asset["assetType"])
                else:
                    added_asset_types.extend([o["assetType"] for o in asset["objects"]])

                    if not asset["allowDuplicates"]:
                        spawnable_asset_groups = spawnable_asset_groups.query(
                            f"assetGroupName!='{asset['assetGroupName']}'"
                        )

                for asset_type in added_asset_types:
                    # Remove spawned object types from `priority_asset_types` when appropriate
                    if asset_type in priority_asset_types:
                        priority_asset_types.remove(asset_type)

                    allow_duplicates_of_asset_type = odb.PLACEMENT_ANNOTATIONS.loc[
                        asset_type.lower()
                    ]["multiplePerRoom"]
                    # print(allow_duplicates_of_asset_type)

                    if not allow_duplicates_of_asset_type:
                        # NOTE: Remove all asset groups that have the type
                        spawnable_asset_groups = spawnable_asset_groups[
                            ~spawnable_asset_groups[f"has{asset_type.lower()}"]
                        ]

                        # NOTE: Remove all standalone assets that have the type
                        spawnable_assets = spawnable_assets[
                            spawnable_assets["assetType"] != asset_type
                        ]

        def convert_position(position: Vector3):
            x = a.position["x"]
            y = a.position["y"]
            z = a.position["z"]
            return (x, y, z)

        for room in self.rooms.values():

            log(f"room: {room.room_id}")
            for a in room.assets:
                if isinstance(a, Asset):
                    prefab = a.asset_id
                    prefab_size = odb.PREFABS[prefab]["size"]
                    bbox = (
                        (
                            a.position["x"] - prefab_size["x"] / 2,
                            a.position["z"] - prefab_size["z"] / 2,
                            a.position["x"] + prefab_size["x"] / 2,
                            a.position["z"] + prefab_size["z"] / 2,
                        )
                        if a.rotation == 0 or a.rotation == 180
                        else (
                            a.position["x"] - prefab_size["z"] / 2,
                            a.position["z"] - prefab_size["x"] / 2,
                            a.position["x"] + prefab_size["z"] / 2,
                            a.position["z"] + prefab_size["x"] / 2,
                        )
                    )

                    if not self.placer.place_rectangle(prefab, bbox):
                        log(f"Failed to place{prefab} into {bbox}")
                    elif odb.OBJECT_TO_TYPE[prefab] in specified_object_types:
                        log(f"conflicted with specified objects!")
                    else:
                        log(
                            f"Placed {prefab} into position:{ format(a.position['x'],'.4f')},{format(a.position['z'],'.4f')}, bbox:{bbox} rotation:{a.rotation}"
                        )

                        is_receptacle = True
                        object_instances.append(
                            {
                                "prefab": a.asset_id,
                                "position": convert_position(a.position),
                                "rotation": [0, a.rotation, 0],
                                "scale": [1, 1, 1],
                                "parent": room.room_id,
                                "type": (
                                    "interactable"
                                    if a.asset_id
                                    in self.odb.KINETIC_AND_INTERACTABLE_INFO[
                                        "interactable_names"
                                    ]
                                    else "kinematic"
                                ),
                                "room_id": room.room_id,
                                "is_receptacle": is_receptacle,
                            }
                        )

                else:  # is asset_group
                    assets_dict = a.assets_dict
                    # log(f"asset_dict: {json.dumps(assets_dict, indent=4)}")
                    max_bbox = (10000, 100000, -1, -1)
                    asset_group_full_name = []

                    conflict = False
                    for asset in assets_dict:
                        prefab = asset["assetId"]
                        asset_type = odb.OBJECT_TO_TYPE[prefab]
                        if asset_type in specified_object_types:
                            # log(f'conflicted with specified objects!')
                            conflict = True
                            break

                        asset_group_full_name.append(prefab)
                        if "children" in asset:
                            for child in asset["children"]:
                                prefab = child["assetId"]
                                asset_group_full_name.append(prefab)
                        prefab_size = odb.PREFABS[prefab]["size"]
                        bbox = (
                            (
                                asset["position"]["x"] - prefab_size["x"] / 2,
                                asset["position"]["z"] - prefab_size["z"] / 2,
                                asset["position"]["x"] + prefab_size["x"] / 2,
                                asset["position"]["z"] + prefab_size["z"] / 2,
                            )
                            if asset["rotation"] == 0 or asset["rotation"] == 180
                            else (
                                asset["position"]["x"] - prefab_size["z"] / 2,
                                asset["position"]["z"] - prefab_size["x"] / 2,
                                asset["position"]["x"] + prefab_size["z"] / 2,
                                asset["position"]["z"] + prefab_size["x"] / 2,
                            )
                        )
                        max_bbox = (
                            min(max_bbox[0], bbox[0]),
                            min(max_bbox[1], bbox[1]),
                            max(max_bbox[2], bbox[2]),
                            max(max_bbox[3], bbox[3]),
                        )
                    asset_group_full_name = "+".join(asset_group_full_name)

                    if not self.placer.place_rectangle(asset_group_full_name, max_bbox):
                        log(f"Failed to place{asset_group_full_name} into {max_bbox}")
                    elif conflict:
                        log(f"conflicted with specified objects!")
                    else:

                        log(f"Placed {asset_group_full_name} into {max_bbox}")
                        for asset in assets_dict:

                            is_receptacle = True
                            if (
                                "tv" in asset["assetId"].lower()
                                or "chair" in asset["assetId"].lower()
                            ):
                                is_receptacle = False

                            # log(
                            #     f'{asset["assetId"]} is_receptacle: {is_receptacle} tvinid {"tv" in asset["assetId"].lower()} chairinid {"chair" in asset["assetId"].lower()}'
                            # )
                            object_instances.append(
                                {
                                    "prefab": asset["assetId"],
                                    "position": (
                                        asset["position"]["x"],
                                        asset["position"]["y"],
                                        asset["position"]["z"],
                                    ),
                                    "rotation": [0, asset["rotation"]["y"], 0],
                                    "scale": [1, 1, 1],
                                    "parent": 0,  # 0 represents the floor
                                    "type": (
                                        "interactable"
                                        if asset["assetId"]
                                        in self.odb.KINETIC_AND_INTERACTABLE_INFO[
                                            "interactable_names"
                                        ]
                                        else "kinematic"
                                    ),
                                    "room_id": room.room_id,
                                    "is_receptacle": is_receptacle,
                                }
                            )
                            if "children" in asset:
                                for child in asset["children"]:

                                    is_receptacle = True
                                    if (
                                        "tv" in asset["assetId"].lower()
                                        or "chair" in asset["assetId"].lower()
                                    ):
                                        is_receptacle = False

                                    # log(
                                    #     f'{asset["assetId"]} is_receptacle: {is_receptacle} tvinid {"tv" in asset["assetId"].lower()} chairinid {"chair" in asset["assetId"].lower()}'
                                    # )

                                    object_instances.append(
                                        {
                                            "prefab": child["assetId"],
                                            "position": (
                                                child["position"]["x"],
                                                child["position"]["y"],
                                                child["position"]["z"],
                                            ),
                                            "rotation": [0, child["rotation"]["y"], 0],
                                            "scale": [1, 1, 1],
                                            "parent": 0,  # 0 represents the floor
                                            "type": (
                                                "interactable"
                                                if child["assetId"]
                                                in self.odb.KINETIC_AND_INTERACTABLE_INFO[
                                                    "interactable_names"
                                                ]
                                                else "kinematic"
                                            ),
                                            "room_id": room.room_id,
                                            "is_receptacle": is_receptacle,
                                        }
                                    )

        max_object_types_per_room = 10
        small_object_instances = []
        small_object_instances = add_small_objects(
            object_instances,
            odb,
            self.rooms,
            max_object_types_per_room,
            (min_x, min_z, max_x, max_z),
            object_counts=object_counts,
            specified_object_instances=specified_object_instances,
            receptacle_object_counts=receptacle_object_counts,
        )

        # for object in small_object_instances:
        #     log(f"small_object: {object['prefab']}")

        ### STEP 5: Adjust Positions for Unity GameObject
        # Convert all the positions (the center of the mesh bounding box) to positions of Unity GameObject transform
        # They are not equal because position of a GameObject also depends on the relative center offset of the mesh within the prefab

        instances = (
            floor_instances
            + object_instances
            + specified_object_instances
            + small_object_instances
        )

        DEBUG = True
        if DEBUG:
            for inst in instances:
                inst["type"] = "kinematic"

        height = max(12, (max_z - min_z) * 1 + 2)
        # center = [0, height, 0]
        center = [(min_x + max_x) / 2, height, (min_z + max_z) / 2]
        infos = {
            "prompt": "",
            "instances": instances,
            "player": player,
            "agent": playmate,
            "center": center,
        }
        with open("last_scene.json", "w", encoding="utf-8") as f:
            json.dump(infos, f, ensure_ascii=False, indent=4)
        return infos
