import json
from random import choice

input("Press enter to run")

with open("user_data.json", "r") as json_file:
    data = json.load(json_file)

symbols = "23456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"

for elem in data:
    data[elem]["referrals"] = []
    data[elem]["commander"] = "None"

with open("user_data_new.json", "w") as json_file:
    json_file.write(json.dumps(data, indent=2))
