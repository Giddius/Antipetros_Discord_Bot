

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from textwrap import dedent
import asyncio
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands, flags, tasks
import discord
from datetime import datetime
from dateparser import parse as date_parse
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import make_config_name, delete_message_if_text_channel
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, log_invoker, owner_or_admin, has_attachments
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogState
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.converters import DateTimeFullConverter, date_time_full_converter_flags
# endregion[Imports]

# region [TODO]


# TODO: get_logs command
# TODO: get_appdata_location command


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
COG_NAME = "AdministrationCog"
CONFIG_NAME = make_config_name(COG_NAME)
get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]


class AdministrationCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Commands and methods that help in Administrate the Discord Server.
    """
    # region [ClassAttributes]

    config_name = CONFIG_NAME

    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.OPEN_TODOS | CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING | CogState.OUTDATED | CogState.DOCUMENTATION_MISSING,)}
    required_config_data = dedent("""
                                  """)
    # endregion[ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Properties]


# endregion[Properties]

# region [Setup]


    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

    @ auto_meta_info_command(enabled=True)
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def delete_msg(self, ctx, *msgs: discord.Message):
        for msg in msgs:

            await msg.delete()
        await ctx.message.delete()

    @auto_meta_info_command(aliases=['clr-scrn'])
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def the_bots_new_clothes(self, ctx: commands.Context, delete_after: int = None):
        """
        Sends about a page worth of empty message to a channel, looks like channel got purged.

        Optional deletes the empty message after specified seconds (defaults to not deleting)

        Args:
            delete_after (int, optional): time in seconds after which to delete the empty message. Defaults to None which means that it does not delete the empty message.
        """
        msg = ZERO_WIDTH * 20 + '\n'
        await ctx.send('THE BOTS NEW CLOTHES' + (msg * 60), delete_after=delete_after)

        await ctx.message.delete()

    @auto_meta_info_command()
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def write_message(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        await channel.send(message)
        await ctx.message.delete()

    @flags.add_flag("--title", '-t', type=str, default=ZERO_WIDTH)
    @flags.add_flag("--description", '-d', type=str, default=ZERO_WIDTH)
    @flags.add_flag("--url", '-u', type=str)
    @flags.add_flag("--thumbnail", '-th', type=str)
    @flags.add_flag("--image", "-i", type=str)
    @flags.add_flag("--timestamp", "-ts", type=date_time_full_converter_flags, default=datetime.utcnow())
    @flags.add_flag("--author-name", "-an", type=str)
    @flags.add_flag("--author-url", '-au', type=str, default=discord.Embed.Empty)
    @flags.add_flag("--author-icon", "-ai", type=str, default=discord.Embed.Empty)
    @flags.add_flag("--footer-text", "-ft", type=str)
    @flags.add_flag("--footer-icon", "-fi", type=str, default=discord.Embed.Empty)
    @flags.add_flag("--disable-mentions", "-dis", type=bool, default=True)
    @flags.add_flag("--delete-after", "-da", type=int, default=None)
    @auto_meta_info_command(cls=flags.FlagCommand)
    @owner_or_admin()
    @log_invoker(log, "info")
    async def make_embed(self, ctx: commands.Context, channel: discord.TextChannel, **flags):
        """
        Creates a simple embed message in the specified channel.

        No support for embed fields, as input would be to complicated.

        Args:
            channel (discord.TextChannel): either channel name or channel id (prefered), where the message should be posted.
            --title (str):
            --description (str):
            --url (str):
            --thumbnail (str):
            --image (str):
            --timestamp (str):
            --author-name (str):
            --author-url (str):
            --author-icon (str):
            --footer-text (str):
            --footer-icon (str):
            --thumbnail (str):
            --image (str):
            --disable-mentions (bool):
            --delete-after (int):
        """
        allowed_mentions = discord.AllowedMentions.none() if flags.pop("disable_mentions") is True else None
        delete_after = flags.pop('delete_after')
        print(delete_after)
        if flags.get('author_name', None) is not None:
            flags["author"] = {"name": flags.pop('author_name', None), "url": flags.pop("author_url", None), "icon_url": flags.pop("author_icon", None)}
        else:
            flags["author"] = None
        if flags.get('footer_text', None) is not None:
            flags["footer"] = {"text": flags.pop("footer_text", None), "icon_url": flags.pop("footer_icon", None)}
        else:
            flags["footer"] = None
        embed_data = await self.bot.make_generic_embed(**flags)

        embed_message = await channel.send(**embed_data, allowed_mentions=allowed_mentions, delete_after=delete_after)
        await ctx.send(f"__**Created Embed in Channel**__: {channel.mention}\n**__Link__**: {embed_message.jump_url}", allowed_mentions=discord.AllowedMentions.none(), delete_after=60)
        await asyncio.sleep(60)
        await delete_message_if_text_channel(ctx)

    def cog_check(self, ctx):
        return True

    async def cog_command_error(self, ctx, error):
        pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    def __repr__(self):
        return f"{self.qualified_name}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(AdministrationCog(bot)))
