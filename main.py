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


import math
import os

from datetime import datetime, timezone
from io import BytesIO

from config_handler import ConfigHandler
from user_data_handler import UserDataHandler
from utils import DiscordUtils, Utils

import discord
import requests

from discord.ext import commands, tasks
from PIL import Image, ImageDraw, ImageFont


CONFIG_FILE = "config.json"

config = ConfigHandler()
config.load_data(CONFIG_FILE)

bot = commands.Bot(command_prefix=config.get_attribute("command_prefix"), intents=discord.Intents.all(), help_command=None)

############################################################### - UTIL FUNCTIONS - ###############################################################

def create_embed_for_top(top: int, by: str, title: str) -> discord.Embed:
    """
    Returnes a discord.Embed object for the given top
    """

    guild = bot.get_guild(config.get_attribute("server_id"))

    user_data.sort_database(by)
    ids = [id for id in user_data.list_ids() if DiscordUtils.is_user_in_guild(id, guild)][:top]
    leaderboard = {id: user_data.get_user_info(id) for id in ids}

    embed_text = ""
    for index, user_id in enumerate(leaderboard, start=1):
        member = bot.get_guild(config.get_attribute("server_id")).get_member(int(user_id))

        match index:
            case 1:
                place = ":first_place:"
            case 2:
                place = ":second_place:"
            case 3:
                place = ":third_place:"
            case _:
                place = f"{index}."

        embed_text += f"{place} {member.display_name}: {':coin:' if 'wins' not in by else ''} {int(leaderboard[user_id][by])}\n"

    return discord.Embed(color=discord.Color.blue(), title=title, description=embed_text)

def get_member_rank(member: discord.Member) -> str:
    """
    Returns the name of the member's role that represents the member's rank
    """

    for rank in config.get_attribute("roles_threshold"):
        if rank in [role.name for role in member.roles] and rank != get_ranks_list()[0]:
            return rank
    
    return config.get_attribute("member_role")

def get_ranks_list() -> list[str]:
    """
    Returns the list of all ranks names in their correct order
    """

    return list(config.get_attribute("roles_threshold").keys())

############################################################### - NON-COMMAND ASYNC FUNCTIONS - ###############################################################

async def update_user(ctx: commands.Context, user: discord.User) -> str:
    """
    Updates user's rank. Returns the new rank if it was changed
    """

    all_rank_roles = [role for role in ctx.guild.roles if role.name in config.get_attribute("roles_threshold")]
    all_rank_roles.sort(key=lambda role: config.get_attribute("roles_threshold")[role.name])

    total_points = user_data.get_attribute(user.id, "total_points")

    for rank in all_rank_roles:
        if total_points >= config.get_attribute("roles_threshold")[rank.name]:
            new_role = rank

    member = ctx.guild.get_member(user.id)

    if total_points < min(list(config.get_attribute("roles_threshold").values())):
        return

    for rank in all_rank_roles:
        if rank in member.roles and rank != new_role and rank.name != get_ranks_list()[0]:
            await member.remove_roles(rank)

    for role_name in config.get_attribute("other_roles_threshold"):
        role = [role for role in ctx.guild.roles if role.name == role_name].pop()
        if total_points >= config.get_attribute("other_roles_threshold")[role_name] and role not in member.roles:
            await member.add_roles(role)

    if new_role not in member.roles:
        await member.add_roles(new_role)
        return new_role.name

async def reset_leaderboards_if_needed() -> None:
    """
    Check whether a new week/month has started and resets leaderboards if needed
    Additionally backups the data files every day
    Additionally sends the summary of the weekly/monthly leaderboard upon reset
    """

    current_weekday = datetime.isoweekday(datetime.now(timezone.utc))
    current_month = datetime.now(timezone.utc).month

    if current_weekday != config.get_attribute("current_weekday"):
        config.set_attribute("current_weekday", current_weekday)
        if current_weekday == 1:
            await send_leaderboard_summary(leaderboard_type="weekly_points")
            user_data.reset_attribute("weekly_points")
            user_data.reset_attribute("weekly_wins")
        
        await backup_data()

    if current_month != config.get_attribute("current_month"):
        config.set_attribute("current_month", current_month)
        await send_leaderboard_summary(leaderboard_type="monthly_points")
        user_data.reset_attribute("monthly_points")
        user_data.reset_attribute("monthly_wins")

    config.save_data(CONFIG_FILE)

async def show_message(ctx: commands.Context, message_title: str, message_text: str) -> None:
    """
    Shows a message
    """

    embed = discord.Embed(color=discord.Color.orange(), title=message_title, description=message_text)

    await ctx.send(embed=embed)

