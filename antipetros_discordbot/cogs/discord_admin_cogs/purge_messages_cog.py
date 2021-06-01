

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands, flags
from typing import TYPE_CHECKING, Union, Any, Callable, Optional, List, Dict, Set, Tuple, Iterable
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
import discord
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import delete_message_if_text_channel
from antipetros_discordbot.utility.checks import in_allowed_channels
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, AntiPetrosFlagCommand, CommandCategory, auto_meta_info_command
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, AntiPetrosFlagCommand, CommandCategory, auto_meta_info_command
from antipetros_discordbot.utility.general_decorator import universal_log_profiler
from collections import UserDict
import asyncio
import re
from collections import defaultdict
from sortedcontainers import SortedDict, SortedList
from discord.ext import commands
from hashlib import blake2b
from random import seed, randint
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, SPECIAL_SPACE, SPECIAL_SPACE_2
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
# endregion[Imports]

# region [TODO]

# TODO: Add all special Cog methods

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


class MessageRepostCacheDict(UserDict):
    whitespace_regex = re.compile(r'\W')
    removal_time_seconds = 1200

    def clean_content(self, content: str) -> str:
        cleaned_content = discord.utils.remove_markdown(content)
        cleaned_content = self.whitespace_regex.sub('', cleaned_content)
        return cleaned_content

    async def hash_content(self, content: Union[str, bytes]) -> str:
        if isinstance(content, str):
            content = content.encode('utf-8', errors='ignore')
        content_hash = blake2b(content).hexdigest()
        return content_hash

    async def handle_message(self, msg: discord.Message) -> bool:

        member_id = msg.author.id
        member_id_string = str(member_id)
        text_content = msg.content
        attachment_content = [await attachment.read() for attachment in msg.attachments]
        cleaned_content = await asyncio.to_thread(self.clean_content, text_content)
        all_content = [cleaned_content] + attachment_content
        full_msg_hash = ""
        for content_item in all_content:
            full_msg_hash += await self.hash_content(content_item)

        if full_msg_hash in set(self.data.get(member_id_string, [])):
            return True

        await self.add(member_id_string, full_msg_hash)

        return False

    async def add(self, member_id_string: str, hashed_content_item: str):
        if member_id_string not in self.data:
            self.data[member_id_string] = []
        self.data[member_id_string].append(hashed_content_item)
        asyncio.create_task(self._timed_removal(member_id_string, hashed_content_item))
        log.debug('Added message to %s', str(self))

    async def _timed_removal(self, member_id_string: str, hashed_message: str):
        await asyncio.sleep(self.removal_time_seconds)
        self.data.get(member_id_string).remove(hashed_message)
        if self.data.get(member_id_string) == []:
            del self.data[member_id_string]
            log.debug('Remove member_id_string from %s, member_id_string="%s"', str(self), member_id_string)
        log.debug('Remove message from %s', str(self))

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(amount_keys={len(self.data.keys())}, amount_values={sum(len(value) for value in self.data.values())})"


class PurgeMessagesCog(AntiPetrosBaseCog, command_attrs={'hidden': True, "categories": CommandCategory.ADMINTOOLS}):
    """
    Commands to purge messages.
    """

# region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {}}
    required_folder = []
    required_files = []

# endregion[ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.ready = False
        self.msg_keeper = MessageRepostCacheDict()

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

# region [Listener]


    @commands.Cog.listener(name='on_message')
    async def remove_double_posts(self, msg: discord.Message):
        if self.ready is False or self.bot.setup_finished is False:
            return
        if msg.channel.type is discord.ChannelType.private:
            return
        if msg.channel.id != 645930607683174401:  # for dev hard coded to only apply in bot-testing
            return
        if msg.author.bot is True:
            return

        # commented out for dev so I can test it!

        # if msg.author.top_role.position <= 5:
        #     return
        log.debug("checking 'remove_double_post' if it is bot prefix")
        if any(msg.content.startswith(prfx) for prfx in await self.bot.get_prefix(msg)):
            return
        log.debug("finished checking 'remove_double_post' if it is bot prefix")
        if await self.msg_keeper.handle_message(msg) is True:
            log.debug("determined that message should be deleted")
            content = msg.content if msg.content != '' else 'NO TEXT CONTENT'
            author = msg.author
            channel_name = msg.channel.name
            files = [await attachment.to_file() for attachment in msg.attachments]
            log.debug("requesting deletion")
            await msg.delete()
            await author.send(f"Your message in `{channel_name}` was deleted because you reposted the same message in a short time!\n\n> {content}", files=files, allowed_mentions=discord.AllowedMentions.none())


# endregion[Listener]

# region [Commands]


    @flags.add_flag("--and-giddi", '-gid', type=bool, default=False)
    @flags.add_flag("--number-of-messages", '-n', type=int, default=99999999999)
    @auto_meta_info_command(cls=AntiPetrosFlagCommand)
    @commands.is_owner()
    @in_allowed_channels()
    async def purge_antipetros(self, ctx: commands.Context, **command_flags):
        """
        Removes all messages of the bot and optionally of giddi.

        Example:
            @AntiPetros purge_antipetros -gid yes -n 1000
        """

        def is_antipetros(message):
            if command_flags.get('and_giddi') is False:
                return message.author.id == self.bot.id
            return message.author.id in [self.bot.id, self.bot.creator.id]

        await ctx.channel.purge(limit=command_flags.get('number_of_messages'), check=is_antipetros, bulk=True)
        await ctx.send('done', delete_after=60)
        await delete_message_if_text_channel(ctx)

# endregion[Commands]

# region [SpecialMethods]

    def __repr__(self):
        return f"{self.name}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))
# endregion[SpecialMethods]

# region[Main_Exec]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(PurgeMessagesCog(bot))

# endregion[Main_Exec]
