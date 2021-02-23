

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import Optional
from datetime import datetime
from textwrap import dedent
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import flags, tasks, commands

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, save_commands, CogConfigReadOnly, make_config_name, is_even, seconds_to_pretty
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role_2, in_allowed_channels, owner_or_admin, log_invoker
from antipetros_discordbot.utility.converters import DateOnlyConverter
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogState
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)


# endregion[Logging]

# region [Constants]
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
COG_NAME = "BotAdminCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)
# endregion[Constants]


class BotAdminCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Soon
    """
    config_name = CONFIG_NAME
    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.FEATURE_MISSING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 05:19:50",
                             "b0fabfbd25ed7b45a009737879c2ef61262acce2c3e9043d7b2b27e51f6cd8de27fea94d52e1f97739765b4629d534de76bf28b241c5f27bd96917f3eb8c7e6e")}

    required_config_data = dedent("""
                                  """)

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')

        glog.class_init_notification(log, self)
# region [Setup]

    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

    @property
    def who_is_trigger_phrases(self):
        return [f'who is {self.bot.display_name.casefold()}',
                f'what is {self.bot.display_name.casefold()}',
                f'who the fuck is {self.bot.display_name.casefold()}']

    @commands.Cog.listener(name='on_message')
    async def who_is_this_bot_listener(self, msg: discord.Message):
        command_name = "who_is_this_bot_listener"
        if get_command_enabled(command_name) is False:
            return
        channel = msg.channel
        if channel.type is not discord.ChannelType.text:
            return False

        if channel.name.casefold() not in self.allowed_channels(command_name):
            return False
        if any(trigger_phrase in msg.content.casefold() for trigger_phrase in self.who_is_trigger_phrases):
            embed_data = await self.bot.make_generic_embed(title=f'WHO IS {self.bot.display_name.upper()}', description='I am an custom made Bot for this community!',
                                                           fields=[self.bot.field_item(name='What I can do', value=f'Get a description of my features by using `@{self.bot.display_name} help`', inline=False),
                                                                   self.bot.field_item(name='Who created me', value='I was created by __**Giddi**__, for the Antistasi Community')])
            await msg.reply(**embed_data, delete_after=150)

    @ auto_meta_info_command(enabled=True)
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def add_to_blacklist(self, ctx, user: discord.Member):

        if user.bot is True:
            # TODO: make as embed
            await ctx.send("the user you are trying to add is a **__BOT__**!\n\nThis can't be done!")
            return
        blacklisted_user = await self.bot.blacklist_user(user)
        if blacklisted_user is not None:
            await ctx.send(f"User '{user.name}' with the id '{user.id}' was added to my blacklist, he wont be able to invoke my commands!")
        else:
            await ctx.send("Something went wrong while blacklisting the User")

    @ auto_meta_info_command(enabled=True)
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def remove_from_blacklist(self, ctx, user: discord.Member):

        await self.bot.unblacklist_user(user)
        await ctx.send(f"I have unblacklisted user {user.name}")

    @ auto_meta_info_command(enabled=True)
    async def tell_uptime(self, ctx):

        now_time = datetime.utcnow()
        delta_time = now_time - await self.bot.support.start_time
        seconds = round(delta_time.total_seconds())
        # TODO: make as embed
        await ctx.send(f"__Uptime__ -->\n\t\t| {str(seconds_to_pretty(seconds))}")

    def __repr__(self):
        return f"{self.name}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name


# region[Main_Exec]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(BotAdminCog(bot)))

# endregion[Main_Exec]
