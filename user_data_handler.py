import json
import os

from discord_utils import DiscordUtils
from utils import Utils

class UserDataHandler:
    def __init__(self):
        self._user_data = set()
        self._default_entry = {"weekly_points": 0,
                               "monthly_points": 0,
                               "total_points": 0,
                               "weekly_wins": 0,
                               "monthly_wins": 0,
                               "total_wins": 0,
                               "referral_code": Utils.generate_referral_code(),
                               "referrals": [],
                               "commander": None,
                               "unlocked_achievements": []}

    def _reset_referral_code(self) -> None:
        self._default_entry["referral_code"] = Utils.generate_referral_code()

    def load_data(self, file_name: str) -> None:
        """
        Loads the user data from the given file
        """
        
        # If the user data file doesn't exist we create it and fill with an empty json object
        if not os.path.exists(f"./{file_name}"):
            with open(file_name, "w") as user_data_file:
                user_data_file.write(json.dumps(dict(), indent=2))
        
        # Read the data from json file
        with open(file_name) as user_data_file:
            self._user_data = json.load(user_data_file)

    def save_data(self, file_name: str, indent: int = 2) -> None:
        with open(file_name, "w") as save_file:
            save_file.write(json.dumps(self._user_data, indent=indent))

    def is_in_database(self, id: int) -> bool:
        return str(id) in self._user_data
    
    def get_user_info(self, id: int) -> dict:
        if not self.is_in_database(id):
            raise Exception(f"User with id <{id}> isn't in the database")
        
        return self._user_data[str(id)]
    
    def get_attribute(self, id: int, attribute: str) -> object:
        return self.get_user_info(id)[attribute]
    
    def delete_entry(self, id: int) -> None:
        del self._user_data[str(id)]

    def add_entry(self, id: int) -> None:
        if self.is_in_database(id):
            raise Exception("User with id <{id}> is already in the database")
        
        self._user_data[str(id)] = self._default_entry
        self._reset_referral_code()

    def add_entry_if_needed(self, id: int) -> None:
        if self.is_in_database(id):
            return
        
        self._user_data[str(id)] = self._default_entry
        self._reset_referral_code()

    def reset_entry(self, id: int) -> None:
        if not self.is_in_database(id):
            raise Exception("User with id <{id}> isn't in the database")
        
        self._user_data[str(id)] = self._default_entry
        self._reset_referral_code()
        
    def sort_database(self, by_attribute: str, reverse: bool = True) -> None:
        sorted_user_data = list(self._user_data.items())
        sorted_user_data.sort(key=lambda elem: elem[1][by_attribute], reverse=reverse)
        sorted_user_data = {item[0]: item[1] for item in sorted_user_data}

        self._user_data = sorted_user_data

    def reset_attribute(self, attribute: str) -> None:
        for id in self._user_data:
            self._user_data[id] = self._default_entry[attribute]

    def set_attribute(self, id: int, attribute: str, value: object) -> None:
        self._user_data[str(id)][attribute] = value

    def list_ids(self) -> list[str]:
        return [int(id) for id in self._user_data]
    
    def get_number_of_entries(self) -> int:
        return len(self._user_data)