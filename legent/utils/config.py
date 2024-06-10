import os
import importlib.util

# Get the installation directory of the package
package_name = "legent"
package_path = importlib.util.find_spec(package_name).submodule_search_locations[0]

# Construct the path to the resource
resource_path = os.path.join(package_path, os.pardir, ".legent")
resource_path = os.path.abspath(resource_path)

ENV_FOLDER = f"{resource_path}/env"
ENV_DATA_FOLDER = f"{ENV_FOLDER}/env_data"
CLIENT_FOLDER = f"{ENV_FOLDER}/client"
SCENES_FOLDER = f"{resource_path}/scenes"
TASKS_FOLDER = f"{resource_path}/tasks"
DATASET_FOLDER = f"{resource_path}/dataset"
MODEL_FOLDER = f"{resource_path}/models"
EVAL_FOLDER = f"{resource_path}/eval"
PACKED_FOLDER = f"{resource_path}/packed_scenes"


DEFAULT_GRPC_PORT = 50051
