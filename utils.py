from typing import Dict
import os
import json
import yaml

def config_read():
    config_path = "./config.yaml"
    fo = open(config_path, "r", encoding="utf-8")
    res = yaml.load(fo, Loader=yaml.FullLoader)

    return res

def return_config():
    config = config_read()
    return config["LOG"], config["SERVER"], config["LLM"], config["TOKEN"]

def load_tokens(
    token_file: str
):
    if os.path.exists(token_file):
        with open(token_file, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

def save_tokens(
    tokens: Dict,
    token_file: str
):
    with open(token_file, "w", encoding="utf-8") as file:
        json.dump(tokens, file, ensure_ascii=False)