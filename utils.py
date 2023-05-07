import random
import string

import discord

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
    
    def has_any_of_the_roles(role_names: list[str]):
        """
        Decorator that checks whether the message author has any of the listed roles
        """

        async def predicate(ctx) -> bool:
            return bool({role.name for role in ctx.author.roles} & set(role_names))
        
        return commands.check(predicate)