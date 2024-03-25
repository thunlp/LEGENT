import os
import pkg_resources

# Get the installation directory of the package
package_path = pkg_resources.resource_filename("legent", "")
# Construct the path to the resource
resource_path = os.path.join(package_path, os.pardir, ".legent")
resource_path = os.path.abspath(resource_path)

ENV_DATA_FOLDER = f"{resource_path}/env/env_data"
CLIENT_FOLDER = f"{resource_path}/env/client"
SCENES_FOLDER = f"{resource_path}/scenes"
TASKS_FOLDER = f"{resource_path}/tasks"
DATASET_FOLDER = f"{resource_path}/dataset"
MODEL_FOLDER = f"{resource_path}/models"
EVAL_FOLDER = f"{resource_path}/eval"
