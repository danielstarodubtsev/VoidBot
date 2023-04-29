"""
The discord VoidBot coded especially for the VOID clan in Territorial.io

Author:
    * DanTheMan (DanTheMan#9743) [id=762353710931509268]

Credit for help, ideas and suggestions:
    * Angry Ox (OX#1420) [id=515648621669122157]
    * Cyber (! Cyber™#8596) [id=778892830248009738]
    * Shef (My_Name_Is_Shef#0197) [id=139458125055918081]
    * Trinco (Trinco#2930) [id=334777399298359296]
    * John (John#6436) [id=270018062369947648]
    * Rediff/Mert (|_Mert_|#8053) [id=751377029697372220]
    * Vkij/Teinc (Teinc3#1106) [id=420725289908174859]

!!! ANY DISTRIBUTION OF THE SOURCE CODE WITHOUT DANTHEMAN'S PERMISSION IS PROHIBITED !!!
"""


import asyncio
import json
import math
import os
import random
import string
import typing

from datetime import datetime, timezone
from io import BytesIO

import discord
import requests

from discord.ext import commands, tasks
from PIL import Image, ImageDraw, ImageColor, ImageFont


CONFIG_FILE = "config.json"

# Load config
if os.path.exists(f"./{CONFIG_FILE}"):
    with open(CONFIG_FILE) as config_file:
        config = json.load(config_file)
else:
    exit("FATAL ERROR: Impossible to proceed without a config file!")

bot = commands.Bot(command_prefix=config["command_prefix"], intents=discord.Intents.all(), help_command=None)

############################################################### - UTIL FUNCTIONS - ###############################################################

def load_user_data(user_data_file_name: str) -> dict:
    """Loads the user data from the given file"""
    
    if not os.path.exists(f"./{user_data_file_name}"):
        with open(user_data_file_name, "w") as user_data_file:
            user_data_file.write(json.dumps(dict(), indent=2))
        
    with open(user_data_file_name) as user_data_file:
        user_data = json.load(user_data_file)

    return user_data

def save_data(save_user_data: bool = True, save_config: bool = True) -> None:
    """Saves all the data to json files"""

    if save_user_data:
        with open(config["user_data_file"], "w") as user_data_file:
            user_data_file.write(json.dumps(user_data, indent=2))

    if save_config:
        with open(CONFIG_FILE, "w") as config_file:
            config_file.write(json.dumps(config, indent=2))

def sort_user_data(user_data: dict, by: str, reverse: bool = True) -> dict:
    """Returns the sorted user_data"""

    sorted_user_data = list(user_data.items())
    sorted_user_data.sort(key=lambda elem: elem[1][by], reverse=reverse)
    sorted_user_data = {elem[0]: elem[1] for elem in sorted_user_data}

    return sorted_user_data

def init_user_if_needed(user_id: str) -> None:
    """Adds a new user to the user_data if it doesn't already exist"""

    if user_id in user_data:
        return

    user_data[user_id] = {"weekly_points": 0,
                            "monthly_points": 0,
                            "total_points": 0,
                            "weekly_wins": 0,
                            "monthly_wins": 0,
                            "total_wins": 0,
                            "referral_code": generate_referral_code(),
                            "referrals": [],
                            "commander": None,
                            "unlocked_achievements": []}

    save_data(save_config=False)

def reset_leaderboard(leaderboard_type: str) -> None:
    """Resets a particular leaderboard"""

    if leaderboard_type == "weekly":
        for user_id in user_data:
            user_data[user_id]["weekly_points"] = 0
            user_data[user_id]["weekly_wins"] = 0

    elif leaderboard_type == "monthly":
        for user_id in user_data:
            user_data[user_id]["monthly_points"] = 0
            user_data[user_id]["monthly_wins"] = 0

    elif leaderboard_type == "total":
        for user_id in user_data:
            user_data[user_id]["total_points"] = 0
            user_data[user_id]["total_wins"] = 0

    save_data(save_config=False)

