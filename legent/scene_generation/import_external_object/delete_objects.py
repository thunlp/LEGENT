import argparse
import json
import os
from legent.environment.env_utils import get_default_env_data_path
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--asset", type=str)

args = parser.parse_args()


ENV_DATA_PATH = Path(f"{get_default_env_data_path()}/procthor")

def find_addressable(asset,addressables):
    path = ENV_DATA_PATH / "addressables.json"
    for i in range(len(addressables["prefabs"])):
        if addressables["prefabs"][i]["name"] == asset:
            return i
    return -1
def delete_addressables(asset):
    path = ENV_DATA_PATH / "addressables.json"
    with open(path, "r") as f:
        addressables = json.load(f)
    idx = find_addressable(asset,addressables)
    if idx != -1:
        del addressables["prefabs"][idx]
        with open(path, "w") as f:
            json.dump(addressables, f, indent=4)

def delete_object_dict(asset):
    path = ENV_DATA_PATH / "object_dict.json"
    with open(path, "r") as f:
        object_dict = json.load(f)
    for k,v in object_dict.items():
        if asset in v:
            v.remove(asset)
    with open(path, "w") as f:
        json.dump(object_dict, f, indent=4)

def delete_name_to_type(asset):
    path = ENV_DATA_PATH / "object_name_to_type.json"
    with open(path, "r") as f:
        name_to_type = json.load(f)
    del name_to_type[asset]
    with open(path, "w") as f:
        json.dump(name_to_type, f, indent=4)



delete_addressables(args.asset)
delete_object_dict(args.asset)
delete_name_to_type(args.asset)

