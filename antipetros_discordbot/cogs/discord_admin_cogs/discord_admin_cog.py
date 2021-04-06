

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from textwrap import dedent
import asyncio
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands, flags, tasks
import discord
from datetime import datetime, timedelta, timezone
from dateparser import parse as date_parse
from typing import Iterable, List, Dict, Optional, Tuple, Union, Callable, Mapping
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from async_property import async_property
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import make_config_name, delete_message_if_text_channel
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, log_invoker, owner_or_admin, has_attachments
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogState, UpdateTypus
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.converters import DateTimeFullConverter, date_time_full_converter_flags
from antipetros_discordbot.utility.id_generation import make_full_cog_id
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
    cog_id = 10
    full_cog_id = make_full_cog_id(THIS_FILE_DIR, cog_id)
    config_name = CONFIG_NAME
    announcements_channel_id = 645930607683174401
    community_subscriber_role_id = 827937724341944360
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
        self.meeting_message_times = {self.send_first_meeting_message: datetime(year=2021, month=1, day=1, hour=17, minute=5, second=0, tzinfo=timezone.utc),
                                      self.send_second_meeting_message: datetime(year=2021, month=1, day=1, hour=17, minute=10, second=0, tzinfo=timezone.utc),
                                      self.send_third_meeting_message: datetime(year=2021, month=1, day=1, hour=17, minute=15, second=0, tzinfo=timezone.utc)}
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Properties]

    @property
    def announcements_channel(self):
        return self.bot.sync_channel_from_id(self.announcements_channel_id)

    @property
    def community_subscriber_role(self):
        return self.bot.sync_retrieve_antistasi_role(self.community_subscriber_role_id)

# endregion[Properties]

# region [Setup]

    async def on_ready_setup(self):
        self.community_meeting_messages.start()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    async def send_first_meeting_message(self):
        start_time = datetime.now(tz=timezone.utc).replace(hour=19, minute=0, second=0)

        embed_data = await self.bot.make_generic_embed(title="Community Meeting Reminder",
                                                       description="Community Meeting in 30 minutes!",
                                                       fields=[self.bot.field_item(name="Meeting time as your local time", value="⇩")],
                                                       timestamp=start_time,
                                                       color="green")
        await self.announcements_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    async def send_second_meeting_message(self):
        start_time = datetime.now(tz=timezone.utc).replace(hour=19, minute=0, second=0)
        embed_data = await self.bot.make_generic_embed(title="Community Meeting Reminder",
                                                       description=f"`{self.community_subscriber_role.mention}` Community Meeting in 15 minutes!",
                                                       fields=[self.bot.field_item(name="Meeting time as your local time", value="⇩")],
                                                       timestamp=start_time,
                                                       color="green")
        await self.announcements_channel.send(**embed_data)

    async def send_third_meeting_message(self):
        start_time = datetime.now(tz=timezone.utc).replace(hour=19, minute=0, second=0)
        embed_data = await self.bot.make_generic_embed(title="Community Meeting Starting",
                                                       description="Community meeting starting now!",
                                                       timestamp=start_time,
                                                       color="green")
        await self.announcements_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    async def check_timespan(self, target_time: datetime, time_span_minutes: int = 1, on_days: Iterable = None):
        on_days = {0, 1, 2, 3, 4, 5, 6} if on_days is None else set(on_days)
        check_delta = timedelta(minutes=time_span_minutes)
        lower_time = target_time - check_delta
        upper_time = target_time + check_delta
        now = datetime.now(tz=timezone.utc)
        if now.weekday() in on_days:
            return lower_time.time() < now.time() < upper_time.time()
        return False

    @tasks.loop(minutes=2)
    async def community_meeting_messages(self):
        for key, value in self.meeting_message_times.items():
            if await self.check_timespan(value, time_span_minutes=1, on_days=[6]) is True:
                await key()
                break

# endregion[Loops]

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
    @flags.add_flag("--url", '-u', type=str, default=discord.Embed.Empty)
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
        embed_data = await self.bot.make_generic_embed(**flags, color='random')

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
        self.community_meeting_messages.stop()
        log.debug("Cog '%s' UNLOADED!", str(self))


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(AdministrationCog(bot)))