def create_embed_for_top(top: int, by: str, title: str) -> discord.Embed:
    """Returnes a discord.Embed object for the given top"""

    leaderboard = [user_info for user_info in list(sort_user_data(user_data=user_data, by=by).items()) if bot.get_guild(config["server_id"]).get_member(int(user_info[0]))][:top]
    leaderboard = {elem[0]: elem[1] for elem in leaderboard}

    embed_text = ""
    for index, user_id in enumerate(leaderboard, start=1):
        member = bot.get_guild(config["server_id"]).get_member(int(user_id))

        match index:
            case 1:
                place = ":first_place:"
            case 2:
                place = ":second_place:"
            case 3:
                place = ":third_place:"
            case _:
                place = f"{index}."

        embed_text += f"{place} {member.display_name}: {':coin:' if by != 'total_wins' else ''} {int(leaderboard[user_id][by])}\n"

    return discord.Embed(color=discord.Color.blue(), title=title, description=embed_text)

def generate_referral_code(length: int = 10) -> str:
    """Generates a new random referral code of given length"""

    symbols = string.ascii_lowercase + string.ascii_uppercase + string.digits
    code = "".join([random.choice(symbols) for _ in range(length)])

    return code

def has_any_of_the_roles(role_names: list[str]):
    """Decorator that checks whether the message author has any of the listed roles"""

    async def predicate(ctx) -> bool:
        return bool({role.name for role in ctx.author.roles} & set(role_names))
    
    return commands.check(predicate)

def update_achievements(user: discord.User) -> list[str]:
    """Updates users achievements and returns the new achievements obtained by the user"""

    user_id = str(user.id)
    
    return []

############################################################### - NON-COMMAND ASYNC FUNCTIONS - ###############################################################

async def update_rank(ctx, user: discord.User) -> str:
    """Updated user's rank. Returns the new rank if it was changed"""

    all_rank_roles = [role for role in ctx.guild.roles if role.name in config["roles_threshold"]]
    all_rank_roles.sort(key=lambda role: config["roles_threshold"][role.name])

    for rank in all_rank_roles:
        if user_data[str(user.id)]["total_points"] >= config["roles_threshold"][rank.name]:
            new_role = rank

    member = ctx.guild.get_member(user.id)

    if user_data[str(user.id)]["total_points"] < min(list(config["roles_threshold"].values())):
        return

    for rank in all_rank_roles:
        if rank in member.roles and rank != new_role:
            await member.remove_roles(rank)

    for role_name in config["other_roles_threshold"]:
        role = [role for role in ctx.guild.roles if role.name == role_name].pop()
        if user_data[str(user.id)]["total_points"] >= config["other_roles_threshold"][role_name] and role not in member.roles:
            await member.add_roles(role)

    if new_role not in member.roles:
        await member.add_roles(new_role)
        return new_role.name

async def update_user(ctx, user: discord.User) -> typing.Tuple[str, list[str]]:
    """Updates user's ranks and achievements, returnes new rank and the list of all new achievements"""

    new_rank = await update_rank(ctx, user)
    new_achievements = update_achievements(user)

    return new_rank, new_achievements

async def reset_leaderboards_if_needed() -> None:
    """Check whether a new week/month has started and resets leaderboards if needed. Additionally backups the data files every day"""

    current_weekday = datetime.isoweekday(datetime.now(timezone.utc))
    current_month = datetime.now(timezone.utc).month

    if current_weekday != config["current_weekday"]:
        config["current_weekday"] = current_weekday
        if current_weekday == 1:
            reset_leaderboard(leaderboard_type="weekly")
        
        await backup_data()

    if current_month != config["current_month"]:
        config["current_month"] = current_month
        reset_leaderboard(leaderboard_type="monthly")

    save_data(save_user_data=False)

async def show_message(ctx, message_title, message_text: str) -> None:
    """Shows a message"""

    embed = discord.Embed(color=discord.Color.orange(), title=message_title, description=message_text)

    await ctx.send(embed=embed)

