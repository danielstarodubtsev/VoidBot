import discord

from discord.ext import commands


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