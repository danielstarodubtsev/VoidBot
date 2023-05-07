import json
import os


class ConfigHandler:
    def __init__(self):
        self._config = set()

    def load_config(self, file_name: str) -> None:
        if not os.path.exists(f"./{file_name}"):
            raise FileNotFoundError("Impossible to load config from file {file_name} because it doesn't exist")
        
        with open(file_name) as config_file:
            self._config = json.load(config_file)