async def manipulate_points(ctx: commands.Context, amounts: list[float], users: list[discord.User]) -> None:
    """
    Gives the user a certain amount of points
    """

    await reset_leaderboards_if_needed()
    
    value = ""

    result_amounts = []
    for amount, user in zip(amounts, users):
        user_id = str(user.id)
        member = ctx.guild.get_member(user.id)

        old_weekly_points = user_data.get_attribute(user.id, "weekly_points")
        old_monthly_points = user_data.get_attribute(user.id, "monthly_points")
        old_total_points = user_data.get_attribute(user.id, "total_points")
        old_event_points = user_data.get_attribute(user.id, "event_points")

        old_weekly_wins = user_data.get_attribute(user.id, "weekly_wins")
        old_monthly_wins = user_data.get_attribute(user.id, "monthly_wins")
        old_total_wins = user_data.get_attribute(user.id, "total_wins")

        amount_with_mult = math.ceil(amount * config.get_attribute("multiplier") if amount > 0 else amount)

        new_weekly_points = old_weekly_points + amount_with_mult
        new_monthly_points = old_monthly_points + amount_with_mult
        new_total_points = old_total_points + amount_with_mult
        new_event_points = old_event_points + amount_with_mult

        if new_weekly_points < 0 or new_monthly_points < 0 or new_total_points < 0:
            await show_message(ctx=ctx, message_title="Error!", message_text="Negative points are not allowed")
            return

        result_amounts.append(amount_with_mult)

        value += f"""{"Added" if amount_with_mult >= 0 else "Removed"} **{abs(amount_with_mult)}** points {"to" if amount_with_mult >= 0 else "from"} {member.display_name}
**Weekly: {old_weekly_points} -> {new_weekly_points}
Monthly: {old_monthly_points} -> {new_monthly_points}
Total: {old_total_points} -> {new_total_points}**\n"""

        user_data.set_attribute(user.id, "weekly_points", new_weekly_points)
        user_data.set_attribute(user.id, "monthly_points", new_monthly_points)
        user_data.set_attribute(user.id, "total_points", new_total_points)
        if config.get_attribute("is_event"):
            user_data.set_attribute(user.id, "event_points", new_event_points)

        if new_total_points >= config.get_attribute("commander_threshold"):
            commander_id = user_data.get_attribute(user.id, "commander")

            if commander_id:
                referrals = user_data.get_attribute(int(commander_id), "referrals")
                referrals.remove(user_id)
                user_data.set_attribute(user.id, "commander", None)
                user_data.set_attribute(int(commander_id), "referrals", referrals)

        if abs(amount) >= 10:
            user_data.set_attribute(user.id, "weekly_wins", old_weekly_wins + amount / abs(amount))
            user_data.set_attribute(user.id, "monthly_wins", old_monthly_wins + amount / abs(amount))
            user_data.set_attribute(user.id, "total_wins", old_total_wins + amount / abs(amount))

        new_rank = await update_user(ctx, user)
        user_data.save_data(config.get_attribute("user_data_file"))
        
        if new_rank:
            value += f"{member.display_name} ranked {'up' if amount_with_mult > 0 else 'down'} to {new_rank}\n"

    with open("points_logs.txt", "r") as points_logs_file:
        lines = (points_logs_file.readlines() + [f"{[user.id for user in users]} - {result_amounts}\n"])[-500:]

    with open("points_logs.txt", "w") as points_logs_file:
        points_logs_file.write("".join(lines))

    embed = discord.Embed(color=discord.Color.green(), description=value)
    await ctx.send(embed=embed)

async def backup_data() -> None:
    """
    Sends the user_data file to the channel given by config["backup_channel_id"]
    """

    backup_channel = bot.get_channel(config.get_attribute("backup_channel_id"))
    current_datetime = datetime.now(timezone.utc)

    summary = f"""```Type: "user_data" backup
Date: {current_datetime.date()}
Time: {current_datetime.time()}
Size: {os.stat(config.get_attribute("user_data_file")).st_size} bytes
Total Members: {len(user_data)}```"""

    await backup_channel.send(summary, file=discord.File(config.get_attribute("user_data_file")))

async def send_leaderboard_summary(leaderboard_type: str) -> None:
    """
    Sends the summary of the leaderboard to the channel given by config["backup_data"]
    """

    guild = bot.get_guild(config.get_attribute("server_id"))
    channel = bot.get_channel(config.get_attribute("backup_channel_id"))
    current_datetime = datetime.now(timezone.utc)

    user_data.sort_database(leaderboard_type)

    data = [id for id in user_data.list_ids() if user_data.get_attribute(id, leaderboard_type) > 0 and DiscordUtils.is_user_in_guild(id, guild)]
    file_lines = [f"{index}. {guild.get_member(int(id)).display_name} - {user_data.get_attribute(id, leaderboard_type)}" for index, id in enumerate(data, start=1)]

    with open("cache_leaderboard_summary.txt", "w", encoding="utf-8") as cache_leaderboard_summary_file:
        cache_leaderboard_summary_file.write("\n".join(file_lines))
    
    summary = f"""```Type: leaderboard by "{leaderboard_type}" summary
Date: {current_datetime.date()}
Time: {current_datetime.time()}
Size: {os.stat("cache_leaderboard_summary.txt").st_size} bytes
Total Members Included: {len(data)}```"""

    await channel.send(summary, file=discord.File("cache_leaderboard_summary.txt"))

    os.remove("cache_leaderboard_summary.txt")

############################################################### - LOOP FUNCTIONS - ###############################################################

@tasks.loop(minutes=7)
async def update_leaderboards_in_special_channel() -> None:
    """
    Updates leaderboards in the leaderboard channel every seven minutes (to avoid being rate-limited)
    """
    
    lb_channel = bot.get_channel(config.get_attribute("leaderboard_channel_id"))

    weekly_lb_embed = create_embed_for_top(top=50, by="weekly_points", title="Weekly leaderboard")
    monthly_lb_embed = create_embed_for_top(top=50, by="monthly_points", title="Monthly leaderboard")
    all_time_lb_embed = create_embed_for_top(top=50, by="total_points", title="All time leaderboard")

    weekly_lb_message = await lb_channel.fetch_message(config.get_attribute("weekly_leaderboard_id"))
    monthly_lb_message = await lb_channel.fetch_message(config.get_attribute("monthly_leaderboard_id"))
    all_time_lb_message = await lb_channel.fetch_message(config.get_attribute("all_time_leaderboard_id"))

    await weekly_lb_message.edit(embed=weekly_lb_embed)
    await monthly_lb_message.edit(embed=monthly_lb_embed)
    await all_time_lb_message.edit(embed=all_time_lb_embed)

