

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import asyncio
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_LZMA
from typing import TYPE_CHECKING
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands, flags, tasks
import discord
from datetime import datetime
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from async_property import async_property
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import delete_message_if_text_channel
from antipetros_discordbot.utility.checks import log_invoker, owner_or_admin
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.converters import date_time_full_converter_flags

from antipetros_discordbot.utility.gidtools_functions import pathmaker
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, AntiPetrosFlagCommand, CommandCategory, auto_meta_info_command
from antipetros_discordbot.utility.general_decorator import universal_log_profiler

if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
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

# endregion[Constants]


class AdministrationCog(AntiPetrosBaseCog, command_attrs={'hidden': True, 'categories': CommandCategory.ADMINTOOLS | CommandCategory.META}):
    """
    Commands and methods that help in Administrate the Discord Server.
    """
    # region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING

    required_config_data = {'base_config': {},
                            'cogs_config': {}}
    required_folder = []
    required_files = []

# endregion[ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.color = "brown"
        self.ready = False
        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Setup]

    async def on_ready_setup(self):
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Properties]


# endregion[Properties]

# region [Loops]


# endregion[Loops]

# region [Commands]

    @ auto_meta_info_command()
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def delete_msg(self, ctx, *msgs: discord.Message):
        """
        Deletes messages.

        Can take several message Ids as input, as long as they are seperated by a single space.

        Example:
            @AntiPetros delete_msg 837700676872044604 837488218567475200
        """
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

        Example:
            @AntiPetros the_bot_new_clothes 120
        """
        msg = ZERO_WIDTH * 20 + '\n'
        await ctx.send('THE BOTS NEW CLOTHES' + (msg * 60), delete_after=delete_after)

        await ctx.message.delete()

    @auto_meta_info_command()
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def write_message(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        """
        Writes a message as the bot to a specific channel.


        Args:
            channel (discord.TextChannel): name or id of channel. Preferably use Id as it is failsafe.
            message (str): The message you want to write, does not need any quotes and can be multiline

        Example:
            @AntiPetros write_message 645930607683174401 This is my message
        """
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
    @auto_meta_info_command(cls=AntiPetrosFlagCommand)
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

        Example:
            @AntiPetros make_embed -t "My Title" -d "This is my description" -dis yes -da 120
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

    @auto_meta_info_command(categories=[CommandCategory.TEAMTOOLS, CommandCategory.DEVTOOLS])
    async def all_guild_emojis(self, ctx: commands.Context):
        """
        Collects all Guild emojis and sends them as zipped file.

        Example:
            @AntiPetros all_guild_emojis
        """
        async with ctx.typing():
            start_message = await ctx.send('Please wait this could take a minute or more!')
            with TemporaryDirectory() as tempdir:
                zip_path = pathmaker(tempdir, 'all_guild_emojis.zip')
                with ZipFile(zip_path, 'w', ZIP_LZMA) as zippy:
                    for emoji in self.bot.antistasi_guild.emojis:
                        emoji_asset = emoji.url_as()
                        save_path = pathmaker(tempdir, emoji.name + '_' + str(sum(int(num) for num in str(emoji.id))) + '.' + str(emoji_asset).split('.')[-1])
                        await emoji_asset.save(save_path)
                        zippy.write(save_path, os.path.basename(save_path))
                file = discord.File(zip_path)
                await ctx.send(file=file)
                if ctx.channel.type is not discord.ChannelType.private:
                    await start_message.delete()

# endregion[Commands]

# region [Helper]


# endregion[Helper]

# region [SpecialMethods]

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

# endregion[SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(AdministrationCog(bot))
