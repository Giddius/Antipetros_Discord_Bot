"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

import gc
import os
import unicodedata


# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

# from discord import Embed, File

from discord.ext import commands, tasks

from discord.ext.commands.core import GroupMixin, hooked_wrapped_callback

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


import gidlogger as glog
from .base_command import AntiPetrosBaseCommand


# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class AntiPetrosBaseGroup(GroupMixin, AntiPetrosBaseCommand):
    is_group = True

    def __init__(self, *args, **attrs):
        self.invoke_without_command = attrs.pop('invoke_without_command', False)
        super().__init__(*args, **attrs)

    def copy(self):
        """Creates a copy of this :class:`Group`.

        Returns
        --------
        :class:`Group`
            A new instance of this group.
        """
        ret = super().copy()
        for cmd in self.commands:
            ret.add_command(cmd.copy())
        return ret

    async def invoke(self, ctx):
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            await self.prepare(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)

        if early_invoke:
            injected = hooked_wrapped_callback(self, ctx, self.callback)
            await injected(*ctx.args, **ctx.kwargs)

        ctx.invoked_parents.append(ctx.invoked_with)

        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.invoke(ctx)
        elif not early_invoke:
            # undo the trigger parsing
            view.index = previous
            view.previous = previous
            await super().invoke(ctx)

    async def reinvoke(self, ctx, *, call_hooks=False):
        ctx.invoked_subcommand = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            ctx.command = self
            await self._parse_arguments(ctx)

            if call_hooks:
                await self.call_before_hooks(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)

        if early_invoke:
            try:
                await self.callback(*ctx.args, **ctx.kwargs)
            except:
                ctx.command_failed = True
                raise
            finally:
                if call_hooks:
                    await self.call_after_hooks(ctx)

        ctx.invoked_parents.append(ctx.invoked_with)

        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.reinvoke(ctx, call_hooks=call_hooks)
        elif not early_invoke:
            # undo the trigger parsing
            view.index = previous
            view.previous = previous
            await super().reinvoke(ctx, call_hooks=call_hooks)

    def command(self, *args, **kwargs):
        """A shortcut decorator that invokes :func:`.command` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_command`.

        Returns
        --------
        Callable[..., :class:`Command`]
            A decorator that converts the provided method into a Command, adds it to the bot, then returns it.
        """
        def decorator(func):
            kwargs.setdefault('parent', self)
            kwargs.setdefault('cls', AntiPetrosBaseCommand)
            result = commands.command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
