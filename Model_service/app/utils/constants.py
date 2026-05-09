import os
from pathlib import Path

import yaml

def get_root_path():
    return Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT_PATH = get_root_path()
CONFIG_PATH = ROOT_PATH / "configs"

config = yaml.load(open(f"{CONFIG_PATH}/config.yaml", "r", encoding="utf-8"), Loader=yaml.FullLoader)
LLM_API_TIMEOUT = 300