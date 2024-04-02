import random
from typing import Any, Dict, Iterable, List, Set, Tuple, Union

from legent.scene_generation.constants import OUTDOOR_ROOM_ID
from legent.scene_generation.house import HouseStructure
from legent.scene_generation.objects import ObjectDB
from legent.scene_generation.room_spec import LeafRoom, MetaRoom, RoomSpec
from legent.scene_generation.types import BoundaryGroups

OPEN_ROOM_CONNECTIONS = [
    {"between": {"Kitchen", "LivingRoom"}, "p": 0.75, "pFrame": 0.5}
]
"""Which rooms may have door frames or no walls between them?

Parameters:
- between: The neighboring room types that may have an open room connection.
- p: probability of having a door frame or no walls between rooms.
- pFrame: probability of having a door frame instead of no walls.
"""

OPEN_ROOM_PADDING = 0.35
"""Padding per each room's side of an open room connection."""

PREFERRED_ENTRANCE_PADDING = 0.5
"""The amount of space to leave, in meters, behind of the door.

.. note::
    The entrance is on the opposite side of how the direction that the door
    opens.
"""

PADDING_IN_FRONT_OF_DOOR = 0.35
"""The amount of padding, in meters, in front of a door.

.. note::
    The front of the door is the direction that it opens.

.. note::
    This is in addition to the padding already provided to ensure that the door
    can fully open.
"""

PREFERRED_ROOMS_TO_OUTSIDE = {"Kitchen", "LivingRoom"}
"""Preferred room types to have doors to the outside."""

MIN_DOORS_TO_OUTSIDE = 1
"""Minimum number of rooms with doors to the outside."""

MAX_DOORS_TO_OUTSIDE = 1
"""Maximum number of rooms with doors to the outside."""

EPSILON = 1e-3
"""Small value to compare floats within a bound."""

MAX_NEIGHBOR_RETRIES = 100


def convert_rowcol_walls(rowcol_walls):
    for k, v in rowcol_walls.items():
        new_walls = []
        for item in v:
            if item[0][0] == item[1][0]:
                new_walls.append(
                    ((item[1][0], item[1][1]), (item[1][0] + 1, item[1][1])),
                )
            elif item[0][1] == item[1][1]:
                new_walls.append(
                    ((item[1][0], item[1][1]), (item[1][0], item[1][1] + 1)),
                )
        rowcol_walls[k] = new_walls
    return rowcol_walls


def default_add_doors(
    odb: ObjectDB,
    room_spec: RoomSpec,
    house_structure: HouseStructure,
):
    """Add doors to the house."""

    boundary_groups = house_structure.boundary_groups
    rowcol_walls = house_structure.rowcol_walls
    rowcol_walls = convert_rowcol_walls(rowcol_walls)

    room_spec_neighbors = get_room_spec_neighbors(room_spec=room_spec.spec)
    openings = select_openings(
        neighboring_rooms=set(boundary_groups.keys()),
        room_spec_neighbors=room_spec_neighbors,
        room_spec=room_spec,
    )
    door_walls = select_door_walls(
        openings=openings,
        rowcol_walls=rowcol_walls,
    )
    
    return door_walls


def flatten(x):
    """Return the set of elements in an iterable collection.

    Example:
        input: [[{5}, {6}], [{555}, {667}], [{35}, {53}, {5, 6}, {555, 667}]]
        output: {5, 6, 35, 53, 555, 667}
    """
    return set([a for i in x for a in flatten(i)]) if isinstance(x, Iterable) else {x}


def get_room_spec_neighbors(
    room_spec: List[Union[MetaRoom, LeafRoom]]
) -> List[List[Set[int]]]:
    """Identify possible neighboring rooms from a room_spec.

    Here is an example, where the room_spec: ::

        [
            MetaRoom(
                children=[
                    LeafRoom(room_id=35),
                    LeafRoom(room_id=53),
                    MetaRoom(children=[LeafRoom(room_id=5), LeafRoom(room_id=6)]),
                    MetaRoom(children=[LeafRoom(room_id=555), LeafRoom(room_id=667)]),
                ],
            ),
            MetaRoom(children=[LeafRoom(room_id=48), LeafRoom(room_id=57)]),
        ]

    would return: ::

        [
            [{5}, {6}],
            [{555}, {667}],
            [{35}, {53}, {5, 6}, {555, 667}],
            [{48}, {57}],
            [{35, 5, 6, 555, 53, 667}, {48, 57}]
        ]

    Here, [{5}, {6}] indicates 5 and 6 must have a door between them,
    [{35, 5, 6, 555, 53, 667}, {48, 57}] indicates a door must connect from
    one of {35, 5, 6, 555, 53, 667} to one of {48, 57}, and [{35}, {53}, {5, 6},
    {555, 667}] indicates there must be a path between {35} to {53} to {5 or 6}
    to {555 to 667}.

    """
    out = []
    room_ids = [{room.room_id} for room in room_spec if isinstance(room, LeafRoom)]
    for room in room_spec:
        if isinstance(room, MetaRoom):
            child_ids = get_room_spec_neighbors(room.children)
            out.extend(child_ids)

            flattened_ids = flatten(child_ids)
            room_ids.append(flattened_ids)
    out.append(room_ids)
    return out


