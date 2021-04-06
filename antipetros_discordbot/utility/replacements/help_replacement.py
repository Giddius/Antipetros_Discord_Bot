from discord.ext.commands import Command
from antipetros_discordbot.utility.gidtools_functions import loadjson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.gidtools_functions import pathmaker, readit, writeit, loadjson, writejson
from typing import List, Dict, Set, Tuple, Union
import os
import discord
from enum import Enum, Flag, auto, unique
from discord.ext import commands, tasks
from discord.ext.commands import MinimalHelpCommand


APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')


class BaseCustomHelpCommand(MinimalHelpCommand):
    bot = None
    mention_placeholder = "@BOTMENTION"

    def __init__(self, sort_commands: bool = True, **options):
        super().__init__(sort_commands=sort_commands, **options)

    def get_command_signature(self, command):
        if hasattr(command, 'example') and command.example is not None:
            return f"```css\n{command.example.replace(self.mention_placeholder,'@'+ self.bot.display_name)}\n```"
        return super().get_command_signature(command)

    async def send_command_help(self, command):
        await super().send_command_help(command)
        if hasattr(command, "gif") and command.gif is not None:
            file = discord.File(command.gif)
            destination = self.get_destination()
            await destination.send(file=file)
