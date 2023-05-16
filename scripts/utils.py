import os
import random
import string

import discord

from typing import Union

from discord.ext import commands


class Utils:
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def generate_referral_code(length: int = 10, charset: str = None) -> str:
        """
        Generates a new random referral code of given length
        """

        if charset is None:
            charset = string.ascii_lowercase + string.ascii_uppercase + string.digits

        return "".join([random.choice(charset) for _ in range(length)])
    
    @staticmethod
    def range_clamp(val: Union[float, int], min_val: Union[float, int], max_val: Union[float, int]) -> Union[float, int]:
        """
        If val < min_val, returns min_val
        if val > max_val, returns max_val
        Otherwise returns val
        """

        return min(max_val, max(min_val, val))
    
    @staticmethod
    def shorten_string(string: str, max_length: int) -> str:
        """
        If the string is longer than max_length, shortens it and adds dots in the end of the string
        """

        if len(string) <= max_length:
            return string
    
        return string[:max_length - 2] + ".."
    
    @staticmethod
    def is_same_global_rank(rank1: str, rank2: str) -> bool:
        """
        [IX] Living Legend - 2 is same global rank as [IX] Living Legend - 4 but not same as [VI] Master - 1
        """

        return rank1.split(" - ")[0] == rank2.split(" - ")[0]
    

class DiscordUtils:
    def __init__(self):
        pass

    @staticmethod
    def is_user_in_guild(id: int, guild: discord.Guild) -> bool:
        return guild.get_member(id) is not None
    
    @staticmethod
    def has_any_of_the_roles(role_names: list[str]):
        """
        Decorator that checks whether the message author has any of the listed roles
        """

        async def predicate(ctx) -> bool:
            return bool({role.name for role in ctx.author.roles} & set(role_names))
        
        return commands.check(predicate)
    
    @staticmethod
    async def turn_msg_into_file(message: discord.Message, file_name: str, new_content: str = "", remove_file: bool = True) -> None:
        """
        Turns the message with the given ID into a file, substitutes the previous content with the new one
        Useful for example when first sending a message with a loading text, then converting it to a file via this func
        Deletes the file upon sending if remove_file is True
        """

        with open(file_name, "rb") as file:
            await message.add_files(discord.File(file))
        
        await message.edit(content=new_content)

        if remove_file:
            os.remove(file_name)