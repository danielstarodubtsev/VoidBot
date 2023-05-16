import json
import os

from copy import deepcopy

from scripts.utils import Utils

class UserDataHandler:
    """
    A class used for all work with the user data - points, wins, referral system, etc.
    Stores data locally in json files
    """

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
                               "unlocked_achievements": [],
                               "event_points": 0}

    def __len__(self) -> int:
        return len(self._user_data)

    def _reset_referral_code(self) -> None:
        """
        Resets the referral code attribute in _default_entry
        """
        
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
        with open(file_name, "r") as user_data_file:
            self._user_data = json.load(user_data_file)

    def save_data(self, file_name: str, indent: int = 2) -> None:
        """
        Saves the data to the given file
        """

        with open(file_name, "w") as save_file:
            save_file.write(json.dumps(self._user_data, indent=indent))

    def is_in_database(self, id: int) -> bool:
        """
        Checks if an entry with the given ID exists
        """

        return str(id) in self._user_data
    
    def get_user_info(self, id: int) -> dict:
        """
        Fetches the info assigned to the given ID
        """

        if not self.is_in_database(id):
            raise Exception(f"User with id <{id}> isn't in the database")
        
        return self._user_data[str(id)]
    
    def get_attribute(self, id: int, attribute: str) -> object:
        """
        Fetches a praticular attribute of the given entry by ID
        """

        return self.get_user_info(id)[attribute]
    
    def delete_entry(self, id: int) -> None:
        """
        Deletes an entry given by ID
        """

        del self._user_data[str(id)]

    def add_entry_if_needed(self, id: int) -> None:
        """
        Adds a new entry to the database
        """

        if self.is_in_database(id):
            return
        
        self._user_data[str(id)] = deepcopy(self._default_entry)
        self._reset_referral_code()

    def reset_entry(self, id: int) -> None:
        """
        Resets a given entry to a default one
        """

        if not self.is_in_database(id):
            raise Exception("User with id <{id}> isn't in the database")
        
        self._user_data[str(id)] = deepcopy(self._default_entry)
        self._reset_referral_code()
        
    def sort_database(self, by_attribute: str, reverse: bool = True) -> None:
        """
        Sortes the database by a given parameter
        """

        sorted_user_data = list(self._user_data.items())
        sorted_user_data.sort(key=lambda elem: elem[1][by_attribute], reverse=reverse)
        sorted_user_data = {item[0]: item[1] for item in sorted_user_data}

        self._user_data = sorted_user_data

    def reset_attribute(self, attribute: str) -> None:
        """
        Resets a particular attribute for all entries of the database
        """

        for id in self._user_data:
            self._user_data[id][attribute] = self._default_entry[attribute]

    def set_attribute(self, id: int, attribute: str, value: object) -> None:
        """
        Sets a particular attribute to a particular value
        """

        self._user_data[str(id)][attribute] = value

    def list_ids(self) -> list[str]:
        """
        Returnes the list of all ID's in the order they appear in the database
        """

        return [int(id) for id in self._user_data]