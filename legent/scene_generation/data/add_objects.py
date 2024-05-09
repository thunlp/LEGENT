import argparse
import json
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--type", type=str, choices=["asset", "asset_type"], required=True)
parser.add_argument("--asset_type", type=str, required=True)
parser.add_argument("--asset", type=str)
# inKitchens
parser.add_argument("--inKitchens", type=int)
# inLivingRooms
parser.add_argument("--inLivingRooms", type=int)
# inBedrooms
parser.add_argument("--inBedrooms", type=int)
# inBathrooms
parser.add_argument("--inBathrooms", type=int)
# onFloor
parser.add_argument("--onFloor", type=bool)
# multiplePerRoom
parser.add_argument("--multiplePerRoom", type=bool)

args = parser.parse_args()
args.asset_type = args.asset_type.lower()


def add_to_addressables(data):
    with open("addressables.json", "r") as f:
        addressables = json.load(f)
    if data not in addressables["prefabs"]:
        addressables["prefabs"].append(data)
    else:
        assert ValueError(f"asset already exists in addressables")
    with open("addressables.json", "w") as f:
        json.dump(addressables, f, indent=4)


def add_to_object_dict(name, type):
    with open("object_dict.json", "r") as f:
        object_dict = json.load(f)
    if type not in object_dict:
        assert ValueError(f"{type} not in object_dict, please add asset_type first!")
    if name not in object_dict[type]:
        object_dict[type].append(name)
    else:
        assert ValueError(f"{name} already exists in object_dict")
    with open("object_dict.json", "w") as f:
        json.dump(object_dict, f, indent=4)


def add_to_name_to_type(name, type):
    with open("object_name_to_type.json", "r") as f:
        name_to_type = json.load(f)
    if name not in name_to_type:
        name_to_type[name] = type
    else:
        assert ValueError(f"{name} already exists in name_to_type")
    with open("object_name_to_type.json", "w") as f:
        json.dump(name_to_type, f, indent=4)


def add_asset_type(asset_type, args):
    with open("object_dict.json", "r") as f:
        object_dict = json.load(f)
    if asset_type not in object_dict:
        object_dict[asset_type] = []
    else:
        assert ValueError(f"{asset_type} already exists in object_dict")
    with open("object_dict.json", "w") as f:
        json.dump(object_dict, f, indent=4)

    df = pd.read_csv("placement_annotations.csv")
    # add one row
    df = df.append(
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
    df.to_csv("placement_annotations.csv", index=False)


if args.type == "asset":
    assert args.asset is not None

    with open(args.asset, "r") as f:
        data = json.load(f)
    asset_name = data["name"]

    add_to_addressables(asset_name)
    add_to_object_dict(asset_name, args.asset_type)
    add_to_name_to_type(asset_name, args.asset_type)

elif args.type == "asset_type":
    assert all(
        [
            args.inKitchens,
            args.inLivingRooms,
            args.inBedrooms,
            args.inBathrooms,
            args.onFloor,
            args.multiplePerRoom,
        ]
    )
    asset_type = args.asset_type
    add_asset_type(asset_type, args)
