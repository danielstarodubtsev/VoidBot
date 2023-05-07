import json
import os
from typing import Any


class ConfigHandler:
    def __init__(self):
        self._config = set()

    def load_data(self, file_name: str) -> None:
        if not os.path.exists(f"./{file_name}"):
            raise FileNotFoundError("FATAL ERROR: Impossible to load config from file {file_name} because it doesn't exist")

        with open(file_name, "r") as config_file:
            self._config = json.load(config_file)

    def save_data(self, file_name: str, indent: int = 2) -> None:
        with open(file_name, "w") as config_file:
            config_file.write(json.dumps(self._config, indent=indent))

    def get_attribute(self, attribute: str) -> object:
        return self._config[attribute]
    
    def set_attribute(self, attribute: str, value: object) -> None:
        self._config[attribute] = value