async def manipulate_points(ctx, amounts: list[float], users: list[discord.User]) -> None:
    """Gives the user a certain amount of points"""

    await reset_leaderboards_if_needed()
    
    value = ""

    result_amounts = []
    for amount, user in zip(amounts, users):
        user_id = str(user.id)
        member = ctx.guild.get_member(int(user_id))

        if user_data[user_id]["weekly_points"] + amount < 0 or user_data[user_id]["monthly_points"] + amount < 0:
            await show_message(ctx=ctx, message_title="Error!", message_text="Negative points are not allowed")
            return

        amount_with_mult = math.ceil(amount * config["multiplier"] if amount > 0 else amount)
        result_amounts.append(amount_with_mult)

        value += f"""{"Added" if amount_with_mult >= 0 else "Removed"} **{abs(amount_with_mult)}** points {"to" if amount_with_mult >= 0 else "from"} {member.display_name}
**Weekly: {user_data[user_id]["weekly_points"]} -> {user_data[user_id]["weekly_points"] + amount_with_mult}
Monthly: {user_data[user_id]["monthly_points"]} -> {user_data[user_id]["monthly_points"] + amount_with_mult}
Total: {user_data[user_id]["total_points"]} -> {user_data[user_id]["total_points"] + amount_with_mult}**\n"""

        user_data[user_id]["weekly_points"] += amount_with_mult
        user_data[user_id]["monthly_points"] += amount_with_mult
        user_data[user_id]["total_points"] += amount_with_mult

        if user_data[user_id]["total_points"] >= config["commander_threshold"]:
            commander_id = user_data[user_id]["commander"]

            if commander_id:
                user_data[user_id]["commander"] = None
                user_data[commander_id]["referrals"].remove(user_id)

        if abs(amount) >= 10:
            user_data[user_id]["weekly_wins"] += amount / abs(amount)
            user_data[user_id]["monthly_wins"] += amount / abs(amount)
            user_data[user_id]["total_wins"] += amount / abs(amount)

        new_rank, new_achievements = await update_user(ctx, user)
        save_data(save_config=False)
        
        if new_rank:
            value += f"{member.display_name} ranked {'up' if amount_with_mult > 0 else 'down'} to {new_rank}\n"
        if new_achievements:
            pass

    with open("points_logs.txt", "r") as points_logs_file:
        lines = (points_logs_file.readlines() + [f"{[user.id for user in users]} - {result_amounts}\n"])[-500:]

    with open("points_logs.txt", "w") as points_logs_file:
        points_logs_file.write("".join(lines))

    embed = discord.Embed(color=discord.Color.green(), description=value)
    await ctx.send(embed=embed)

async def backup_data() -> None:
    """Backs up all the data to additional json files and sends to the channel given by config["backup_channel_id"]"""

    backup_channel = bot.get_channel(config["backup_channel_id"])
    await backup_channel.send(datetime.now(timezone.utc), file=discord.File(config["user_data_file"]))

############################################################### - LOOP FUNCTIONS - ###############################################################

@tasks.loop(minutes=7)
async def update_leaderboards_in_special_channel() -> None:
    """Updated leaderboards in the leaderboard channel every seven minutes (to avoid being rate-limited)"""

    weekly_lb_embed = create_embed_for_top(top=50, by="weekly_points", title="Weekly leaderboard")
    monthly_lb_embed = create_embed_for_top(top=50, by="monthly_points", title="Monthly leaderboard")
    all_time_lb_embed = create_embed_for_top(top=50, by="total_points", title="All time leaderboard")

    lb_channel = bot.get_channel(config["leaderboard_channel_id"])

    weekly_lb_message = await lb_channel.fetch_message(config["weekly_leaderboard_id"])
    monthly_lb_message = await lb_channel.fetch_message(config["monthly_leaderboard_id"])
    all_time_lb_message = await lb_channel.fetch_message(config["all_time_leaderboard_id"])

    await weekly_lb_message.edit(embed=weekly_lb_embed)
    await monthly_lb_message.edit(embed=monthly_lb_embed)
    await all_time_lb_message.edit(embed=all_time_lb_embed)

############################################################### - REGULAR BOT COMMANDS - ###############################################################

