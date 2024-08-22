from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
from attrs import define

from legent.scene_generation.constants import OUTDOOR_ROOM_ID
from legent.scene_generation.room_spec import RoomSpec

from .floorplan import generate_floorplan
from .interior_boundaries import sample_interior_boundary


@define
class HouseStructure:
    interior_boundary: np.ndarray
    floorplan: np.ndarray
    rowcol_walls: Dict[Tuple[int, int], List[Tuple[int, int]]]
    boundary_groups: Dict[Tuple[int, int], List[Tuple[float, float]]]
    xz_poly_map: Dict[int, List[Tuple[float, float]]]
    ceiling_height: float


XZPoly = List[Tuple[Tuple[float, float], Tuple[float, float]]]
BoundaryGroups = Dict[Tuple[int, int], List[Tuple[float, float]]]
from .constants import UNIT_SIZE

INTERIOR_BOUNDARY_SCALE = UNIT_SIZE


def find_walls(floorplan: np.array):
    walls = defaultdict(list)
    for row in range(len(floorplan) - 1):
        for col in range(len(floorplan[0]) - 1):
            a = floorplan[row, col]
            b = floorplan[row, col + 1]
            if a != b:
                walls[(int(min(a, b)), int(max(a, b)))].append(
                    ((row - 1, col), (row, col))
                )
            b = floorplan[row + 1, col]
            if a != b:
                walls[(int(min(a, b)), int(max(a, b)))].append(
                    ((row, col - 1), (row, col))
                )
    return walls


def consolidate_walls(walls):
    """Join neighboring walls together.

    Example: if one of the walls is ::

        [
            ((0, 0), (0, 1)),
            ((0, 1), (0, 2)),
            ((0, 2), (0, 3)),
            ((0, 3), (0, 4)),
            ((0, 4), (0, 5)),
            ((0, 5), (0, 6)),
            ((0, 6), (0, 7)),
            ((0, 7), (0, 8)),
            ((0, 8), (0, 9)),
            ((0, 0), (1, 0)),
            ((1, 0), (2, 0)),
            ((2, 0), (3, 0)),
            ((3, 0), (4, 0)),
            ((4, 0), (5, 0)),
            ((5, 0), (6, 0)),
            ((6, 0), (7, 0)),
            ((7, 0), (8, 0)),
            ((8, 0), (9, 0))
        ]

    it becomes ::

        {
            ((0, 0), (0, 9)),
            ((0, 0), (9, 0))
        }
    """
    out = dict()
    for wall_group_id, wall_pairs in walls.items():
        wall_map = defaultdict(lambda: set())
        wall_map = dict()
        for wall in wall_pairs:
            if wall[0] not in wall_map:
                wall_map[wall[0]] = set()
            wall_map[wall[0]].add(wall[1])

        did_update = True
        while did_update:
            did_update = False
            for w1_1 in wall_map.copy():
                if w1_1 not in wall_map:
                    continue
                break_outer = False
                for w1_2 in wall_map[w1_1]:
                    if w1_2 in wall_map:
                        w2_1 = w1_2
                        for w2_2 in wall_map[w2_1]:
                            if (
                                w1_1[0] == w1_2[0] == w2_1[0] == w2_2[0]
                                or w1_1[1] == w1_2[1] == w2_1[1] == w2_2[1]
                            ):
                                wall_map[w2_1].remove(w2_2)
                                if not wall_map[w2_1]:
                                    del wall_map[w2_1]

                                wall_map[w1_1].remove(w2_1)
                                wall_map[w1_1].add(w2_2)

                                did_update = True
                                break_outer = True
                                break
                        if break_outer:
                            break
                    if break_outer:
                        break
        out[wall_group_id] = set([(w1, w2) for w1 in wall_map for w2 in wall_map[w1]])
    return out


def scale_boundary_groups(
    boundary_groups: BoundaryGroups, scale: float, precision: int = 3
) -> BoundaryGroups:
    out = dict()
    for key, lines in boundary_groups.items():
        scaled_lines = set()
        for (x0, z0), (x1, z1) in lines:
            scaled_lines.add(
                (
                    (round(x0 * scale, precision), round(z0 * scale, precision)),
                    (round(x1 * scale, precision), round(z1 * scale, precision)),
                )
            )
        out[key] = scaled_lines
    return out