############################################################### - REGULAR BOT COMMANDS - ###############################################################

@bot.command(name="g")
@commands.has_role(config.get_attribute("member_role"))
async def give_points(ctx: commands.Context, amount: int) -> None:
    """
    Gives the user who ran the command a certain amount of points
    """

    user_id = ctx.author.id
    user_data.add_entry_if_needed(user_id)

    if amount <= 0:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values are allowed")
        return

    if user_data.get_attribute(user_id, "commander"):
        commander = bot.get_user(int(user_data.get_attribute(user_id, "commander")))
        await manipulate_points(ctx=ctx, amounts=[1.1 * amount, .1 * amount], users=[ctx.author, commander])
        return

    await manipulate_points(ctx=ctx, amounts=[amount], users=[ctx.author])

@bot.command(name="cg")
@commands.has_role(config.get_attribute("member_role"))
async def contest_give(ctx: commands.Context, amount: int, *users: discord.User) -> None:
    """
    Gives a certain amount of points to multiple users
    """

    if amount <= 0:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values are allowed")
        return

    percentages = [1, .8, .7, .6, .5, .4, .3] + [.25] * 50
    amounts = []
    result_users = []

    for index, user in enumerate(users):
        user_data.add_entry_if_needed(user.id)

        if not user_data.get_attribute(user.id, "commander"):
            amounts.append(amount * percentages[index])
            result_users.append(user)
        else:
            amounts.append(amount * percentages[index] * 1.1)
            amounts.append(amount * percentages[index] * .1)
            result_users.append(user)
            result_users.append(bot.get_user(int(user_data.get_attribute(user.id, "commander"))))

    await reset_leaderboards_if_needed()

    await manipulate_points(ctx=ctx, amounts=amounts, users=result_users)

@bot.command(name="d")
@commands.has_role(config.get_attribute("member_role"))
async def distribute_points(ctx: commands.Context, amount: int, *users: discord.User) -> None:
    """
    Distributes the points equally between listed users
    """

    if amount <= 0:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values are allowed")
        return

    percentages = [1 / len(users)] * len(users)
    amounts = []
    result_users = []

    for index, user in enumerate(users):
        user_data.add_entry_if_needed(user.id)

        if not user_data.get_attribute(user.id, "commander"):
            amounts.append(amount * percentages[index])
            result_users.append(user)
        else:
            amounts.append(amount * percentages[index] * 1.1)
            amounts.append(amount * percentages[index] * .1)
            result_users.append(user)
            result_users.append(bot.get_user(int(user_data.get_attribute(user.id, "commander"))))

    await reset_leaderboards_if_needed()

    await manipulate_points(ctx=ctx, amounts=amounts, users=result_users)