@bot.command()
@commands.has_role(config["member_role"])
async def g(ctx, amount: int) -> None:
    """Gives the user who ran the command a certain amount of points"""

    user_id = str(ctx.author.id)
    init_user_if_needed(user_id=user_id)

    if amount <= 0:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values are allowed")
        return

    if user_data[user_id]["commander"]:
        commander = bot.get_user(int(user_data[user_id]["commander"]))
        await manipulate_points(ctx=ctx, amounts=[1.1 * amount, .1 * amount], users=[ctx.author, commander])
        return

    await manipulate_points(ctx=ctx, amounts=[amount], users=[ctx.author])

@bot.command()
@commands.has_role(config["member_role"])
async def cg(ctx, amount: int, *users: discord.User) -> None:
    """Gives a certain amount of points to multiple users"""

    if amount <= 0:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values are allowed")
        return

    percentages = [1, .8, .7, .6, .5, .4, .3] + [.25] * 50
    amounts = []
    result_users = []

    for index, user in enumerate(users):
        user_id = str(user.id)
        init_user_if_needed(user_id=user_id)

        if not user_data[user_id]["commander"]:
            amounts.append(amount * percentages[index])
            result_users.append(user)
        else:
            amounts.append(amount * percentages[index] * 1.1)
            amounts.append(amount * percentages[index] * .1)
            result_users.append(user)
            result_users.append(bot.get_user(int(user_data[user_id]["commander"])))

    await reset_leaderboards_if_needed()

    await manipulate_points(ctx=ctx, amounts=amounts, users=result_users)

@bot.command()
@commands.has_role(config["member_role"])
async def d(ctx, amount: int, *users: discord.User) -> None:
    """Distributes the points equally between listed users"""

    if amount <= 0:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values are allowed")
        return

    percentages = [1 / len(users)] * len(users)
    amounts = []
    result_users = []

    for index, user in enumerate(users):
        user_id = str(user.id)
        init_user_if_needed(user_id=user_id)

        if not user_data[user_id]["commander"]:
            amounts.append(amount * percentages[index])
            result_users.append(user)
        else:
            amounts.append(amount * percentages[index] * 1.1)
            amounts.append(amount * percentages[index] * .1)
            result_users.append(user)
            result_users.append(bot.get_user(int(user_data[user_id]["commander"])))

    await reset_leaderboards_if_needed()

    await manipulate_points(ctx=ctx, amounts=amounts, users=result_users)

@bot.command()
@commands.has_role(config["member_role"])
async def bal(ctx, user: discord.User = None) -> None:
    """Lets a user check how many points and wins they or another user have"""

    if user is None:
        user = bot.get_user(ctx.author.id)

    user_id = str(user.id)
    init_user_if_needed(user_id=user_id)

    member = ctx.guild.get_member(int(user_id))

    weekly_points = user_data[user_id]["weekly_points"]
    monthly_points = user_data[user_id]["monthly_points"]
    total_points = user_data[user_id]["total_points"]

    weekly_points_place = [user_info[0] for user_info in list(sort_user_data(user_data=user_data, by="weekly_points").items()) if bot.get_user(int(user_info[0]))].index(user_id) + 1
    monthly_points_place = [user_info[0] for user_info in list(sort_user_data(user_data=user_data, by="monthly_points").items()) if bot.get_user(int(user_info[0]))].index(user_id) + 1
    total_points_place = [user_info[0] for user_info in list(sort_user_data(user_data=user_data, by="total_points").items()) if bot.get_user(int(user_info[0]))].index(user_id) + 1

    weekly_wins = user_data[user_id]["weekly_wins"]
    monthly_wins = user_data[user_id]["monthly_wins"]
    total_wins = user_data[user_id]["total_wins"]

    weekly_wins_place = list(sort_user_data(user_data=user_data, by="weekly_wins").keys()).index(user_id) + 1
    monthly_wins_place = list(sort_user_data(user_data=user_data, by="monthly_wins").keys()).index(user_id) + 1
    total_wins_place = list(sort_user_data(user_data=user_data, by="total_wins").keys()).index(user_id) + 1

    embed = discord.Embed(title=f"{member.display_name}", color=discord.Color.dark_blue())
    embed = embed.add_field(name="This week", value=f"Points: {weekly_points} (#{weekly_points_place})\nWins: {int(weekly_wins)} (#{weekly_wins_place})")
    embed = embed.add_field(name="This month", value=f"Points: {monthly_points} (#{monthly_points_place})\nWins: {int(monthly_wins)} (#{monthly_wins_place})")
    embed = embed.add_field(name="All time", value=f"Points: {total_points} (#{total_points_place})")
    embed = embed.add_field(name="Win count", value=f"Total wins since 23 jan 2023: {int(total_wins)} (#{total_wins_place})")

    await ctx.send(embed=embed)

