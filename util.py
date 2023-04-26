import json
from random import choice

input("Press enter to run")

with open("user_data.json", "r") as json_file:
    data = json.load(json_file)

symbols = "23456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"

for elem in data:
    if data[elem]["commander"] == "None":
        data[elem]["commander"] = None

with open("user_data.json", "w") as json_file:
    json_file.write(json.dumps(data, indent=2))
