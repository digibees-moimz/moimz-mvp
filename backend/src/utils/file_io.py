import json
import os


def load_json(path: str, default=None) -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default or {}


def save_json(path: str, data: dict, indent: int = 2):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=indent)
