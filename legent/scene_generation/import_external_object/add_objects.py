import argparse
import json
import os
from pathlib import Path

import pandas as pd

from legent.environment.env_utils import get_default_env_data_path

ENV_DATA_PATH = Path(f"{get_default_env_data_path()}/procthor")
# ENV_DATA_PATH = Path(r"D:\code\LEGENT\LEGENT\legent\scene_generation\data")

parser = argparse.ArgumentParser()
parser.add_argument("--type", type=str, choices=["asset", "asset_type"], required=True)
parser.add_argument("--asset_type", type=str, required=True)
parser.add_argument("--asset", type=str)
# inKitchens
parser.add_argument("--inKitchens", type=int, default=2)
# inLivingRooms
parser.add_argument("--inLivingRooms", type=int, default=2)
# inBedrooms
parser.add_argument("--inBedrooms", type=int, default=2)
# inBathrooms
parser.add_argument("--inBathrooms", type=int, default=2)
# onFloor
parser.add_argument("--onFloor", type=bool, default=True)
# multiplePerRoom
parser.add_argument("--multiplePerRoom", type=bool, default=True)

args = parser.parse_args()
args.asset_type = args.asset_type.lower()


def get_mesh_size(input_file):
    """Get the bounding box of a mesh file.
    Args:
        input_file: str, the path of the mesh file.
    Returns:
        mesh_size: np.ndarray, the size of the mesh file.
    """

    import trimesh

    mesh = trimesh.load(input_file)
    min_vals, max_vals = mesh.bounds[0], mesh.bounds[1]
    return max_vals - min_vals

def add_to_addressables(asset):
    path = ENV_DATA_PATH / "addressables.json"
    with open(path, "r") as f:
        addressables = json.load(f)
    size = get_mesh_size(asset)

    data = {
        'name': asset,
        'size':{
            'x': size[0],
            'y': size[1],
            'z': size[2]
        },
        "placeable_surfaces": [
            {
                "y": size[1] / 2,
                "x_min": -size[0] / 2,
                "z_min": -size[2] / 2,
                "x_max": size[0] / 2,
                "z_max": size[2] / 2,
            }
        ],
        "type": "kinematic"
    }
    if data not in addressables["prefabs"]:
        addressables["prefabs"].append(data)
    else:
        assert ValueError(f"{asset} already exists in addressables")
    with open(path, "w") as f:
        json.dump(addressables, f, indent=4)


def add_to_object_dict(name, type):
    path = ENV_DATA_PATH / "object_dict.json"
    with open(path, "r") as f:
        object_dict = json.load(f)
    if type not in object_dict:
        assert ValueError(f"{type} not in object_dict, please add asset_type first!")
    if name not in object_dict[type]:
        object_dict[type].append(name)
    else:
        assert ValueError(f"{name} already exists in object_dict")
    with open(path, "w") as f:
        json.dump(object_dict, f, indent=4)


def add_to_name_to_type(name, type):

    path = ENV_DATA_PATH / "object_name_to_type.json"
    with open(path, "r") as f:
        name_to_type = json.load(f)
    if name not in name_to_type:
        name_to_type[name] = type
    else:
        assert ValueError(f"{name} already exists in name_to_type")
    with open(path, "w") as f:
        json.dump(name_to_type, f, indent=4)


def add_asset_type(asset_type, args):
    path = ENV_DATA_PATH / "object_dict.json"
    with open(path, "r") as f:
        object_dict = json.load(f)
    if asset_type not in object_dict:
        object_dict[asset_type] = []
    else:
        assert ValueError(f"{asset_type} already exists in object_dict")
    with open(path, "w") as f:
        json.dump(object_dict, f, indent=4)

    path = ENV_DATA_PATH / "placement_annotations.csv"
    df = pd.read_csv(path)
    # add one row
    new_row = pd.Series(
        {
            "Object": asset_type,
            "inKitchens": args.inKitchens,
            "inLivingRooms": args.inLivingRooms,
            "inBedrooms": args.inBedrooms,
            "inBathrooms": args.inBathrooms,
            "onFloor": args.onFloor,
            "multiplePerRoom": args.multiplePerRoom,
            "onEdge": True,
            "inMiddle": True,
            "inCorner": True,
        }
    )
    df.loc[len(df)] = new_row
    df.to_csv(path, index=False)

    path = ENV_DATA_PATH / "receptacle.json"
    with open(path, "r") as f:
        data = json.load(f)
    for k, v in data.items():
        v[asset_type] = 2
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


if args.type == "asset":

    assert os.path.exists(args.asset), f"{args.asset} does not exist"
    asset = args.asset

    add_to_addressables(asset)
    add_to_object_dict(asset, args.asset_type)
    add_to_name_to_type(asset, args.asset_type)

elif args.type == "asset_type":
    asset_type = args.asset_type
    add_asset_type(asset_type, args)