@bot.command(name="bal")
@commands.has_role(config.get_attribute("member_role"))
async def balance(ctx: commands.Context, user: discord.User = None) -> None:
    """
    Shows info about user, including weekly, monthly and all-time points and wins, user's position on the leaderboards and user's progress towards next ranks
    """

    temporary_loading_message = await ctx.send("Loading information about the member... Please be patient")

    WIDTH = 1270
    HEIGHT = 700

    corner_radius = 30
    background_color = (32, 34, 37, 255)
    transparent_color = (0, 0, 0, 0)
    box_color = (47, 49, 54, 255)
    light_grey = (166, 166, 166, 255)
    dark_grey = (36, 36, 36, 255)
    darker_box_color = (32, 34, 37, 255)
    darkest_box_color = (24, 26, 27, 255)
    header_font = ImageFont.truetype("verdana.ttf", 40)
    smaller_font = ImageFont.truetype("verdana.ttf", 30)
    smallest_font = ImageFont.truetype("verdana.ttf", 14)

    if user is None:
        user = bot.get_user(ctx.author.id)

    guild = bot.get_guild(config.get_attribute("server_id"))

    user_id = user.id
    user_data.add_entry_if_needed(user.id)

    member = ctx.guild.get_member(user_id)
    member_rank = get_member_rank(member)

    if member_rank != get_ranks_list()[-1]:
        next_rank = get_ranks_list()[get_ranks_list().index(member_rank) + 1]
    else:
        next_rank = member_rank

    global_member_rank = member_rank.replace("2", "1").replace("3", "1").replace("4", "1").replace("5", "1")
    if global_member_rank not in get_ranks_list()[-5:]:
        for rank in get_ranks_list()[get_ranks_list().index(global_member_rank):]:
            if not Utils.is_same_global_rank(global_member_rank, rank):
                next_global_member_rank = rank
                break
    else:
        next_global_member_rank = get_ranks_list()[-1]

    pfp = user.display_avatar
    await pfp.to_file(filename="test.png")

    progress_bar_img = Image.new("RGBA", (WIDTH, HEIGHT), color=transparent_color)
    drawer = ImageDraw.Draw(progress_bar_img)

    # Preparing stuff
    pfp_url = user.avatar
    try:
        image_data = requests.get(pfp_url).content
        pfp_image = Image.open(BytesIO(image_data))
    except: # Occurs if user doesn't have a pfp
        pfp_image = Image.open("default_discord_pfp.png")
    pfp_image = pfp_image.resize((90, 90))

    guild_icon_url = ctx.guild.icon
    image_data = requests.get(guild_icon_url).content
    guild_icon_image = Image.open(BytesIO(image_data)).resize((35, 35))

    weekly_points = user_data.get_attribute(user_id, "weekly_points")
    monthly_points = user_data.get_attribute(user_id, "monthly_points")
    total_points = user_data.get_attribute(user_id, "total_points")

    weekly_wins = int(user_data.get_attribute(user_id, "weekly_wins"))
    monthly_wins = int(user_data.get_attribute(user_id, "monthly_wins"))
    total_wins = int(user_data.get_attribute(user_id, "total_wins"))

    user_data.sort_database("weekly_points")
    weekly_points_place = [id for id in user_data.list_ids() if DiscordUtils.is_user_in_guild(id, guild)].index(user_id) + 1
    user_data.sort_database("monthly_points")
    monthly_points_place = [id for id in user_data.list_ids() if DiscordUtils.is_user_in_guild(id, guild)].index(user_id) + 1
    user_data.sort_database("total_points")
    total_points_place = [id for id in user_data.list_ids() if DiscordUtils.is_user_in_guild(id, guild)].index(user_id) + 1

    user_data.sort_database("weekly_wins")
    weekly_wins_place = [id for id in user_data.list_ids() if DiscordUtils.is_user_in_guild(id, guild)].index(user_id) + 1
    user_data.sort_database("monthly_wins")
    monthly_wins_place = [id for id in user_data.list_ids() if DiscordUtils.is_user_in_guild(id, guild)].index(user_id) + 1
    user_data.sort_database("total_wins")
    total_wins_place = [id for id in user_data.list_ids() if DiscordUtils.is_user_in_guild(id, guild)].index(user_id) + 1

    weekly_points_summary = f"{weekly_points} (#{weekly_points_place})"
    monthly_points_summary = f"{monthly_points} (#{monthly_points_place})"
    total_points_summary = f"{total_points} (#{total_points_place})"

    weekly_wins_summary = f"{weekly_wins} (#{weekly_wins_place})"
    monthly_wins_summary = f"{monthly_wins} (#{monthly_wins_place})"
    total_wins_summary = f"{total_wins} (#{total_wins_place})"

    points_text_size = (header_font.getbbox("Points")[2], header_font.getbbox("Points")[3])
    wins_text_size = (header_font.getbbox("Wins")[2], header_font.getbbox("Wins")[3])
    weekly_points_text_size = (smaller_font.getbbox(weekly_points_summary)[2], smaller_font.getbbox(weekly_points_summary)[3])
    monthly_points_text_size = (smaller_font.getbbox(monthly_points_summary)[2], smaller_font.getbbox(monthly_points_summary)[3])
    total_points_text_size = (smaller_font.getbbox(total_points_summary)[2], smaller_font.getbbox(total_points_summary)[3])
    weekly_wins_text_size = (smaller_font.getbbox(weekly_wins_summary)[2], smaller_font.getbbox(weekly_wins_summary)[3])
    monthly_wins_text_size = (smaller_font.getbbox(monthly_wins_summary)[2], smaller_font.getbbox(monthly_wins_summary)[3])
    total_wins_text_size = (smaller_font.getbbox(total_wins_summary)[2], smaller_font.getbbox(total_wins_summary)[3])

    user_data.sort_database("total_points")
    points_keys = [id for id in user_data.list_ids() if DiscordUtils.is_user_in_guild(id, guild)]
    points_user_pos = points_keys.index(user_id)
    starting_points_lb_index = max(0, points_user_pos - 3)
    ending_points_lb_index = min(starting_points_lb_index + 6, len(points_keys) - 1)

    user_data.sort_database("total_wins")
    wins_keys = [id for id in user_data.list_ids() if DiscordUtils.is_user_in_guild(id, guild)]
    wins_user_pos = wins_keys.index(user_id)
    starting_wins_lb_index = max(0, wins_user_pos - 3)
    ending_wins_lb_index = min(starting_wins_lb_index + 6, len(wins_keys) - 1)

    # Filling the background while leaving rounded corners
    drawer.rounded_rectangle((0, 0, WIDTH, HEIGHT), fill=background_color, radius=corner_radius)

    # Placing the stuff in the top left corner
    progress_bar_img.paste(pfp_image, (20, 20))
    progress_bar_img.paste(guild_icon_image, (125, 75))
    drawer.text((125, 20), text=member.display_name, font=header_font, stroke_width=1)
    drawer.text((165, 73), text=ctx.guild.name, font=smaller_font, fill=light_grey)

    # Light boxes
    drawer.rounded_rectangle((20, 129, 417, 370), fill=box_color, radius=corner_radius / 2)
    drawer.rounded_rectangle((437, 129, 834, 370), fill=box_color, radius=corner_radius / 2)
    drawer.rounded_rectangle((854, 129, 1251, 370), fill=box_color, radius=corner_radius / 2)
    drawer.rounded_rectangle((20, 390, 312, 680), fill=box_color, radius=corner_radius / 2)
    drawer.rounded_rectangle((332, 390, 625, 680), fill=box_color, radius=corner_radius / 2)
    drawer.rounded_rectangle((645, 390, 1250, 680), fill=box_color, radius=corner_radius / 2)

    # Darker boxes
    drawer.rounded_rectangle((35, 189, 402, 265), fill=darker_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((452, 189, 819, 265), fill=darker_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((869, 189, 1236, 265), fill=darker_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((35, 279, 402, 355), fill=darker_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((452, 279, 819, 355), fill=darker_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((869, 279, 1236, 355), fill=darker_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((35, 450, 297, 665), fill=darker_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((345, 450, 610, 665), fill=darker_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((660, 450, 1235, 665), fill=darker_box_color, radius=corner_radius / 4)

    # Darkest boxes
    drawer.rounded_rectangle((35, 189, 182, 265), fill=darkest_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((452, 189, 599, 265), fill=darkest_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((869, 189, 1016, 265), fill=darkest_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((35, 279, 182, 355), fill=darkest_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((452, 279, 599, 355), fill=darkest_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((869, 279, 1016, 355), fill=darkest_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((675, 465, 1220, 525), fill=darkest_box_color, radius=corner_radius / 4)
    drawer.rounded_rectangle((675, 565, 1220, 625), fill=darkest_box_color, radius=corner_radius / 4)

    # Boxes names
    drawer.text((35, 134), text="This week", font=header_font)
    drawer.text((452, 134), text="This month", font=header_font)
    drawer.text((869, 134), text="All time", font=header_font)
    drawer.text((35, 398), text="Points LB", font=smaller_font)
    drawer.text((347, 398), text="Wins LB", font=smaller_font)
    drawer.text((660, 398), text="Rank progress", font=smaller_font)

    # Text inside boxes
    drawer.text((108 - points_text_size[0] / 2, 222 - points_text_size[1] / 2), text="Points", font=header_font)
    drawer.text((525 - points_text_size[0] / 2, 222 - points_text_size[1] / 2), text="Points", font=header_font)
    drawer.text((942 - points_text_size[0] / 2, 222 - points_text_size[1] / 2), text="Points", font=header_font)
    drawer.text((108 - wins_text_size[0] / 2, 312 - wins_text_size[1] / 2), text="Wins", font=header_font)
    drawer.text((525 - wins_text_size[0] / 2, 312 - wins_text_size[1] / 2), text="Wins", font=header_font)
    drawer.text((942 - wins_text_size[0] / 2, 312 - wins_text_size[1] / 2), text="Wins", font=header_font)
    drawer.text((292 - weekly_points_text_size[0] / 2, 227 - weekly_points_text_size[1] / 2), text=weekly_points_summary, font=smaller_font)
    drawer.text((709 - monthly_points_text_size[0] / 2, 227 - monthly_points_text_size[1] / 2), text=monthly_points_summary, font=smaller_font)
    drawer.text((1126 - total_points_text_size[0] / 2, 227 - total_points_text_size[1] / 2), text=total_points_summary, font=smaller_font)
    drawer.text((292 - weekly_wins_text_size[0] / 2, 317 - weekly_wins_text_size[1] / 2), text=weekly_wins_summary, font=smaller_font)
    drawer.text((709 - monthly_wins_text_size[0] / 2, 317 - monthly_wins_text_size[1] / 2), text=monthly_wins_summary, font=smaller_font)
    drawer.text((1126 - total_wins_text_size[0] / 2, 317 - total_wins_text_size[1] / 2), text=total_wins_summary, font=smaller_font)

    # Points leaderboard
    for position in range(ending_points_lb_index, starting_points_lb_index - 1, -1):
        current_member = bot.get_guild(config.get_attribute("server_id")).get_member(int(points_keys[position]))
        display_text = f"{position + 1}. {Utils.shorten_string(current_member.display_name, 19)}: {user_data.get_attribute(current_member.id, 'total_points')}"

        fill_color = (166, 166, 166, 255) if position != points_user_pos else (255, 255, 255, 255)
        drawer.text((43, 636 - (ending_points_lb_index - position) * 30), text=display_text, font=smallest_font, fill=fill_color)

    # Wins leaderboard
    for position in range(ending_wins_lb_index, starting_wins_lb_index - 1, -1):
        current_member = bot.get_guild(config.get_attribute("server_id")).get_member(int(wins_keys[position]))
        display_text = f"{position + 1}. {Utils.shorten_string(current_member.display_name, 19)}: {int(user_data.get_attribute(current_member.id, 'total_wins'))}"

        fill_color = (166, 166, 166, 255) if position != wins_user_pos else (255, 255, 255, 255)
        drawer.text((353, 636 - (ending_wins_lb_index - position) * 30), text=display_text, font=smallest_font, fill=fill_color)

    # Progress bars
    TOTAL_BAR_LENGTH = 545
    upper_bar_length = TOTAL_BAR_LENGTH * max(0, min(1, (user_data.get_attribute(user_id, 'total_points') - config.get_attribute("roles_threshold")[member_rank]) / (config.get_attribute("roles_threshold")[next_rank] - config.get_attribute("roles_threshold")[member_rank] + 1)))
    lower_bar_length = TOTAL_BAR_LENGTH * max(0, min(1, (user_data.get_attribute(user_id, 'total_points') - config.get_attribute("roles_threshold")[global_member_rank]) / (config.get_attribute("roles_threshold")[next_global_member_rank] - config.get_attribute("roles_threshold")[global_member_rank] + 1)))
    drawer.text((675, 530), text=member_rank, font=smallest_font)
    drawer.text((1220 - smallest_font.getbbox(next_rank)[2], 530), text=next_rank, font=smallest_font)
    drawer.text((675, 630), text=global_member_rank, font=smallest_font)
    drawer.text((1220 - smallest_font.getbbox(next_global_member_rank)[2], 630), text=next_global_member_rank, font=smallest_font)
    drawer.rounded_rectangle((675, 465, 675 + upper_bar_length, 525), fill=light_grey, radius=corner_radius / 4)
    drawer.rounded_rectangle((675, 565, 675 + lower_bar_length, 625), fill=light_grey, radius=corner_radius / 4)
    upper_percentage = round(upper_bar_length / TOTAL_BAR_LENGTH * 100, 1)
    lower_percentage = round(lower_bar_length / TOTAL_BAR_LENGTH * 100, 1)
    upper_percentage_text = f"{upper_percentage}%"
    lower_percentage_text = f"{lower_percentage}%"
    if upper_percentage > 50:
        drawer.text((670 + upper_bar_length / 2 - smaller_font.getbbox(upper_percentage_text)[2] / 2, 492 - smaller_font.getbbox(upper_percentage_text)[3] / 2), text=upper_percentage_text, font=smaller_font, fill=dark_grey)
    else:
        drawer.text((670 + TOTAL_BAR_LENGTH / 2 + upper_bar_length / 2 - smaller_font.getbbox(upper_percentage_text)[2] / 2, 491 - smaller_font.getbbox(upper_percentage_text)[3] / 2), text=upper_percentage_text, font=smaller_font)
    if lower_percentage > 50:
        drawer.text((670 + lower_bar_length / 2 - smaller_font.getbbox(lower_percentage_text)[2] / 2, 592 - smaller_font.getbbox(lower_percentage_text)[3] / 2), text=lower_percentage_text, font=smaller_font, fill=dark_grey)
    else:
        drawer.text((670 + TOTAL_BAR_LENGTH / 2 + lower_bar_length / 2 - smaller_font.getbbox(lower_percentage_text)[2] / 2, 592 - smaller_font.getbbox(lower_percentage_text)[3] / 2), text=lower_percentage_text, font=smaller_font)

    progress_bar_img.save("cache_image_bal.png")

    with open("cache_image_bal.png", "rb") as pic_file:
        await temporary_loading_message.add_files(discord.File(pic_file))
        await temporary_loading_message.edit(content="")
    
    os.remove("cache_image_bal.png")

@bot.command(name="top")
@commands.has_role(config.get_attribute("member_role"))
async def top_players(ctx: commands.Context, top: int, by1: str = "points", by2: str = "total") -> None:
    """
    Shows the top X players
    """

    if top > 30:
        await show_message(ctx=ctx, message_title="Error!", message_text=f"Cannot display more than 30 players")
        return
    
    if top < 1:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values allowed")
        return
    
    by = f"{by1} {by2}"
    
    by_fix = {"points": "total_points",
              "points total": "total_points",
              "points monthly": "monthly_points",
              "points weekly": "weekly_points",
              "wins": "total_wins",
              "wins total": "total_wins",
              "wins monthly": "monthly_wins",
              "wins weekly": "weekly_wins",
              "points event": "event_points"}

    if by not in by_fix:
        await show_message(ctx=ctx, message_title="Error!", message_text=f'Unknown keywords combination "{by1}" + "{by2}"')
        return

    title = f"Top {top} {config.get_attribute('clan_tag')} players"
    by = by_fix[by]

    if by == "event_points" and not config.get_attribute("is_event"):
        await show_message(ctx=ctx, message_title="Error!", message_text="There is no event currently")
        return

    embed = create_embed_for_top(top=top, by=by, title=title)

    await ctx.send(embed=embed)

@bot.command(name="lb")
@commands.has_role(config.get_attribute("member_role"))
async def leaderboard(ctx: commands.Context, user: discord.User = None) -> None:
    """
    Shows the player's position on the leaderboard and several players around them
    """

    if not user:
        user = bot.get_user(ctx.author.id)

    user_data.sort_database("total_points")
    keys = [id for id in user_data.list_ids() if DiscordUtils.is_user_in_guild(id, ctx.guild)]
    user_pos = keys.index(user.id)

    embed_text = ""
    for pos in range(user_pos + 4, user_pos - 6, -1):
        if not 0 <= pos < len(keys):
            continue

        if pos + 1 == 1:
            place = ":first_place:"
        elif pos + 1 == 2:
            place = ":second_place:"
        elif pos + 1 == 3:
            place = ":third_place:"
        else:
            place = f"{pos + 1}."
        
        member = bot.get_guild(config.get_attribute("server_id")).get_member(int(keys[pos]))

        if pos == user_pos:
            embed_text = f"**{place} {member.display_name}: :coin: {user_data.get_attribute(keys[pos], 'total_points')}**\n" + embed_text
        else:
            embed_text = f"{place} {member.display_name}: :coin: {user_data.get_attribute(keys[pos], 'total_points')}\n" + embed_text

    embed = discord.Embed(title="Leaderboard", color=discord.Color.blue(), description=embed_text)

    await ctx.send(embed=embed)

@bot.command(name="code")
@commands.has_role(config.get_attribute("member_role"))
async def get_referral_code(ctx: commands.Context, user: discord.User = None) -> None:
    """
    Shows a message with the user's referral code
    """

    if not user:
        user = bot.get_user(ctx.author.id)

    code = user_data.get_attribute(user.id, "referral_code")
    total_points = user_data.get_attribute(user.id, "total_points")

    if total_points < config.get_attribute("commander_threshold"):
        await show_message(ctx=ctx, message_title="Error!", message_text=f"You need to earn at least {config.get_attribute('commander_threshold')} points before a referral code is assigned to you")
        return
    
    await show_message(ctx=ctx, message_title="Success!", message_text=f"The referral code is {code}")

@bot.command(name="usecode")
@commands.has_role(config.get_attribute("member_role"))
async def use_referral_code(ctx: commands.Context, code: str) -> None:
    """
    Allows a user to use a referral code, if possible
    """

    user_id = ctx.author.id
    user_data.add_entry_if_needed(user_id)

    total_points = user_data.get_attribute(user_id, "total_points")

    if total_points >= config.get_attribute("referral_threshold"):
        await show_message(ctx=ctx, message_title="Error!", message_text=f"You can only use a referral code if you have less than {config.get_attribute('referral_threshold')} points")
        return
    
    for possible_commander_id in user_data.list_ids():
        referral_code = user_data.get_attribute(possible_commander_id, "referral_code")
        referrals = user_data.get_attribute(possible_commander_id, "referrals")

        if referral_code == code:
            if user_id not in referrals:
                referrals.append(str(user_id))
                user_data.set_attribute(possible_commander_id, "referrals", referrals)

            user_data.set_attribute(user_id, "commander", possible_commander_id)
            user_data.save_data(config.get_attribute("user_data_file"))
            await show_message(ctx=ctx, message_title="Success!", message_text=f"Now {ctx.guild.get_member(int(possible_commander_id)).display_name} is your commander")
            break
    else:
        await show_message(ctx=ctx, message_title="Error!", message_text="No member with such referral code found")
        return

@bot.command(name="referrals")
@commands.has_role(config.get_attribute("member_role"))
async def get_user_referrals(ctx: commands.Context, user: discord.User = None) -> None:
    """
    Allows to see all the referrals
    """

    if user is None:
        user = bot.get_user(ctx.author.id)

    referrals = [ctx.guild.get_member(int(referral_id)).display_name for referral_id in user_data.get_attribute(user.id, "referrals") if ctx.guild.get_member(int(referral_id))]

    if referrals:
        await show_message(ctx=ctx, message_title="Success!", message_text=f"The referrals are {', '.join(referrals)}")
        return
    
    await show_message(ctx=ctx, message_title="Error!", message_text="No referrals found")

@bot.command(name="help")
@commands.has_role(config.get_attribute("member_role"))
async def help_command(ctx: commands.Context) -> None:
    """
    Shows all the commands of the bot
    """

    help_text = f"""**BASIC COMMANDS**
{config.get_attribute("command_prefix")}g (points) - give the user who used the command a certain amount of points
{config.get_attribute("command_prefix")}cg (points) (user1) [user2] ... [userN] - gives all listed users a certain amount of points
{config.get_attribute("command_prefix")}d (points) (user1) [user2] ... [userN] - distibutes the points equally between mentioned users
{config.get_attribute("command_prefix")}bal [user] - shows the user's balance. By default the user is the one who ran the command
{config.get_attribute("command_prefix")}top (X) [keyword1] [keyword2] - shows the top X players by "keywords" where keyword1 may be "points" or "wins", keyword2 may be "total", "monthly", "weekly" or "event". Default: keyword1 = "points", keyword2 = "total"
{config.get_attribute("command_prefix")}lb [user] - shows the user's position on the leaderboard and several players around them. By default the user is the one who ran the command
{config.get_attribute("command_prefix")}code [user] - shows the user's referral code. By default the user is the one who ran the command. Only available to members with at least {config.get_attribute("commander_threshold")} points
{config.get_attribute("command_prefix")}usecode (code) - uses a referral code. Only available to members with less than {config.get_attribute("referral_threshold")} points
{config.get_attribute("command_prefix")}referrals [user] - shows the list of the user's referrals. By default the user is the one who ran the command
{config.get_attribute("command_prefix")}help - shows this window

**STAFF-ONLY COMMANDS**
{config.get_attribute("command_prefix")}a (points) (user) - gives the user a certain amount of points
{config.get_attribute("command_prefix")}r (points) (user) - removes a certain amount of points from the user
{config.get_attribute("command_prefix")}mult (multiplier) - sets the points multiplier
{config.get_attribute("command_prefix")}undo - revertes the last points-related command used by any user
{config.get_attribute("command_prefix")}startevent - starts a new event with a separate points leaderboard. There can only be one event at a time
{config.get_attribute("command_prefix")}endevent - ends the current event and shows the final event leaderboard"""

    embed = discord.Embed(title="All VoidBot commands", color=discord.Color.dark_gold(), description=help_text)
    await ctx.send(embed=embed)

############################################################### - STAFF-ONLY BOT COMMANDS - ###############################################################

@bot.command(name="a")
@commands.has_role(config.get_attribute("member_role"))
@DiscordUtils.has_any_of_the_roles(config.get_attribute("staff_roles"))
async def add_points(ctx: commands.Context, amount: int, user: discord.User) -> None:
    """
    Adds a certain amount of points to any user
    """

    user_data.add_entry_if_needed(user.id)

    if amount <= 0:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values are allowed")
        return

    commander_id = user_data.get_attribute(user.id, "commander")
    if commander_id:
        commander = bot.get_user(int(commander_id))
        await manipulate_points(ctx=ctx, amounts=[1.1 * amount, .1 * amount], users=[user, commander])
        return

    await manipulate_points(ctx=ctx, amounts=[amount], users=[user])

@bot.command(name="r")
@commands.has_role(config.get_attribute("member_role"))
@DiscordUtils.has_any_of_the_roles(config.get_attribute("staff_roles"))
async def remove_points(ctx: commands.Context, amount: int, user: discord.User) -> None:
    """
    Removes a certain amount of points from any user
    """

    if amount <= 0:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values are allowed")
        return
    
    await manipulate_points(ctx=ctx, amounts=[-amount], users=[user])

@bot.command(name="mult")
@commands.has_role(config.get_attribute("member_role"))
@DiscordUtils.has_any_of_the_roles(config.get_attribute("staff_roles"))
async def set_multiplier(ctx: commands.Context, multiplier: float) -> None:
    """
    Sets a point multiplier (for 2x events etc.)
    """

    if multiplier <= 0:
        await show_message(ctx=ctx, message_title="Error!", message_text="Only positive values are allowed")
        return

    await show_message(ctx=ctx, message_title="Success!", message_text=f"The points multiplier is now {multiplier}")

    config.set_attribute("multiplier", multiplier)
    config.save_data(CONFIG_FILE)

@bot.command(name="undo")
@commands.has_role(config.get_attribute("member_role"))
@DiscordUtils.has_any_of_the_roles(config.get_attribute("staff_roles"))
async def undo_last_command(ctx: commands.Context) -> None:
    """
    Revertes the last points-related command used by any user
    """

    with open("points_logs.txt", "r") as points_logs_file:
        lines = points_logs_file.readlines()

    last_action = lines.pop(-1)
    ids = list(map(int, last_action.split(" - ")[0].replace("[", "").replace("]", "").split(", ")))
    users = [bot.get_user(id) for id in ids]
    amounts = list(map(lambda elem: -int(float(elem)), last_action.split(" - ")[1].replace("[", "").replace("]", "").split(", ")))

    await manipulate_points(ctx=ctx, amounts=amounts, users=users)

    with open("points_logs.txt", "w") as points_logs_file:
        points_logs_file.write("".join(lines))

@bot.command(name="startevent")
@commands.has_role(config.get_attribute("member_role"))
@DiscordUtils.has_any_of_the_roles(config.get_attribute("staff_roles"))
async def start_event(ctx: commands.Context) -> None:
    """
    Toggles the config "is_event" attribute to become true
    """

    if config.get_attribute("is_event"):
        await show_message(ctx=ctx, message_title="Error!", message_text="An event already exists, consider ending it before starting a new one!")
        return
    
    config.set_attribute("is_event", True)
    config.save_data(CONFIG_FILE)

    user_data.reset_attribute("event_points")
    user_data.save_data(config.get_attribute("user_data_file"))

    await show_message(ctx=ctx, message_title="Success!", message_text='Event started! Run "top" command with "points" + "event" keywords to see the leaderboard')

@bot.command(name="endevent")
@commands.has_role(config.get_attribute("member_role"))
@DiscordUtils.has_any_of_the_roles(config.get_attribute("staff_roles"))
async def end_event(ctx: commands.Context) -> None:
    """
    Toggles the config "is_event" attribute to become false, sends resulting event leaderboard into the channel where the command was run
    """

    if not config.get_attribute("is_event"):
        await show_message(ctx=ctx, message_title="Error!", message_text="There isn't an event currently, consider creating one!")
        return
    
    config.set_attribute("is_event", False)
    config.save_data(CONFIG_FILE)

    results_embed = create_embed_for_top(top=30, by="event_points", title="Event results")

    user_data.reset_attribute("event_points")
    user_data.save_data(config.get_attribute("user_data_file"))

    await ctx.send(embed=results_embed)

############################################################### - ON_EVENT ACTIONS - ###############################################################

@bot.event
async def on_ready() -> None:
    """
    on_ready set ups
    """

    update_leaderboards_in_special_channel.start()

    print("READY")

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

    @bot.command(name="rwp")
@commands.has_role(config["member_role"])
@DiscordUtils.has_any_of_the_roles(config["staff_roles"])
async def remove_weekly_points(ctx, amount: int, user: discord.User) -> None:
    """
    Removes weekly points from user. Doesn't affect monthly/total points
    """

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

@bot.command(name="rmp")
@commands.has_role(config["member_role"])
@DiscordUtils.has_any_of_the_roles(config["staff_roles"])
async def remove_monthly_points(ctx, amount: int, user: discord.User) -> None:
    """
    Removes monthly points from user. Doesn't affect weekly/total points
    """

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
'''

############################################################### - MAIN PART - ###############################################################

if __name__ == "__main__":
    user_data = UserDataHandler()
    user_data.load_data(config.get_attribute("user_data_file"))

    bot.run(config.get_attribute("token"))

############################################################### - TODO - ###############################################################

"""
TODO:
    - ...
    - ...
"""