@bot.command()
@commands.has_role(config["member_role"])
async def picbal(ctx, user: discord.User = None) -> None:
    """later"""

    WIDTH = 1270
    HEIGHT = 700

    corner_circle_radius = 30
    background_color = (32, 34, 37, 255)
    transparent_color = (0, 0, 0, 0)
    header_font = ImageFont.truetype("verdana.ttf", 40)
    clan_name_font = ImageFont.truetype("verdana.ttf", 30)

    if user is None:
        user = bot.get_user(ctx.author.id)

    user_id = str(user.id)
    init_user_if_needed(user_id=user_id)

    member = ctx.guild.get_member(int(user_id))

    pfp = user.display_avatar
    await pfp.to_file(filename="test.png")

    progress_bar_img = Image.new("RGBA", (WIDTH, HEIGHT), color=transparent_color)
    drawer = ImageDraw.Draw(progress_bar_img)

    # Preparing stuff
    name_to_display = member.display_name + (f"#{user.discriminator}" if member.display_name == user.display_name else "")
    pfp_url = user.avatar
    image_data = requests.get(pfp_url).content
    pfp_image = Image.open(BytesIO(image_data))
    pfp_image = pfp_image.resize((90, 90))

    guild_icon_url = ctx.guild.icon
    image_data = requests.get(guild_icon_url).content
    guild_icon_image = Image.open(BytesIO(image_data))
    guild_icon_image = guild_icon_image.resize((35, 35))

    # Filling the background while leaving rounded corners
    drawer.rounded_rectangle((0, 0, WIDTH, HEIGHT), fill=background_color, radius=corner_circle_radius)

    # Placing the stuff in the top left corner
    progress_bar_img.paste(pfp_image, (20, 20))
    progress_bar_img.paste(guild_icon_image, (125, 75))
    drawer.text((125, 20), text=name_to_display, align="left", font=header_font, stroke_width=1)
    drawer.text((165, 73), text=ctx.guild.name, align="left", font=clan_name_font, fill=(166, 166, 166))


    progress_bar_img.save("cache_image_bal.png")

    with open("cache_image_bal.png", "rb") as pic_file:
        await ctx.send(file=discord.File(pic_file))
    
    os.remove("cache_image_bal.png")

@bot.command()
@commands.has_role(config["member_role"])
async def top(ctx, top: int, by: str = "total_points", title: str = None) -> None:
    """Shows the top X players"""

    if top > 30:
        await show_message(ctx=ctx, message_title="Error!", message_text=f"Cannot display more than 30 players")
        return
    
    if top < 1:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values allowed")
        return

    if not title:
        title = f"Top {top} {config['clan_tag']} players"

    if by == "weekly":
        by = "weekly_points"
    elif by == "monthly":
        by = "monthly_points"
    elif by == "wins":
        by = "total_wins"

    embed = create_embed_for_top(top=top, by=by, title=title)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_role(config["member_role"])
async def lb(ctx, user: discord.User = None) -> None:
    """Shows the player's position on the leaderboard and several players around them"""

    if not user:
        user = bot.get_user(ctx.author.id)

    user_id = str(user.id)
    lb = [user_info for user_info in list(sort_user_data(user_data=user_data, by="total_points").items()) if bot.get_user(int(user_info[0]))]
    lb = {elem[0]: elem[1] for elem in lb}
    keys = list(lb.keys())
    user_pos = keys.index(user_id)

    embed_text = ""
    for pos in range(user_pos + 4, user_pos - 6, -1):
        if not 0 <= pos < len(lb):
            continue

        if pos + 1 == 1:
            place = ":first_place:"
        elif pos + 1 == 2:
            place = ":second_place:"
        elif pos + 1 == 3:
            place = ":third_place:"
        else:
            place = f"{pos + 1}."
        
        member = bot.get_guild(config["server_id"]).get_member(int(keys[pos]))

        if pos == user_pos:
            embed_text = f"**{place} {member.display_name}: :coin: {lb[keys[pos]]['total_points']}**\n" + embed_text
        else:
            embed_text = f"{place} {member.display_name}: :coin: {lb[keys[pos]]['total_points']}\n" + embed_text

    embed = discord.Embed(title="Leaderboard", color=discord.Color.blue(), description=embed_text)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_role(config["member_role"])
