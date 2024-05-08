import copy
import random
import time
from collections import defaultdict
from statistics import mean
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypedDict,
    Union,
)

import numpy as np
from shapely.geometry import LineString, MultiPolygon, Point, Polygon

from legent.scene_generation.constants import (
    MARGIN,
    MAX_INTERSECTING_OBJECT_RETRIES,
    MIN_RECTANGLE_SIDE_SIZE,
    OPENNESS_RANDOMIZATIONS,
    P_CHOOSE_EDGE,
    P_LARGEST_RECTANGLE,
    PADDING_AGAINST_WALL,
)
from legent.scene_generation.objects import ObjectDB

from .asset_groups import Asset, AssetGroup, AssetGroupGenerator
from .types import Vector3


def is_chosen_asset_group(data: dict) -> bool:
    """Determine if a dict is from a ChosenAsset or ChosenAssetGroup."""
    return "objects" in data


class ChosenAssetGroup(TypedDict):
    assetGroupName: str
    xSize: float
    ySize: float
    zSize: float
    rotated: bool
    objects: Any
    bounds: Any
    allowDuplicates: bool


class ChosenAsset(TypedDict):
    xSize: float
    ySize: float
    zSize: float
    assetId: str
    rotated: bool


class OrthogonalPolygon:
    def __init__(self, polygon) -> None:
        self.polygon = polygon
        self._set_attributes()

    def _set_attributes(self) -> None:
        if isinstance(self.polygon, MultiPolygon):
            points = set()
            for poly in self.polygon.geoms:
                points.update(set(poly.exterior.coords))
                for interior in poly.interiors:
                    points.update(set(interior.coords[:]))
        else:
            points = set(self.polygon.exterior.coords)
            for interior in self.polygon.interiors:
                points.update(set(interior.coords[:]))

        self.xs = [p[0] for p in points]
        self.zs = [p[1] for p in points]

        self.unique_xs = sorted(list(set(self.xs)))
        self.unique_zs = sorted(list(set(self.zs)))

        self.x_edges_map = self._set_x_edges_map(points)
        self.z_edges_map = self._set_z_edges_map(points)

        # NOTE: get_neighboring_rectangles() sets the area
        self.get_neighboring_rectangles()

    def is_point_inside(self, point: Tuple[float, float]) -> bool:
        return self.polygon.contains(Point(*point))

    def _set_x_edges_map(self, points: Set[Tuple[float, float]]):
        out = defaultdict(list)
        points = list(points)
        for p0, p1 in zip(points, points[1:]):
            if p0[0] == p1[0]:
                out[p0[0]].append(sorted([p0[1], p1[1]]))
        return out

    def _set_z_edges_map(self, points: Set[Tuple[float, float]]):
        out = defaultdict(list)
        points = list(points)
        for p0, p1 in zip(points, points[1:]):
            if p0[1] == p1[1]:
                out[p0[1]].append(sorted([p0[0], p1[0]]))
        return out

    def get_neighboring_rectangles(self) -> Set[Tuple[float, float, float, float]]:
        out = []
        area = 0
        for x0, x1 in zip(self.unique_xs, self.unique_xs[1:]):
            for z0, z1 in zip(self.unique_zs, self.unique_zs[1:]):
                mid_x = (x0 + x1) / 2
                mid_z = (z0 + z1) / 2
                if self.is_point_inside((mid_x, mid_z)):
                    out.append((x0, z0, x1, z1))
                    area += (x1 - x0) * (z1 - z0)

        return set(out)

    def _join_neighboring_rectangles(
        self, rects: Set[Tuple[float, float, float, float]]
    ) -> Tuple[float, float, float, float]:
        orig_rects = rects.copy()
        out = []
        for rect1 in rects.copy():
            x0_0, z0_0, x1_0, z1_0 = rect1
            points1 = {(x0_0, z0_0), (x0_0, z1_0), (x1_0, z1_0), (x1_0, z0_0)}
            for rect2 in rects - {rect1}:
                x0_1, z0_1, x1_1, z1_1 = rect2
                points2 = {(x0_1, z0_1), (x0_1, z1_1), (x1_1, z1_1), (x1_1, z0_1)}
                if len(points1 & points2) == 2:
                    out.append(
                        (
                            min(x0_0, x1_0, x0_1, x1_1),
                            min(z0_0, z1_0, z0_1, z1_1),
                            max(x0_0, x1_0, x0_1, x1_1),
                            max(z0_0, z1_0, z0_1, z1_1),
                        )
                    )
        new_rects = set(out) - orig_rects
        all_rects = set(out) | orig_rects
        cnt = 1
        while True:
            out = []
            for rect1 in new_rects:
                x0_0, z0_0, x1_0, z1_0 = rect1
                points1 = {(x0_0, z0_0), (x0_0, z1_0), (x1_0, z1_0), (x1_0, z0_0)}
                for rect2 in all_rects - {rect1}:
                    x0_1, z0_1, x1_1, z1_1 = rect2
                    points2 = {(x0_1, z0_1), (x0_1, z1_1), (x1_1, z1_1), (x1_1, z0_1)}
                    if len(points1 & points2) == 2:
                        out.append(
                            (
                                min(x0_0, x1_0, x0_1, x1_1),
                                min(z0_0, z1_0, z0_1, z1_1),
                                max(x0_0, x1_0, x0_1, x1_1),
                                max(z0_0, z1_0, z0_1, z1_1),
                            )
                        )
            new_rects = set(out) - all_rects
            all_rects = set(out) | all_rects
            if cnt == 2:
                return all_rects
            if not new_rects:
                return all_rects
            cnt += 1
        # return set(out)

    def random_cover_rectangles(
        self, rects: Set[Tuple[float, float, float, float]]
    ) -> Set[Tuple[float, float, float, float]]:
        orig_rects = rects.copy()
        curr_rects = rects.copy()
        out = []
        curr_rect = random.choice(list(orig_rects))
        curr_rects = curr_rects - {curr_rect}
        while True:
            x0_0, z0_0, x1_0, z1_0 = curr_rect
            points1 = {(x0_0, z0_0), (x0_0, z1_0), (x1_0, z1_0), (x1_0, z0_0)}
            grow_flag = False
            for rect in curr_rects:
                x0_1, z0_1, x1_1, z1_1 = rect
                points2 = {(x0_1, z0_1), (x0_1, z1_1), (x1_1, z1_1), (x1_1, z0_1)}
                if len(points1 & points2) == 2:
                    curr_rects = curr_rects - {rect}
                    curr_rect = (
                        min(x0_0, x1_0, x0_1, x1_1),
                        min(z0_0, z1_0, z0_1, z1_1),
                        max(x0_0, x1_0, x0_1, x1_1),
                        max(z0_0, z1_0, z0_1, z1_1),
                    )
                    grow_flag = True
                    break
            if grow_flag:
                continue
            else:
                out.append(curr_rect)
                if not curr_rects:
                    break
                curr_rect = random.choice(list(curr_rects))
                curr_rects = curr_rects - {curr_rect}
        return set(out) | orig_rects

    def get_all_rectangles(self) -> Set[Tuple[float, float, float, float]]:
        start_time = time.time()
        neighboring_rectangles = self.get_neighboring_rectangles().copy()
        curr_rects = neighboring_rectangles
        all_rects = self.random_cover_rectangles(curr_rects)
        return all_rects

    @staticmethod
    def get_top_down_poly(
        anchor_location: Tuple[float, float],
        anchor_delta: int,
        asset_bb: Dict[str, float],
        rotated: bool,
    ) -> List[Tuple[float, float]]:
        """Return the top-down polygon from an asset."""
        x, z = anchor_location
        rot1, rot2 = ("z", "x") if rotated else ("x", "z")

        if anchor_delta == 0:
            top_down_poly = [
                (x, z),
                (x, z + asset_bb[rot2] + PADDING_AGAINST_WALL),
                (
                    x - asset_bb[rot1] - PADDING_AGAINST_WALL,
                    z + asset_bb[rot2] + PADDING_AGAINST_WALL,
                ),
                (x - asset_bb[rot1] - PADDING_AGAINST_WALL, z),
            ]
        elif anchor_delta == 1:
            top_down_poly = [
                (x - asset_bb[rot1] / 2, z),
                (x + asset_bb[rot1] / 2, z),
                (x + asset_bb[rot1] / 2, z + asset_bb[rot2] + PADDING_AGAINST_WALL),
                (x - asset_bb[rot1] / 2, z + asset_bb[rot2] + PADDING_AGAINST_WALL),
            ]
        elif anchor_delta == 2:
            top_down_poly = [
                (x, z),
                (x, z + asset_bb[rot2] + PADDING_AGAINST_WALL),
                (
                    x + asset_bb[rot1] + PADDING_AGAINST_WALL,
                    z + asset_bb[rot2] + PADDING_AGAINST_WALL,
                ),
                (x + asset_bb[rot1] + PADDING_AGAINST_WALL, z),
            ]
        elif anchor_delta == 3:
            top_down_poly = [
                (x, z + asset_bb[rot2] / 2),
                (x, z - asset_bb[rot2] / 2),
                (x - asset_bb[rot1] - PADDING_AGAINST_WALL, z - asset_bb[rot2] / 2),
                (x - asset_bb[rot1] - PADDING_AGAINST_WALL, z + asset_bb[rot2] / 2),
            ]
        elif anchor_delta == 4:
            top_down_poly = [
                (x - asset_bb[rot1] / 2, z - asset_bb[rot2] / 2),
                (x + asset_bb[rot1] / 2, z - asset_bb[rot2] / 2),
                (x + asset_bb[rot1] / 2, z + asset_bb[rot2] / 2),
                (x - asset_bb[rot1] / 2, z + asset_bb[rot2] / 2),
            ]
        elif anchor_delta == 5:
            top_down_poly = [
                (x, z + asset_bb[rot2] / 2),
                (x, z - asset_bb[rot2] / 2),
                (x + asset_bb[rot1] + PADDING_AGAINST_WALL, z - asset_bb[rot2] / 2),
                (x + asset_bb[rot1] + PADDING_AGAINST_WALL, z + asset_bb[rot2] / 2),
            ]
        elif anchor_delta == 6:
            top_down_poly = [
                (x, z),
                (x, z - asset_bb[rot2] - PADDING_AGAINST_WALL),
                (
                    x - asset_bb[rot1] - PADDING_AGAINST_WALL,
                    z - asset_bb[rot2] - PADDING_AGAINST_WALL,
                ),
                (x - asset_bb[rot1] - PADDING_AGAINST_WALL, z),
            ]
        elif anchor_delta == 7:
            top_down_poly = [
                (x - asset_bb[rot1] / 2, z),
                (x + asset_bb[rot1] / 2, z),
                (x + asset_bb[rot1] / 2, z - asset_bb[rot2] - PADDING_AGAINST_WALL),
                (x - asset_bb[rot1] / 2, z - asset_bb[rot2] - PADDING_AGAINST_WALL),
            ]
        elif anchor_delta == 8:
            top_down_poly = [
                (x, z),
                (x, z - asset_bb[rot2] - PADDING_AGAINST_WALL),
                (
                    x + asset_bb[rot1] + PADDING_AGAINST_WALL,
                    z - asset_bb[rot2] - PADDING_AGAINST_WALL,
                ),
                (x + asset_bb[rot1] + PADDING_AGAINST_WALL, z),
            ]
        else:
            raise Exception(
                f"Unknown anchor anchor_delta: {anchor_delta}. Must be an int in [0:8]."
            )

        return top_down_poly

    @staticmethod
    def add_margin_to_top_down_poly(
        poly: Sequence[Tuple[float, float]],
        rotation: Literal[0, 90, 180, 270],
        anchor_type: Literal["inCorner", "onEdge", "inMiddle"],
    ) -> Sequence[Tuple[float, float]]:
        """Adds margin to a top-down polygon."""
        if rotation not in {0, 90, 180, 270}:
            raise ValueError(
                f"rotation must be in {{0, 90, 180, 270}}. Got {rotation}."
            )
        if anchor_type not in {"inCorner", "onEdge", "inMiddle"}:
            raise ValueError(
                'anchor_type must be in {{"inCorner", "onEdge", "inMiddle"}}.'
                f" You gave {anchor_type}."
            )

        min_x = min(p[0] for p in poly)
        max_x = max(p[0] for p in poly)

        min_z = min(p[1] for p in poly)
        max_z = max(p[1] for p in poly)

        if anchor_type == "inMiddle":
            # NOTE: add margin to each side of a middle object.
            margin = MARGIN["middle"]

            min_x -= margin
            max_x += margin

            min_z -= margin
            max_z += margin
        else:
            if anchor_type == "onEdge":
                front_space = MARGIN["edge"]["front"]
                back_space = MARGIN["edge"]["back"]
                side_space = MARGIN["edge"]["sides"]
            elif anchor_type == "inCorner":
                front_space = MARGIN["corner"]["front"]
                back_space = MARGIN["corner"]["back"]
                side_space = MARGIN["corner"]["sides"]

            if rotation == 0:
                max_z += front_space
                min_z -= back_space
                max_x += side_space
                min_x -= side_space
            elif rotation == 90:
                max_x += front_space
                min_x -= back_space
                max_z += side_space
                min_z -= side_space
            elif rotation == 180:
                min_z -= front_space
                max_z += back_space
                max_x += side_space
                min_x -= side_space
            elif rotation == 270:
                min_x -= front_space
                max_x += back_space
                max_z += side_space
                min_z -= side_space

        return [(min_x, min_z), (min_x, max_z), (max_x, max_z), (max_x, min_z)]

    def subtract(self, polygon: Polygon) -> None:
        self.polygon -= polygon
        self._set_attributes()


