import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Tuple, Union

import pandas as pd
from attr import define

from legent.environment.env_utils import get_default_env_data_path


@define
class ObjectDB:
    PLACEMENT_ANNOTATIONS: pd.DataFrame
    OBJECT_DICT: Dict[str, List[str]]
    MY_OBJECTS: Dict[str, List[str]]
    OBJECT_TO_TYPE: Dict[str, str]
    PREFABS: Dict[str, Any]
    RECEPTACLES: Dict[str, Any]
    KINETIC_AND_INTERACTABLE_INFO: Dict[str, Any]
    ASSET_GROUPS: Dict[str, Any]
    FLOOR_ASSET_DICT: Dict[Tuple[str, str], Tuple[Dict[str, Any], pd.DataFrame]]
    PRIORITY_ASSET_TYPES: Dict[
        str, List[str]
    ]  # These objects should be placed first inside of the rooms.


def _get_place_annotations():
    # filepath = os.path.join(f"{get_default_env_data_path()}/procthor", "placement_annotations_extended.csv")
    filepath = os.path.join(f"{get_default_env_data_path()}/procthor","placement_annotations_latest.csv")
    # filepath = os.path.join(f"{get_default_env_data_path()}/procthor", "placement_annotations_filtered.csv")
    df = pd.read_csv(filepath, index_col=0)
    df.index.set_names("assetType", inplace=True)
    return df


def _get_object_dict():
    filepath = os.path.join(f"{get_default_env_data_path()}/procthor", "object_dict_filtered_new.json")
    return json.load(open(filepath))


def _get_my_objects():
    filepath = os.path.join(f"{get_default_env_data_path()}/procthor", "my_objects.json")
    return json.load(open(filepath))


def _get_object_to_type():
    filepath = os.path.join(f"{get_default_env_data_path()}/procthor", "object_name_to_type.json")
    return json.load(open(filepath))


def _get_prefabs():
    DEFAULT_FLOOR_PREFAB = "LowPolyInterior_Floor_01"
    DEFAULT_WALL_PREFAB = "LowPolyInterior_WallFloor1_09"
    (
        prefabs,
        interactable_names,
        kinematic_names,
        interactable_names_set,
        kinematic_names_set,
    ) = (None, [], [], {}, {})
    dirname = os.path.dirname(__file__)
    json_file_path = os.path.join(f"{get_default_env_data_path()}/procthor", "addressables.json")
    # json_file = pkg_resources.resource_filename(__name__, json_file_path)
    with open(json_file_path, "r", encoding="utf-8") as f:
        prefabs = json.load(f)["prefabs"]
        for prefab in prefabs:
            if prefab["type"]=="interactable":
                interactable_names.append(prefab["name"])
            else:
                if prefab["name"] not in {DEFAULT_FLOOR_PREFAB, DEFAULT_WALL_PREFAB}:
                    kinematic_names.append(prefab["name"])
        prefabs = {prefab["name"]: prefab for prefab in prefabs}
    interactable_names_set = set(interactable_names)
    kinematic_names_set = set(kinematic_names)
    # print(prefabs)
    return prefabs, {
        "interactable_names": interactable_names,
        "kinematic_names": kinematic_names,
        "interactable_names_set": interactable_names_set,
        "kinematic_names_set": kinematic_names_set,
    }


def _get_asset_groups():
    dirname = os.path.dirname(__file__)
    asset_group_path = os.path.join(f"{get_default_env_data_path()}/procthor", "asset_groups")
    asset_group_files = os.listdir(asset_group_path)
    asset_groups = {}
    for file in asset_group_files:
        file_path = os.path.join(asset_group_path, file)
        with open(file_path, "r") as f:
            asset_groups[file[: -len(".json")]] = json.load(f)
    return asset_groups


def _get_floor_assets(
    room_type: str, split: str, odb: ObjectDB
) -> Tuple[Any, pd.DataFrame]:
    # print(odb.PLACEMENT_ANNOTATIONS.head())
    # print(odb.OBJECT_DICT.keys())
    floor_types = odb.PLACEMENT_ANNOTATIONS[
        odb.PLACEMENT_ANNOTATIONS["onFloor"]
        & (odb.PLACEMENT_ANNOTATIONS[f"in{room_type}s"] > 0)
    ]
    assets = pd.DataFrame(
        [
            {
                "assetId": asset_name,
                "assetType": asset_type,
                "xSize": odb.PREFABS[asset_name]["size"]["x"],
                "ySize": odb.PREFABS[asset_name]["size"]["y"],
                "zSize": odb.PREFABS[asset_name]["size"]["z"],
            }
            for asset_type in floor_types.index
            for asset_name in odb.OBJECT_DICT[asset_type]
            # for asset in odb.PREFABS[asset_name]
        ]
    )
    # print(assets.head())
    # print(floor_types.head())
    assets = pd.merge(assets, floor_types, on="assetType", how="left")
    # assets = assets[assets["split"].isin([split, None])]
    assets.set_index("assetId", inplace=True)
    return floor_types, assets


def _get_default_floor_assets_from_key(key: Tuple[str, str]):
    return _get_floor_assets(*key, odb=DEFAULT_OBJECT_DB)


class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret


def _get_receptacles():
    filepath = os.path.join(f"{get_default_env_data_path()}/procthor", "recptacle_score2.json")
    return json.load(open(filepath))


DEFAULT_OBJECT_DB = ObjectDB(
    PLACEMENT_ANNOTATIONS=_get_place_annotations(),
    OBJECT_DICT=_get_object_dict(),
    MY_OBJECTS=_get_my_objects(),
    OBJECT_TO_TYPE=_get_object_to_type(),
    PREFABS=_get_prefabs()[0],
    RECEPTACLES=_get_receptacles(),
    KINETIC_AND_INTERACTABLE_INFO=_get_prefabs()[1],
    ASSET_GROUPS=_get_asset_groups(),
    FLOOR_ASSET_DICT=keydefaultdict(_get_default_floor_assets_from_key),
    PRIORITY_ASSET_TYPES={
        "Bedroom": ["bed", "dresser"],
        "LivingRoom": ["television", "diningTable", "sofa"],
        "Kitchen": ["counterTop", "refrigerator","oven"],
        "Bathroom": ["toilet","washer"],
    },
)
