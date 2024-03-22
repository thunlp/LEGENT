from huggingface_hub import snapshot_download
from legent.utils.config import MODEL_FOLDER
from legent import load_json, store_json


def download_model(repo_id, token=None):
    local_dir = f"{MODEL_FOLDER}/base/{repo_id.split('/')[-1]}"
    snapshot_download(
        repo_id=repo_id,
        token=token,
        ignore_patterns=["*.md", ".gitattributes", "*.h5"],
        local_dir=local_dir,
        local_dir_use_symlinks=False,
    )


def set_vision_tower_to_local():
    config_file = f"{MODEL_FOLDER}/base/llava-v1.5-7b/config.json"
    config = load_json(config_file)
    config['mm_vision_tower'] = f"{MODEL_FOLDER}/base/clip-vit-large-patch14-336"
    store_json(config, config_file)


download_model("openai/clip-vit-large-patch14-336")
download_model("liuhaotian/llava-v1.5-7b")
set_vision_tower_to_local()