class Room:
    def __init__(
        self,
        polygon: Sequence[Tuple[int, int]],
        room_type: Literal["Kitchen", "LivingRoom", "Bedroom", "Bathroom"],
        room_id: int,
        odb: ObjectDB,
    ) -> None:
        self.room_polygon = OrthogonalPolygon(polygon=copy.deepcopy(polygon))
        self.open_polygon = OrthogonalPolygon(polygon=copy.deepcopy(polygon))
        self.room_type = room_type
        self.room_id = room_id
        self.odb = odb
        self.split = "train"
        self.assets: List[Union[Asset, AssetGroup]] = []
        self.last_rectangles: Optional[Set[Tuple[float, float, float, float]]] = None

    @staticmethod
    def sample_rotation(
        asset: Dict[str, Any], rect_x_length: float, rect_z_length: float
    ) -> bool:
        valid_rotated = []
        if asset["xSize"] < rect_x_length and asset["zSize"] < rect_z_length:
            valid_rotated.append(False)
        if asset["xSize"] < rect_z_length and asset["zSize"] < rect_x_length:
            valid_rotated.append(True)
        return random.choice(valid_rotated)

    def sample_next_rectangle(
        self, choose_largest_rectangle: bool = False, cache_rectangles: bool = False
    ):
        start_time = time.time()
        rectangles = self.open_polygon.get_all_rectangles()
        self.last_rectangles = rectangles
        end_time = time.time()
        if len(rectangles) == 0:
            return None

        if choose_largest_rectangle or random.random() < P_LARGEST_RECTANGLE:
            # NOTE: p(epsilon) = choose largest area
            max_area = 0
            out: Optional[Tuple[float, float, float, float]] = None
            for rect in rectangles:
                x0, z0, x1, z1 = rect
                area = (x1 - x0) * (z1 - z0)
                if area > max_area:
                    max_area = area
                    out = rect
            end_time = time.time()
            return out

        # NOTE: p(1 - epsilon) = randomly choose rect, weighted by area
        rectangles = list(rectangles)
        population = []
        weights = []
        for rect in rectangles:
            x0, z0, x1, z1 = rect
            xdist = x1 - x0
            zdist = z1 - z0
            if xdist < MIN_RECTANGLE_SIDE_SIZE or zdist < MIN_RECTANGLE_SIDE_SIZE:
                continue
            area = xdist * zdist
            weights.append(area)
            population.append(rect)
        end_time = time.time()
        if not weights:
            return None
        end_time = time.time()
        return random.choices(population=population, weights=weights, k=1)[0]

    def sample_anchor_location(
        self,
        rectangle: Tuple[float, float, float, float],
    ) -> Tuple[Optional[float], Optional[float], int, str]:
        """Chooses which object to place in the rectangle.

        Returns:
            The (x, z, anchor_delta, anchor_type), where anchor_delta specifies
            the direction of where to place the object. Specifically, it can be though
            of with axes: ::

                0   1   2
                    |
                3 - 4 - 5
                    |
                6   7   8

            where

            * 4 specifies to center the object at (x, z)

            * 8 specifies that the object should go to the bottom right of (x, z)

            * 0 specifies that the object should go to the upper left of (x, z)

            * 1 specifies that the object should go to the upper middle of (x, z)

            and so on.

            The :code:`anchor_type` is:

            * "inCorner" of open area in the scene.

            * "onEdge" of open area in the scene.

            * "inMiddle" of the scene, not next to any other objects.

        """
        x0, z0, x1, z1 = rectangle

        # Place the object in a corner of the room
        rect_corners = [(x0, z0, 2), (x0, z1, 8), (x1, z1, 6), (x1, z0, 0)]
        random.shuffle(rect_corners)
        epsilon = 1e-3
        corners = []
        for x, z, anchor_delta in rect_corners:
            q1 = self.room_polygon.is_point_inside((x + epsilon, z + epsilon))
            q2 = self.room_polygon.is_point_inside((x - epsilon, z + epsilon))
            q3 = self.room_polygon.is_point_inside((x - epsilon, z - epsilon))
            q4 = self.room_polygon.is_point_inside((x + epsilon, z - epsilon))
            if (q1 and q3 and not q2 and not q4) or (q2 and q4 and not q1 and not q3):
                # DiagCorner
                corners.append((x, z, anchor_delta, "inCorner"))
            elif (
                (q1 and not q2 and not q3 and not q4)
                or (q2 and not q1 and not q3 and not q4)
                or (q3 and not q1 and not q2 and not q4)
                or (q4 and not q1 and not q2 and not q3)
            ):
                corners.append((x, z, anchor_delta, "inCorner"))
        if corners:
            return random.choice(corners)

        # Place the object on an edge of the room
        edges = []
        rect_edge_lines = [
            (LineString([(x0, z0), (x1, z0)]), 1),
            (LineString([(x0, z0), (x0, z1)]), 5),
            (LineString([(x1, z0), (x1, z1)]), 3),
            (LineString([(x0, z1), (x1, z1)]), 7),
        ]
        random.shuffle(rect_edge_lines)
        room_outer_lines = LineString(self.room_polygon.polygon.exterior.coords)
        for rect_edge_line, anchor_delta in rect_edge_lines:
            if room_outer_lines.contains(rect_edge_line):
                xs = [p[0] for p in rect_edge_line.coords]
                zs = [p[1] for p in rect_edge_line.coords]
                edges.append((xs, zs, anchor_delta, "onEdge"))
        if edges and random.random() < P_CHOOSE_EDGE:
            return random.choice(edges)

        # Place an object in the middle of the room
        return (None, None, 4, "inMiddle")

    def place_asset_group(
        self,
        asset_group, # pd.DataFrame
        set_rotated: Optional[bool],
        rect_x_length: float,
        rect_z_length: float,
    ) -> Optional[ChosenAssetGroup]:
        """

        Returns None if the asset group collides on each attempt (very unlikely).
        """
        asset_group_generator: AssetGroupGenerator = asset_group[
            "assetGroupGenerator"
        ].iloc[0]

        for _ in range(MAX_INTERSECTING_OBJECT_RETRIES):
            object_placement = asset_group_generator.sample_object_placement()

            return ChosenAssetGroup(
                assetGroupName=asset_group["assetGroupName"].iloc[0],
                xSize=object_placement["bounds"]["x"]["length"],
                ySize=object_placement["bounds"]["y"]["length"],
                zSize=object_placement["bounds"]["z"]["length"],
                rotated=set_rotated,
                objects=object_placement["objects"],
                bounds=object_placement["bounds"],
                allowDuplicates=asset_group["allowDuplicates"].iloc[0],
            )

    def place_asset(
        self,
        asset, # pd.DataFrame
        set_rotated: Optional[bool],
        rect_x_length: float,
        rect_z_length: float,
    ) -> ChosenAsset:
        # NOTE: convert the pd dataframe to a dict
        asset.reset_index(drop=False, inplace=True)
        asset = asset.to_dict(orient="records")[0]

        # NOTE: Choose the rotation if both were valid.
        if set_rotated is None:
            set_rotated = Room.sample_rotation(
                asset=asset, rect_x_length=rect_x_length, rect_z_length=rect_z_length
            )
        asset["rotated"] = set_rotated

        return ChosenAsset(**asset)

    def sample_place_asset_in_rectangle(
        self,
        asset: Union[ChosenAsset, ChosenAssetGroup],
        rectangle: Tuple[float, float, float, float],
        anchor_type: Literal["inCorner", "onEdge", "inMiddle"],
        x_info: Any,
        z_info: Any,
        anchor_delta: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8],
    ) -> None:
        """Places a chosen asset somewhere inside of the rectangle."""
        bb = dict(
            x=asset["xSize"] if not asset["rotated"] else asset["zSize"],
            y=asset["ySize"],
            z=asset["zSize"] if not asset["rotated"] else asset["xSize"],
        )
        if anchor_type == "inCorner":
            x, z = x_info, z_info
            if anchor_delta == 0:
                rotation = 270 if asset["rotated"] else 0
            elif anchor_delta == 2:
                rotation = 90 if asset["rotated"] else 0
            elif anchor_delta == 6:
                rotation = 270 if asset["rotated"] else 180
            elif anchor_delta == 8:
                rotation = 90 if asset["rotated"] else 180
        elif anchor_type == "onEdge":
            xs, zs = x_info, z_info
            if anchor_delta in {1, 7}:
                # randomize x
                x0, x1 = xs
                x_length = x1 - x0
                full_rand_dist = x_length - bb["x"]
                rand_dist = random.random() * full_rand_dist
                x = x0 + rand_dist + bb["x"] / 2
                z = sum(zs) / 2
                rotation = 180 if anchor_delta == 7 else 0
            elif anchor_delta in {3, 5}:
                # randomize z
                z0, z1 = zs
                z_length = z1 - z0
                full_rand_dist = z_length - bb["z"]
                rand_dist = random.random() * full_rand_dist
                x = sum(xs) / 2
                z = z0 + rand_dist + bb["z"] / 2
                rotation = 90 if anchor_delta == 5 else 270
        elif anchor_type == "inMiddle":
            x, z = 0, 0
            x0, z0, x1, z1 = rectangle
            x_length = x1 - x0
            z_length = z1 - z0
            full_x_rand_dist = x_length - bb["x"]
            full_z_rand_dist = z_length - bb["z"]
            rand_x_dist = random.random() * full_x_rand_dist
            rand_z_dist = random.random() * full_z_rand_dist
            x = x0 + rand_x_dist + bb["x"] / 2
            z = z0 + rand_z_dist + bb["z"] / 2
            rotation = random.choice([90, 270] if asset["rotated"] else [0, 180])

        top_down_poly = OrthogonalPolygon.get_top_down_poly(
            anchor_location=(x, z),
            anchor_delta=anchor_delta,
            asset_bb=bb,
            rotated=False,
        )
        center_x = mean(p[0] for p in top_down_poly)
        center_z = mean(p[1] for p in top_down_poly)

        top_down_poly_with_margin = OrthogonalPolygon.add_margin_to_top_down_poly(
            poly=top_down_poly,
            rotation=rotation,
            anchor_type=anchor_type,
        )

        if is_chosen_asset_group(asset):
            objects = []
            for obj in asset["objects"]:
                x = obj["position"]["x"]
                z = obj["position"]["z"]

                # NOTE: center the origin of the asset group at (0, 0)
                x -= asset["bounds"]["x"]["center"]
                z -= asset["bounds"]["z"]["center"]

                # NOTE: rotate the asset about the origin
                rotation_rad = -rotation * np.pi / 180.0
                x, z = (
                    x * np.cos(rotation_rad) - z * np.sin(rotation_rad),
                    x * np.sin(rotation_rad) + z * np.cos(rotation_rad),
                )

                x += center_x
                z += center_z

                objects.append(
                    {
                        "assetId": obj["assetId"],
                        # NOTE: adds the base rotation to the object's rotation
                        "rotation": (obj["rotation"] + rotation) % 360,
                        "position": Vector3(x=x, y=obj["position"]["y"], z=z),
                        "instanceId": obj["instanceId"],
                    }
                )
            self.add_asset(
                AssetGroup(
                    asset_group_name=asset["assetGroupName"],
                    top_down_poly=top_down_poly,
                    objects=objects,
                    top_down_poly_with_margin=top_down_poly_with_margin,
                    anchor_type=anchor_type,
                    room_id=self.room_id,
                    object_n=len(self.assets),
                    odb=self.odb,
                )
            )
        else:
            states = {}

            obj_type = self.odb.OBJECT_TO_TYPE[asset["assetId"]]

            self.add_asset(
                Asset(
                    asset_id=asset["assetId"],
                    top_down_poly=top_down_poly,
                    top_down_poly_with_margin=top_down_poly_with_margin,
                    rotation=rotation,
                    position=Vector3(
                        x=center_x,
                        y=bb["y"] / 2,
                        z=center_z,
                    ),
                    anchor_type=anchor_type,
                    room_id=self.room_id,
                    object_n=len(self.assets),
                    states=states,
                    odb=self.odb,
                )
            )

    def add_asset(self, asset: Union[Asset, AssetGroup]) -> None:
        """Add an asset to the room.

        Assumes that the asset can be placed
        """
        self.assets.append(asset)
        self.open_polygon.subtract(Polygon(asset.top_down_poly_with_margin))
