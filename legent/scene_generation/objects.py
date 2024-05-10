import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Tuple
from legent.environment.env_utils import get_default_env_data_path


class ObjectDB:
    def __init__(self, PLACEMENT_ANNOTATIONS, OBJECT_DICT: Dict[str, List[str]], MY_OBJECTS: Dict[str, List[str]], OBJECT_TO_TYPE: Dict[str, str], PREFABS: Dict[str, Any], RECEPTACLES: Dict[str, Any], KINETIC_AND_INTERACTABLE_INFO: Dict[str, Any], ASSET_GROUPS: Dict[str, Any], FLOOR_ASSET_DICT: Dict, PRIORITY_ASSET_TYPES: Dict[str, List[str]]):
        import pandas as pd
        self.PLACEMENT_ANNOTATIONS: pd.DataFrame = PLACEMENT_ANNOTATIONS
        self.OBJECT_DICT: Dict[str, List[str]] = OBJECT_DICT
        self.MY_OBJECTS: Dict[str, List[str]] = MY_OBJECTS
        self.OBJECT_TO_TYPE: Dict[str, str] = OBJECT_TO_TYPE
        self.PREFABS: Dict[str, Any] = PREFABS
        self.RECEPTACLES: Dict[str, Any] = RECEPTACLES
        self.KINETIC_AND_INTERACTABLE_INFO: Dict[str, Any] = KINETIC_AND_INTERACTABLE_INFO
        self.ASSET_GROUPS: Dict[str, Any] = ASSET_GROUPS
        self.FLOOR_ASSET_DICT: Dict[Tuple[str, str], Tuple[Dict[str, Any], pd.DataFrame]] = FLOOR_ASSET_DICT
        self.PRIORITY_ASSET_TYPES: Dict[str, List[str]] = PRIORITY_ASSET_TYPES
        

ENV_DATA_PATH = None
def get_data_path():
    global ENV_DATA_PATH
    if ENV_DATA_PATH is None:
        ENV_DATA_PATH = f"{get_default_env_data_path()}/procthor"
        # ENV_DATA_PATH = r'D:\code\LEGENT\LEGENT\legent\scene_generation\data'
    return ENV_DATA_PATH

def _get_place_annotations():
    import pandas as pd
    filepath = os.path.join(get_data_path(), "placement_annotations.csv")
    df = pd.read_csv(filepath, index_col=0)
    df.index.set_names("assetType", inplace=True)
    return df


def _get_object_dict():
    filepath = os.path.join(get_data_path(), "object_dict.json")
    return json.load(open(filepath))


def _get_my_objects():
    filepath = os.path.join(get_data_path(), "my_objects.json")
    return json.load(open(filepath))


def _get_object_to_type():
    filepath = os.path.join(get_data_path(), "object_name_to_type.json")
    return json.load(open(filepath))


def _get_prefabs():
    (
        prefabs,
        interactable_names,
        kinematic_names,
        interactable_names_set,
        kinematic_names_set,
    ) = (None, [], [], {}, {})
    json_file_path = os.path.join(get_data_path(), "addressables.json")
    with open(json_file_path, "r", encoding="utf-8") as f:
        prefabs = json.load(f)["prefabs"]
        for prefab in prefabs:
            if prefab["type"]=="interactable":
                interactable_names.append(prefab["name"])
            else:
                kinematic_names.append(prefab["name"])
        prefabs = {prefab["name"]: prefab for prefab in prefabs}
    interactable_names_set = set(interactable_names)
    kinematic_names_set = set(kinematic_names)
    return prefabs, {
        "interactable_names": interactable_names,
        "kinematic_names": kinematic_names,
        "interactable_names_set": interactable_names_set,
        "kinematic_names_set": kinematic_names_set,
    }


def _get_asset_groups():
    asset_group_path = os.path.join(get_data_path(), "asset_groups")
    asset_group_files = os.listdir(asset_group_path)
    asset_groups = {}
    for file in asset_group_files:
        file_path = os.path.join(asset_group_path, file)
        with open(file_path, "r") as f:
            asset_groups[file[: -len(".json")]] = json.load(f)
    return asset_groups


def _get_floor_assets(
    room_type: str, split: str, odb: ObjectDB
):
    import pandas as pd
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
        ]
    )
    assets: pd.DataFrame = pd.merge(assets, floor_types, on="assetType", how="left")
    assets.set_index("assetId", inplace=True)
    return floor_types, assets


def _get_default_floor_assets_from_key(key: Tuple[str, str]):
    return _get_floor_assets(*key, odb=get_default_object_db())


class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret


def _get_receptacles():
    filepath = os.path.join(get_data_path(), "receptacle.json")
    return json.load(open(filepath))


DEFAULT_OBJECT_DB = None
def get_default_object_db():
    global DEFAULT_OBJECT_DB
    if DEFAULT_OBJECT_DB is None:
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
                "Bedroom": ["bed", "pc_table"],
                "LivingRoom": ["tv", "table", "sofa"],
                "Kitchen": ["kitchen_table", "refrigerator","oven"],
                "Bathroom": ["toilet","washing_machine"],
            },
        )
    return DEFAULT_OBJECT_DB