async def code(ctx, user: discord.User = None) -> None:
    """Shows a message with the user's referral code"""

    if not user:
        user = bot.get_user(ctx.author.id)

    user_id = str(user.id)
    code = user_data[user_id]["referral_code"]

    if user_data[user_id]["total_points"] < config["commander_threshold"]:
        await show_message(ctx=ctx, message_title="Error!", message_text=f"You need to earn at least {config['commander_threshold']} points before a referral code is assigned to you")
        return
    
    await show_message(ctx=ctx, message_title="Success!", message_text=f"The referral code is {code}")

@bot.command()
@commands.has_role(config["member_role"])
async def usecode(ctx, code: str) -> None:
    """Allows a user to use a referral code, if possible"""

    user_id = str(ctx.author.id)
    init_user_if_needed(user_id=user_id)

    if user_data[user_id]["total_points"] >= config["referral_threshold"]:
        await show_message(ctx=ctx, message_title="Error!", message_text=f"You can only use a referral code if you have less than {config['referral_threshold']} points")
        return
    
    for possible_commander_id in user_data:
        if user_data[possible_commander_id]["referral_code"] == code:
            if user_id not in user_data[possible_commander_id]["referrals"]:
                user_data[possible_commander_id]["referrals"].append(user_id)
            user_data[user_id]["commander"] = possible_commander_id
            save_data(save_config=False)
            await show_message(ctx=ctx, message_title="Success!", message_text=f"Now {ctx.guild.get_member(int(possible_commander_id)).display_name} is your commander")
            break
    else:
        await show_message(ctx=ctx, message_title="Error!", message_text="No member with such referral code found")
        return

@bot.command()
@commands.has_role(config["member_role"])
async def referrals(ctx, user: discord.User = None) -> None:
    """Allows to see all the referrals"""

    if user is None:
        user = bot.get_user(ctx.author.id)

    user_id = str(user.id)

    referrals = [ctx.guild.get_member(int(referral_id)).display_name for referral_id in user_data[user_id]["referrals"] if ctx.guild.get_member(int(referral_id))]

    if referrals:
        await show_message(ctx=ctx, message_title="Success!", message_text=f"The referrals are {', '.join(referrals)}")
        return
    
    await show_message(ctx=ctx, message_title="Error!", message_text="No referrals found")

@bot.command()
@commands.has_role(config["member_role"])
async def help(ctx) -> None:
    """Shows all the commands of the bot"""

    help_text = f"""**BASIC COMMANDS**
{config["command_prefix"]}g (points) - give the user who used the command a certain amount of points
{config["command_prefix"]}cg (points) (user1) [user2] ... [userN] - gives all listed users a certain amount of points
{config["command_prefix"]}d (points) (user1) [user2] ... [userN] - distibutes the points equally between mentioned users
{config["command_prefix"]}bal [user] - shows the user's balance. By default the user is the one who ran the command
{config["command_prefix"]}top (X) [keyword] - shows the top X players by <keyword> where keyword may be "weekly", "monthly" or "wins". By default will show the all-time top
{config["command_prefix"]}lb [user] - shows the user's position on the leaderboard and several players around them. By default the user is the one who ran the command
{config["command_prefix"]}code [user] - shows the user's referral code. By default the user is the one who ran the command. Only available to members with at least {config["commander_threshold"]} points
{config["command_prefix"]}usecode (code) - uses a referral code. Only available to members with less than {config["referral_threshold"]} points
{config["command_prefix"]}referrals [user] - shows the list of the user's referrals. By default the user is the one who ran the command
{config["command_prefix"]}help - shows this window

**STAFF-ONLY COMMANDS**
{config["command_prefix"]}a (points) (user) - gives the user a certain amount of points
{config["command_prefix"]}r (points) (user) - removes a certain amount of points from the user
{config["command_prefix"]}mult (multiplier) - sets the points multiplier
{config["command_prefix"]}rwp (amount) (user) - removes weekly points from the user (doesn't affect monthly/total points)
{config["command_prefix"]}rmp (amount) (user) - removes monthly points from the user (doesn't affect weekly/total points)
{config["command_prefix"]}undo - revertes the last points-related command used by any user (except rwp and rmp commands)"""

    embed = discord.Embed(title="All VoidBot commands", color=discord.Color.dark_gold(), description=help_text)
    await ctx.send(embed=embed)

