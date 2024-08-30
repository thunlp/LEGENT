"""
This script demonstrates how to get spatial relations between objects in the scene.
Currently, the spatial relations include "on_what" and "in_what".
"""
from legent import Environment, ResetInfo, load_json
from legent.environment.env_utils import get_default_env_data_path
from legent.action.api import GetSpatialRelations

# load the default scene
scene = load_json(f"{get_default_env_data_path()}/scene-default.json")
env = Environment(env_path=None)

try:
    obs = env.reset(ResetInfo(scene, api_calls=[GetSpatialRelations()]))
    info = obs.api_returns["object_relations"]
    print(info)
    car_id, table_id = 104, 114
    assert info[car_id]["on_what"] == table_id

    while True:
        obs = env.step()
finally:
    env.close()