def get_wall_loop(walls: Sequence[XZPoly]):
    walls_left = set(walls)
    out = [walls[0]]
    walls_left.remove(walls[0])
    while walls_left:
        for wall in walls_left:
            if out[-1][1] == wall[0]:
                out.append(wall)
                walls_left.remove(wall)
                break
            elif out[-1][1] == wall[1]:
                out.append((wall[1], wall[0]))
                walls_left.remove(wall)
                break
        else:
            raise Exception(f"No connecting wall for {out[-1]}!")
    return out


def get_xz_poly_map(boundary_groups, room_ids: Set[int]) -> Dict[int, XZPoly]:
    out = dict()
    WALL_THICKNESS = 0.1
    for room_id in room_ids:
        room_walls = []
        for k in [k for k in boundary_groups.keys() if room_id in k]:
            room_walls.extend(boundary_groups[k])

        room_wall_loop = get_wall_loop(room_walls)

        # determines if the loop is counter-clockwise, flips if it is
        edge_sum = 0
        for (x0, z0), (x1, z1) in room_wall_loop:
            dist = x0 * z1 - x1 * z0
            edge_sum += dist
        if edge_sum > 0:
            room_wall_loop = [(p1, p0) for p0, p1 in reversed(room_wall_loop)]

        points = []
        dirs = []
        for p0, p1 in room_wall_loop:
            points.append(p0)
            if p1[0] > p0[0]:
                dirs.append("right")
            elif p1[0] < p0[0]:
                dirs.append("left")
            elif p1[1] > p0[1]:
                dirs.append("up")
            elif p1[1] < p0[1]:
                dirs.append("down")
        for i in range(len(points)):
            this_dir = dirs[i]
            last_dir = dirs[i - 1] if i > 0 else dirs[-1]
            if this_dir == "right" and last_dir == "up":
                points[i] = (
                    points[i][0] + WALL_THICKNESS,
                    points[i][1] - WALL_THICKNESS,
                )
            elif this_dir == "down" and last_dir == "right":
                points[i] = (
                    points[i][0] - WALL_THICKNESS,
                    points[i][1] - WALL_THICKNESS,
                )
            elif this_dir == "left" and last_dir == "down":
                points[i] = (
                    points[i][0] - WALL_THICKNESS,
                    points[i][1] + WALL_THICKNESS,
                )
            elif this_dir == "up" and last_dir == "left":
                points[i] = (
                    points[i][0] + WALL_THICKNESS,
                    points[i][1] + WALL_THICKNESS,
                )
        room_wall_loop = list(zip(points, points[1:] + [points[0]]))
        out[room_id] = room_wall_loop
    return out


def generate_house_structure(room_spec: RoomSpec, dims: Optional[Tuple[int, int]], unit_size):
    room_ids = set(room_spec.room_type_map.keys())

    generate_dims = None
    if dims != None:
        generate_dims = dims
    elif room_spec.dims is not None:
        generate_dims = room_spec.dims()

    interior_boundary = sample_interior_boundary(
        num_rooms=len(room_ids),
        dims=generate_dims,
    )

    floorplan = generate_floorplan(
        room_spec=room_spec, interior_boundary=interior_boundary
    )

    floorplan = np.pad(
        floorplan, pad_width=1, mode="constant", constant_values=OUTDOOR_ROOM_ID
    )
    rowcol_walls = find_walls(floorplan=floorplan)
    boundary_groups = consolidate_walls(walls=rowcol_walls)
    boundary_groups = scale_boundary_groups(
        boundary_groups=boundary_groups,
        # scale=INTERIOR_BOUNDARY_SCALE,
        scale = unit_size
    )
    xz_poly_map = get_xz_poly_map(boundary_groups=boundary_groups, room_ids=room_ids)

    ceiling_height = 0
    return HouseStructure(
        interior_boundary=interior_boundary,
        floorplan=floorplan,
        rowcol_walls=rowcol_walls,
        boundary_groups=boundary_groups,
        xz_poly_map=xz_poly_map,
        ceiling_height=ceiling_height,
    )