############################################################### - STAFF-ONLY BOT COMMANDS - ###############################################################

@bot.command()
@commands.has_role(config["member_role"])
@has_any_of_the_roles(config["staff_roles"])
async def a(ctx, amount: int, user: discord.User) -> None:
    """Adds a certain amount of points to any user"""

    user_id = str(user.id)
    init_user_if_needed(user_id=user_id)

    if amount <= 0:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values are allowed")
        return

    if user_data[user_id]["commander"]:
        commander = bot.get_user(int(user_data[user_id]["commander"]))
        await manipulate_points(ctx=ctx, amounts=[1.1 * amount, .1 * amount], users=[user, commander])
        return

    await manipulate_points(ctx=ctx, amounts=[amount], users=[user])

@bot.command()
@commands.has_role(config["member_role"])
@has_any_of_the_roles(config["staff_roles"])
async def r(ctx, amount: int, user: discord.User) -> None:
    """Removes a certain amount of points from any user"""

    if amount <= 0:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values are allowed")
        return
    
    await manipulate_points(ctx=ctx, amounts=[-amount], users=[user])

@bot.command()
@commands.has_role(config["member_role"])
@has_any_of_the_roles(config["staff_roles"])
async def mult(ctx, multiplier: float) -> None:
    """Sets a point multiplier (for 2x events etc.)"""

    if multiplier <= 0:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values are allowed")
        return

    await show_message(ctx=ctx, message_title="Success!", message_text=f"The points multiplier is now {multiplier}")

    config["multiplier"] = multiplier
    save_data(save_user_data=False)

@bot.command()
@commands.has_role(config["member_role"])
@has_any_of_the_roles(config["staff_roles"])
async def rwp(ctx, amount: int, user: discord.User) -> None:
    """Removes weekly points from user. Doesn't affect monthly/total points"""

    user_id = str(user.id)

    await reset_leaderboards_if_needed()

    if amount > user_data[user_id]["weekly_points"]:
        await show_message(ctx=ctx, message_title="Error!", message_text="The user doesn't have enough points")
        return

    member = ctx.guild.get_member(user.id)

    embed_text = f"""Removed **{amount}** weekly points from {member.display_name}
**Weekly: {user_data[user_id]["weekly_points"]} -> {user_data[user_id]["weekly_points"] - amount}
Monthly: {user_data[user_id]["monthly_points"]} -> {user_data[user_id]["monthly_points"]}
Total: {user_data[user_id]["total_points"]} -> {user_data[user_id]["total_points"]}**"""

    user_data[user_id]["weekly_points"] -= amount

    embed = discord.Embed(color=discord.Color.green(), title=member.display_name, description=embed_text)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_role(config["member_role"])
@has_any_of_the_roles(config["staff_roles"])
async def rmp(ctx, amount: int, user: discord.User) -> None:
    """Removes monthly points from user. Doesn't affect weekly/total points"""

    user_id = str(user.id)

    await reset_leaderboards_if_needed()

    if amount > user_data[user_id]["monthly_points"]:
        await show_message(ctx=ctx, message_title="Error!", message_text="The user doesn't have enough points")
        return

    member = ctx.guild.get_member(user.id)

    embed_text = f"""Removed **{amount}** monthly points from {member.display_name}
**Weekly: {user_data[user_id]["weekly_points"]} -> {user_data[user_id]["weekly_points"]}
Monthly: {user_data[user_id]["monthly_points"]} -> {user_data[user_id]["monthly_points"] - amount}
Total: {user_data[user_id]["total_points"]} -> {user_data[user_id]["total_points"]}**"""

    user_data[user_id]["monthly_points"] -= amount

    embed = discord.Embed(color=discord.Color.green(), title=member.display_name, description=embed_text)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_role(config["member_role"])
