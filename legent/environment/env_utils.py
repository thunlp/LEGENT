import glob
import os
import subprocess
from sys import platform
from typing import Optional, List
from legent.utils.io import log, log_green, get_latest_folder
from legent.utils.config import CLIENT_FOLDER, ENV_DATA_FOLDER
import zipfile


def get_platform():
    """
    returns the platform of the operating system : linux, darwin or win32
    """
    return platform


def validate_environment_path(env_path: str) -> Optional[str]:
    """
    Strip out executable extensions of the env_path
    :param env_path: The path to the executable
    """
    env_path = env_path.strip().replace(".app", "").replace(".exe", "").replace(".x86_64", "").replace(".x86", "")
    true_filename = os.path.basename(os.path.normpath(env_path))

    if not (glob.glob(env_path) or glob.glob(env_path + ".*")):
        return None

    cwd = os.getcwd()
    launch_string = None
    true_filename = os.path.basename(os.path.normpath(env_path))
    if get_platform() == "linux" or get_platform() == "linux2":
        candidates = glob.glob(os.path.join(cwd, env_path) + ".x86_64")
        if len(candidates) == 0:
            candidates = glob.glob(os.path.join(cwd, env_path, "*.x86_64"))
        if len(candidates) == 0:
            candidates = glob.glob(os.path.join(cwd, env_path) + ".x86")
        if len(candidates) == 0:
            candidates = glob.glob(env_path + ".x86_64")
        if len(candidates) == 0:
            candidates = glob.glob(env_path + ".x86")
        if len(candidates) == 0:
            if os.path.isfile(env_path):
                candidates = [env_path]
        if len(candidates) > 0:
            launch_string = candidates[0]

    elif get_platform() == "darwin":
        candidates = glob.glob(os.path.join(cwd, env_path + ".app", "Contents", "MacOS", true_filename))
        if len(candidates) == 0:
            candidates = glob.glob(os.path.join(env_path + ".app", "Contents", "MacOS", true_filename))
        if len(candidates) == 0:
            candidates = glob.glob(os.path.join(cwd, env_path + ".app", "Contents", "MacOS", "*"))
        if len(candidates) == 0:
            candidates = glob.glob(os.path.join(env_path + ".app", "Contents", "MacOS", "*"))
        if len(candidates) > 0:
            launch_string = candidates[0]
    elif get_platform() == "win32":
        candidates = glob.glob(os.path.join(cwd, env_path + ".exe"))
        if len(candidates) == 0:
            candidates = glob.glob(env_path + ".exe")
        if len(candidates) == 0:
            # Look for e.g. 3DBall\UnityEnvironment.exe
            crash_handlers = set(glob.glob(os.path.join(cwd, env_path, "UnityCrashHandler*.exe")))
            candidates = [c for c in glob.glob(os.path.join(cwd, env_path, "*.exe")) if c not in crash_handlers]
        if len(candidates) > 0:
            launch_string = candidates[0]
    return launch_string


def launch_executable(file_name: str, args: List[str]) -> subprocess.Popen:
    """
    Launches a Unity executable and returns the process handle for it.
    :param file_name: the name of the executable
    :param args: List of string that will be passed as command line arguments
    when launching the executable.
    """
    launch_string = validate_environment_path(file_name)
    if launch_string is None:
        raise Exception("EnvironmentException:\n" f"Couldn't launch the {file_name} environment. Provided filename does not match any environments.")
    else:
        # Launch Unity environment
        subprocess_args = [launch_string] + args
        # std_out_option = DEVNULL means the outputs will not be displayed on terminal.
        # std_out_option = None is default behavior: the outputs are displayed on terminal.
        std_out_option = subprocess.DEVNULL
        try:
            return subprocess.Popen(
                subprocess_args,
                # start_new_session=True means that signals to the parent python process
                # (e.g. SIGINT from keyboard interrupt) will not be sent to the new process on POSIX platforms.
                # This is generally good since we want the environment to have a chance to shutdown,
                # but may be undesirable in come cases; if so, we'll add a command-line toggle.
                # Note that on Windows, the CTRL_C signal will still be sent.
                start_new_session=True,
                stdout=std_out_option,
                stderr=std_out_option,
            )
        except PermissionError as perm:
            # This is likely due to missing read or execute permissions on file.
            raise Exception("EnvironmentException:\n" f"Error when trying to launch environment - make sure " f"permissions are set correctly. For example " f'"chmod -R 755 {launch_string}"') from perm


def download_file(url, file_path):
    import requests
    from tqdm import tqdm

    folder_path, _ = os.path.split(file_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    with open(file_path, "wb") as file, tqdm(
        desc=file_path,
        total=total_size,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)


def download_env(from_tsinghua_cloud=False, download_env_data=False, download_dev_version=False):
    import requests

    if from_tsinghua_cloud:
        if download_dev_version:
            share_key = "806b350ea72c4bf4ba51"
        else:
            share_key = "9976c807e6e04e069377"
        res = requests.get(f"https://cloud.tsinghua.edu.cn/api/v2.1/share-links/{share_key}/dirents/")
        files = [item["file_name"] for item in res.json()["dirent_list"]]
    else:
        from huggingface_hub import list_repo_files

        if download_dev_version:
            repo_name = "LEGENT/LEGENT-environment-dev"
        else:
            repo_name = "LEGENT/LEGENT-environment-Alpha"
        files = list_repo_files(repo_name)

    if get_platform() == "linux" or get_platform() == "linux2":
        platform_name = "linux"
    elif get_platform() == "darwin":
        platform_name = "mac"
    elif get_platform() == "win32":
        platform_name = "win"
    else:
        log("Cannot decide platform. Exit.")
        return
    file_prefix = "env_data" if download_env_data else f"LEGENT-{platform_name}"
    files = [file for file in files if file.startswith(file_prefix)]
    file_name = sorted(files, reverse=True)[0]
    file_path = f"{ENV_DATA_FOLDER}/{file_name}" if download_env_data else f"{CLIENT_FOLDER}/{file_name}"
    if from_tsinghua_cloud:
        link = f"https://cloud.tsinghua.edu.cn/d/{share_key}/files/?p={file_name}&dl=1"
    else:
        link = f"https://huggingface.co/{repo_name}/resolve/main/{file_name}?download=true"
    # log(f'download {file_name} from {link}')
    download_file(link, file_path)

    extract_to = file_path.rsplit(".", maxsplit=1)[0]
    # log(f'extract {file_path} to {extract_to}')
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    if platform_name != "win":
        mode = 0o777
        for root, dirs, files in os.walk(extract_to):
            os.chmod(root, mode)
            for file in files:
                os.chmod(os.path.join(root, file), mode)
    env_path = os.path.abspath(extract_to).replace("\\", "/")
    log_prefix = "environment data" if download_env_data else "LEGENT environment client"
    log_green(f"{log_prefix} is saved to <g>{env_path}</g>.")


def get_default_env_path(root_folder=CLIENT_FOLDER):
    return get_latest_folder(root_folder)


env_data_path = None


def get_default_env_data_path():
    global env_data_path
    if not env_data_path:
        env_data_path = get_latest_folder(ENV_DATA_FOLDER)
    return env_data_path
