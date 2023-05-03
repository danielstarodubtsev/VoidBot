# Description
This is a custom implementation of a points bot - a bot that lets server members track their contribution into the clan, add themselves and other members points and wins, view weekly/monthly/all-time leaderboards. The bot automatically gives members new ranks and roles that are unlocked upon gaining a certain amount of points.

# Setup
1) Create a new application at https://discord.com/developers/applications
2) Set the profile picture, bio, tags etc. This step is optional
3) Make sure to enable all types of intents in the "Bot" tab (i.e. presence intent, server members intent and message content intent)
4) Add the bot to your server using the URL generator
5) Create a "config.json" file in the same directory as your main.py file is in (on an online hosting or on a local PC). Note: if for some reason you want the confiuration file to be named differently, you have to change the CONFIG_FILE variable assignment in the beginning of the code
6) A sample config is given in this repository, but you will definitely need to change some of the fields. That is:
    "token" - replace with the token that was generated for you on the discord developer portal
    "command_prefix" - set to whatever command prefix you prefer. Default (and recommended) one is the exclamation mark
    "clan_tag" - set to whatever your clan tag is
    "user_data_file" - no need to change unless you want your user database file to be named differently
    "member_role" - set to whatever the name the clan member role has in your server
    "staff_roles" - list all the roles that are staff in your server. These roles will have the permission to run the bot staff-only commands
    "server_id" - set the id of your server
    "leaderboard_channel_id" - set to the id of the channel in which you want to have the monthly/weekly/all-time top 50 lists of players, updated every several minutes
    id's of the messages containing the leaderboards. For the first ever setup, just send any three messages in the channel and insert their id's here. the messages will later be edited to become the               leaderboards
    You don't need to change several of the following parameters. Remember to set the "current_weekday" and "current_month" though (counting starts at 1, i.e. january is the 1st month and Monday is the first       day of the week
    "roles_threshold" - list the ranks that you have in your clan with the number of points needed to reach each rank. Note that when a user reaches a particular rank, they lose all the lower ranks (except the     first one, which should be identical to "member_role" and have a threshold of 1.
    "other_roles_threshold" - list any other roles that are given to members upon reaching a certain amount of points. Here, obtaining one of the roles doesn't affect the rest of them, so if you want your           members to keep all their ranks instead of only having the highest one, you can list the ranks here.
7) Setup is finished! The bot is ready to be used (run the help command to get more info on each bot command). Note that after the setup is finished, the directory with the bot should ALWAYS contain the following files:
    "config.json" - the config you already learnt about
    "default_discord_pfp.png" - a .png image of a discord default profile picture needed to display the balance of the users than don't have a profile picture
    "main.py" - the bot script itself. Can be renamed
    "points_logs.txt" - a file created by the bot automatically that logs the last 500 points-related actions done by any user. Use this file in urgent situations caused by the bot being abused. Read about the     file structure below
    "user_data.json" - a file containing all the user database
    
"points_logs.txt" file structure:
the file contains lines of the format "[id_1, id_2, ... id_n] - [amount_1, amount_2, ... amount_n]. Each line represents an action done to the points. For example a line "[123, 456, 789] - [10, 20, 30]" means that the user with id "123" gained 10 points, the user with id "456" gained 20 points and the user with id "789" gained 30 points.