@has_any_of_the_roles(config["staff_roles"])
async def undo(ctx) -> None:
    "Revertes the last points-related command used by any user"

    with open("points_logs.txt", "r") as points_logs_file:
        lines = points_logs_file.readlines()

    last_action = lines.pop(-1)
    ids = list(map(int, last_action.split(" - ")[0].replace("[", "").replace("]", "").split(", ")))
    users = [bot.get_user(id) for id in ids]
    amounts = list(map(lambda elem: -int(float(elem)), last_action.split(" - ")[1].replace("[", "").replace("]", "").split(", ")))

    await manipulate_points(ctx=ctx, amounts=amounts, users=users)

    with open("points_logs.txt", "w") as points_logs_file:
        points_logs_file.write("".join(lines))

############################################################### - ON_EVENT ACTIONS - ###############################################################

@bot.event
async def on_ready() -> None:
    """on_ready set ups"""

    print("READY")
    update_leaderboards_in_special_channel.start()

############################################################### - ARCHIVED COMMANDS AND FUNCTIONS - ###############################################################

'''
async def update_rank_special(ctx, member) -> str:
    """Updated user's rank. Returns the new rank if it was changed"""

    all_rank_roles = [role for role in ctx.guild.roles if role.name in config["roles_threshold"]]
    all_rank_roles.sort(key=lambda role: config["roles_threshold"][role.name])

    for rank in all_rank_roles:
        if user_data[str(member.id)]["total_points"] >= config["roles_threshold"][rank.name]:
            new_role = rank

    if user_data[str(member.id)]["total_points"] < min(list(config["roles_threshold"].values())):
        return

    for rank in all_rank_roles:
        if rank in member.roles and rank != new_role:
            await member.remove_roles(rank)

    vc_approved_role = [role for role in ctx.guild.roles if role.name == "VC approved"][0]
    if user_data[str(member.id)]["total_points"] >= config["VC_approved_role_threshold"] and vc_approved_role not in member.roles:
        await member.add_roles(vc_approved_role)

    if new_role not in member.roles:
        await member.add_roles(new_role)
        return new_role.name

@bot.command()
@commands.has_role(config["staff_role"])
async def update_all_members(ctx):
    all_members = ctx.guild.members

    for member in all_members:
        if str(member.id) in user_data:
            print(member.display_name)
            await update_rank_special(ctx=ctx, member=member)

    print("finished")

async def play_sound() -> None:
    """Doesn't work"""

    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(1)
        now = datetime.now()
        if now.minute == 0 or now.minute == 14 or now.minute == 44 or now.minute == 59 or now.minute == 37:
            print(0)
            vc = bot.voice_clients[0]
            source = discord.FFmpegPCMAudio(SOUND_FILE)
            vc.play(source, after=lambda e: print('Error:', e) if e else None)
            await asyncio.sleep(60)


@bot.command()
@commands.has_role(config["staff_role"])
async def launch_leaderboards(ctx) -> None:
    """Use for first-ever leaderboards setup in special channel"""
    
    channel = ctx.channel

    weekly_lb_embed = create_embed_for_top(top=50, by="weekly_points", title="Weekly leaderboard")
    monthly_lb_embed = create_embed_for_top(top=50, by="monthly_points", title="Monthly leaderboard")
    all_time_lb_embed = create_embed_for_top(top=50, by="total_points", title="All time leaderboard")

    await channel.send(embed=weekly_lb_embed)
    await channel.send(embed=monthly_lb_embed)
    await channel.send(embed=all_time_lb_embed)

'''

############################################################### - MAIN PART - ###############################################################

if __name__ == "__main__":
    user_data = load_user_data(config["user_data_file"])
    bot.run(config["token"])

############################################################### - TODO - ###############################################################

"""
TODO:
    - ...
    - ...
"""