def select_openings(
    neighboring_rooms: Set[Tuple[int, int]],
    room_spec_neighbors: List[Dict[int, Any]],
    room_spec: RoomSpec,
) -> List[Tuple[int, int]]:
    """Select which neighboring rooms should have doors between them.

    Args:
        neighboring_rooms: (roomId-1, roomId-2) of neighboring rooms, where
            roomId-2 > roomId-1.
        room_spec_neighbors: specifies which rooms can have connections next to each
            other, based on the room spec.

    Returns:
        The neighboring_rooms that can have doors between them.

    """
    selected_doors = []
    for group_neighbors in room_spec_neighbors:
        # NOTE: does not need a door if its the only leaf room.
        if len(group_neighbors) == 1:
            continue

        # NOTE: indexes that still need connecting rooms
        need_connections_between = list(range(len(group_neighbors)))

        cnt = 1
        while need_connections_between:
            cnt+=1
            if cnt > MAX_NEIGHBOR_RETRIES:
                raise ValueError(
                    f"Failed to connect all rooms in group_neighbors: {group_neighbors}"
                )
            next_room_i = random.choice(need_connections_between)
            other_room_is = [i for i in range(len(group_neighbors)) if i != next_room_i]
            random.shuffle(other_room_is)
            n1_subgroup = group_neighbors[next_room_i]
            for other_room_i in other_room_is:
                n2_subgroup = group_neighbors[other_room_i]
                combos = [
                    (a, b) if a < b else (b, a)
                    for a in n1_subgroup
                    for b in n2_subgroup
                ]
                combos = randomly_prioritize_room_ids(
                    room_id_pairs=combos, room_spec=room_spec
                )
                for door_combo in combos:
                    if door_combo in neighboring_rooms:
                        selected_doors.append(door_combo)
                        if next_room_i in need_connections_between:
                            need_connections_between.remove(next_room_i)
                        if other_room_i in need_connections_between:
                            need_connections_between.remove(other_room_i)
                        break

    return selected_doors


def randomly_prioritize_room_ids(
    room_id_pairs: List[Tuple[int, int]], room_spec: RoomSpec
) -> List[Tuple[int, int]]:
    """Random shuffling while moving rooms with avoid_doors_from_metarooms to back."""
    avoid_room_id_pairs = []
    prioritize_room_id_pairs = []
    for room_id_1, room_id_2 in room_id_pairs:
        avoid_on_1 = (
            isinstance(room_spec.room_map[room_id_1], LeafRoom)
            and room_spec.room_map[room_id_1].avoid_doors_from_metarooms
        )
        avoid_on_2 = (
            isinstance(room_spec.room_map[room_id_2], LeafRoom)
            and room_spec.room_map[room_id_2].avoid_doors_from_metarooms
        )
        if avoid_on_1 or avoid_on_2:
            avoid_room_id_pairs.append((room_id_1, room_id_2))
        else:
            prioritize_room_id_pairs.append((room_id_1, room_id_2))

    random.shuffle(prioritize_room_id_pairs)
    random.shuffle(avoid_room_id_pairs)
    return prioritize_room_id_pairs + avoid_room_id_pairs


def select_door_walls(openings: List[Tuple[int, int]], rowcol_walls):
    chosen_openings = dict()
    for opening in openings:
        candidates = list(rowcol_walls[opening])
        # population = range(len(candidates))
        # weights = [abs(c[1][0] - c[0][0]) + abs(c[1][1] - c[0][1]) for c in candidates]

        # Weights are the size of each wall. Since each wall has a size along a
        # single axis, Manhattan distance is equivalent to Euclidean distance
        # chosen_opening = random.choices(population=population, weights=weights, k=1)[0]
        chosen_opening = random.choice(candidates)
        chosen_openings[opening] = chosen_opening
        # chosen_openings[opening] = candidates[chosen_opening]
    return chosen_openings


def select_outdoor_openings(
    boundary_groups: BoundaryGroups, room_type_map: Dict[int, str]
) -> List[Tuple[int, int]]:
    """Select which rooms have doors to the outside."""
    outdoor_candidates = [
        group for group in boundary_groups if OUTDOOR_ROOM_ID in group
    ]
    random.shuffle(outdoor_candidates)

    n_doors_target = random.randint(MIN_DOORS_TO_OUTSIDE, MAX_DOORS_TO_OUTSIDE)
    doors_to_outside = []

    # NOTE: Check preferred room types
    for room_id_1, room_id_2 in outdoor_candidates:
        room_id = room_id_1 if room_id_2 == OUTDOOR_ROOM_ID else room_id_2
        room_type = room_type_map[room_id]
        if room_type in PREFERRED_ROOMS_TO_OUTSIDE:
            doors_to_outside.append((room_id_1, room_id_2))
        if n_doors_target == len(doors_to_outside):
            return doors_to_outside
    if len(doors_to_outside) >= MIN_DOORS_TO_OUTSIDE:
        return doors_to_outside

    # NOTE: Check non preferred room types
    for room_id_1, room_id_2 in outdoor_candidates:
        room_id = room_id_1 if room_id_2 == OUTDOOR_ROOM_ID else room_id_2
        room_type = room_type_map[room_id]
        if room_type not in PREFERRED_ROOMS_TO_OUTSIDE:
            doors_to_outside.append((room_id_1, room_id_2))
        if n_doors_target == len(doors_to_outside):
            return doors_to_outside

    return doors_to_outside
