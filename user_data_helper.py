import json
from random import choice

input("Press enter to run")



with open("user_data.json", "r") as json_file:
    data = json.load(json_file)

for elem in data:
    data[elem]["event_points"] = 0

with open("user_data.json", "w") as json_file:
    json_file.write(json.dumps(data, indent=2))

