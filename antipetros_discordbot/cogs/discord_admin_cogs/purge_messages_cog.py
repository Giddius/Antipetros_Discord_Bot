

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands, flags
from typing import List, TYPE_CHECKING, Union, Set
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
import discord
import textwrap
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import delete_message_if_text_channel
from antipetros_discordbot.utility.checks import in_allowed_channels, log_invoker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, AntiPetrosFlagCommand, CommandCategory, auto_meta_info_command
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, AntiPetrosFlagCommand, CommandCategory, auto_meta_info_command
from antipetros_discordbot.utility.data import IMAGE_EXTENSIONS
from collections import UserDict
import asyncio
from antipetros_discordbot.utility.converters import RoleOrIntConverter
import re
from sortedcontainers import SortedDict, SortedList
from discord.ext import commands
from hashlib import blake2b
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ListMarker
from antipetros_discordbot.auxiliary_classes.hashed_message import HashedMessage
from antipetros_discordbot.auxiliary_classes.asking_items import AskConfirmation, AskFile, AskInput, AskInputManyAnswers, AskAnswer, AskSelectionOptionsMapping, AskSelectionOption, AskSelection
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


class MessageRepostKeeper:

    def __init__(self):
        self.stored_messages = set()

    async def handle_message(self, hashed_msg: HashedMessage) -> bool:
        original_msg = await self.get_original_stored_message(hashed_msg)
        if original_msg is not None:
            await original_msg.reset_storage_time()
            original_msg.amount_reposted += 1
            return True

        self.stored_messages.add(hashed_msg)
        log.debug("Hashed Message %s was added to from %s", hashed_msg, self)
        return False

    async def get_original_stored_message(self, hashed_msg: HashedMessage) -> HashedMessage:
        if hashed_msg not in self.stored_messages:
            return None
        original = [stored_msg for stored_msg in self.stored_messages if stored_msg == hashed_msg][0]
        if await original.message_exists() is False:
            self.stored_messages.remove(original)
            log.debug("Hashed Message %s was removed from %s, because it was deleted", hashed_msg, self)
            return None
        return original

    async def get_original_message_no_check(self, hashed_msg: HashedMessage) -> HashedMessage:
        for stored_message in self.stored_messages:
            if await asyncio.sleep(0, stored_message == hashed_msg):
                return stored_message

    async def remove_stored_message(self, hashed_msg: HashedMessage):
        if hashed_msg in self.stored_messages:
            self.stored_messages.remove(hashed_msg)
            log.debug("Hashed Message %s was removed from %s", hashed_msg, self)

    async def get_amount_reposted(self, hashed_msg: HashedMessage) -> int:
        original = await self.get_original_message_no_check(hashed_msg)
        return original.amount_reposted

    async def get_message_link(self, hashed_msg: HashedMessage) -> str:
        original = await self.get_original_message_no_check(hashed_msg)
        return original.link

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(amount_stored_messages={len(self.stored_messages)})"


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
                            'cogs_config': {"remove_double_posts_enabled": "no",
                                            "double_post_notification_channel": "645930607683174401",
                                            "notify_double_post_in_channel": "no",
                                            "remove_double_posts_max_role_position": "8",
                                            "remove_double_post_timespan_minutes": "20",
                                            "double_post_notification_webhook_urls": "",
                                            "other_bot_prefixes": "",
                                            "remove_double_post_is_dry_run": "yes"}}
    required_folder = []
    required_files = []
    whitespace_regex = re.compile(r'\W')
    hashed_message_class = HashedMessage

# endregion[ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.msg_keeper = None
        self._init_msg_keeper()
        self._other_bot_prefixes = None
        self._remove_double_post_is_dry_run = None
        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Setup]

    async def on_ready_setup(self):

        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        if UpdateTypus.CONFIG in typus:
            await self.hashed_message_class.update_store_for_minutes()
            self._other_bot_prefixes = None
            self._remove_double_post_is_dry_run = None
        log.debug('cog "%s" was updated', str(self))

    def _init_msg_keeper(self):
        self.hashed_message_class.bot = self.bot
        self.hashed_message_class.config_name = self.config_name
        self.msg_keeper = MessageRepostKeeper()
        self.hashed_message_class.removal_signal.connect(self.msg_keeper.remove_stored_message)

# endregion [Setup]

# region [Properties]

    @property
    def notify_channel(self) -> discord.TextChannel:
        notification_channel_id = COGS_CONFIG.retrieve(self.config_name, 'double_post_notification_channel', typus=int, direct_fallback=645930607683174401)  # direct fallback is channel Bot-testing
        return self.bot.channel_from_id(notification_channel_id)

    @property
    def notify_webhooks(self) -> List[str]:
        return COGS_CONFIG.retrieve(self.config_name, "double_post_notification_webhook_urls", typus=List[str], direct_fallback=[])

    @property
    def notify_double_post_in_channel(self) -> bool:
        return COGS_CONFIG.retrieve(self.config_name, 'notify_double_post_in_channel', typus=bool, direct_fallback=False)

    @property
    def remove_double_posts_enabled(self) -> bool:
        return COGS_CONFIG.retrieve(self.config_name, 'remove_double_posts_enabled', typus=bool, direct_fallback=False)

    @property
    def remove_double_posts_max_role_position(self) -> bool:
        return COGS_CONFIG.retrieve(self.config_name, 'remove_double_posts_max_role_position', typus=int, direct_fallback=8)

    @property
    def other_bot_prefixes(self):
        if self._other_bot_prefixes is None:
            self._other_bot_prefixes = COGS_CONFIG.retrieve(self.config_name, 'other_bot_prefixes', typus=Set[str], direct_fallback=set())
        return self._other_bot_prefixes

    @property
    def remove_double_post_is_dry_run(self):
        if self._remove_double_post_is_dry_run is None:
            self._remove_double_post_is_dry_run = COGS_CONFIG.retrieve(self.config_name, 'remove_double_post_is_dry_run', typus=bool, direct_fallback=True)
        return self._remove_double_post_is_dry_run
# endregion[Properties]

# region [Listener]

    @commands.Cog.listener(name='on_message')
    async def remove_double_posts(self, msg: discord.Message):
        if any([self.ready is False, self.bot.setup_finished is False]):
            log.debug("self.ready = %s, self.bot.setup_finished = %s", self.ready, self.bot.setup_finished)
            return
        if self.remove_double_posts_enabled is False:
            return
        if msg.channel.type is discord.ChannelType.private:
            return
        if self.bot.is_debug is True and msg.channel.id != 645930607683174401:  # for dev hard coded to only apply in bot-testing
            return
        if msg.author.bot is True:
            return

        if msg.author.top_role.position > self.remove_double_posts_max_role_position:
            log.debug("msg author top role position is %s and limit is %s", msg.author.top_role.position, self.remove_double_posts_max_role_position)
            return

        if any(msg.content.startswith(prfx) for prfx in await self.bot.get_prefix(msg)):
            return
        if any(msg.content.startswith(prfx) for prfx in self.other_bot_prefixes):
            return
        hashed_msg = await self.hashed_message_class.from_message(msg)
        if await self.msg_keeper.handle_message(hashed_msg) is True:
            log.debug("Message has been determined to be a duplicate message")
            log.debug('Message content:\n%s', textwrap.indent(f'"{msg.content}"', ' ' * 8))
            amount_reposted = await self.msg_keeper.get_amount_reposted(hashed_msg)
            log.debug("Message was reposted %s times", amount_reposted)
            msg_link = await self.msg_keeper.get_message_link(hashed_msg)
            if self.notify_double_post_in_channel is True:
                asyncio.create_task(self._notify_double_post_to_channel(msg.content, msg.author, msg.channel, [await attachment.to_file() for attachment in msg.attachments], amount_reposted, msg_link))
            for w_url in self.notify_webhooks:
                asyncio.create_task(self._notify_double_post_to_webhook(msg.content, msg.author, msg.channel, [await attachment.to_file() for attachment in msg.attachments], amount_reposted, msg_link, w_url))

            asyncio.create_task(self._message_double_post_author(msg.content, msg.author, msg.channel, [await attachment.to_file() for attachment in msg.attachments]))

            if self.remove_double_post_is_dry_run is False:
                log.debug("requesting deletion of Message")
                await msg.delete()
                log.debug("Message has been deleted")

    @commands.Cog.listener(name='on_message_edit')
    async def remove_double_posts_update_edited(self, old_msg: discord.Message, new_msg: discord.Message):
        if any([self.ready is False, self.bot.setup_finished is False]):
            log.debug("self.ready = %s, self.bot.setup_finished = %s", self.ready, self.bot.setup_finished)
            return
        if self.remove_double_posts_enabled is False:
            return

        old_hashed_msg = await self.hashed_message_class.from_message(old_msg)
        if old_hashed_msg in self.msg_keeper.stored_messages:
            await self.msg_keeper.remove_stored_message(old_hashed_msg)
            old_hashed_msg.removal_task.cancel()
        await self.remove_double_posts(new_msg)

# endregion[Listener]

# region [Commands]

    @flags.add_flag("--and-giddi", '-gid', type=bool, default=False)
    @flags.add_flag("--number-of-messages", '-n', type=int, default=99999999999)
    @auto_meta_info_command(cls=AntiPetrosFlagCommand)
    @commands.is_owner()
    @in_allowed_channels()
    @log_invoker(log, 'warning')
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

    @auto_meta_info_command(clear_invocation=True, experimental=True)
    @commands.is_owner()
    @log_invoker(log, 'warning')
    async def remove_double_posts_settings(self, ctx: commands.Context):
        setting_ask = AskSelection(author=ctx.author, channel=ctx.channel, timeout=300, delete_question=True)
        setting_ask.description = "Select a Setting you want to change."
        setting_ask.options.add_option(setting_ask.option_item(item="switch on/off"))
        setting_ask.options.add_option(setting_ask.option_item(item="change max triggered Role"))
        answer = await setting_ask.ask()
        if answer in {setting_ask.CANCELED, setting_ask.NOANSWER}:
            return

        if answer == "switch on/off":
            current_setting = self.remove_double_posts_enabled
            current_setting_text = "Enabled" if current_setting is True else "Disabled"
            future_setting_text = "Disabled" if current_setting is True else "Enabled"

            confirmation_ask = AskConfirmation(ctx.author, ctx.channel, timeout=300, delete_question=True)
            confirmation_ask.description = f"Double Post Remover is currently **{current_setting_text.upper()}**.\nDo you want to set it to ***{future_setting_text}***?"
            answer = await confirmation_ask.ask()
            if answer in {confirmation_ask.CANCELED, confirmation_ask.DECLINED, confirmation_ask.NOANSWER}:
                return
            COGS_CONFIG.set(self.config_name, "remove_double_posts_enabled", str(not current_setting))
            await ctx.send(f"Double Post Remover is now **{future_setting_text}**!")
            return

        if answer == "change max triggered Role":
            input_ask = AskInput(ctx.author, ctx.channel, timeout=300, delete_question=True, delete_answers=True)
            def validator(x): return any([x.isnumeric(), x in self.bot.roles_name_dict])
            input_ask.validator = validator
            level_display = await self._create_role_level_display(self.remove_double_posts_max_role_position)
            input_ask.description = f"Please enter either the position number of the new max role, a role id or a role Name!\n Currently set to \n{level_display}."
            answer = await input_ask.ask()
            if answer in {input_ask.CANCELED, input_ask.NOANSWER}:
                return
            answer = await RoleOrIntConverter().convert(ctx, answer)
            await self.set_remove_double_posts_max_role_position(ctx, answer)

    @auto_meta_info_command()
    @commands.is_owner()
    @log_invoker(log, 'warning')
    async def toggle_remove_double_posts(self, ctx: commands.Context, switch_to: bool = None):
        """
        Turns the remove_double_posts-listener on and off.

        Args:
            switch_to (bool, optional): what you want to switch the listener to, either `on` or `off`, if this is not provided it just automatically switches to the opposite it currently is. Defaults to None.

        Example:
            @AntiPetros toggle_remove_double_posts off
        """
        current_setting = self.remove_double_posts_enabled
        if switch_to is not None:
            if switch_to is current_setting:
                setting_text = "enabled" if switch_to is True else "disabled"
                asyncio.create_task(ctx.send(f"The `remove_double_posts`-listener is already **{setting_text}**", delete_after=120))
                asyncio.create_task(delete_message_if_text_channel(ctx))
                return
        target_setting = not current_setting
        target_setting_text = 'enabled' if target_setting is True else 'disabled'
        asyncio.create_task(delete_message_if_text_channel(ctx))
        await ctx.send(f"trying to switch the `remove_double_posts`-listener to `{target_setting_text}`", delete_after=30)

        COGS_CONFIG.set(self.config_name, "remove_double_posts_enabled", str(target_setting))

        new_text = 'enabled' if self.remove_double_posts_enabled is True else 'disabled'
        await ctx.send(f"The `remove_double_posts`-listener was switched to `{new_text}`", delete_after=120)

    @auto_meta_info_command()
    @commands.is_owner()
    @log_invoker(log, 'warning')
    async def set_remove_double_posts_max_role_position(self, ctx: commands.Context, new_max_position: RoleOrIntConverter):
        """
        Sets the max role position that still triggers the remove_double_posts check.

        Args:
            new_max_position (RoleOrIntConverter): can either be a position number, an Role-id or an Role-name, in the last two cases the position is the roles position.

        Example:
            @AntiPetros set_remove_double_posts_max_role_position 12
        """
        if isinstance(new_max_position, discord.Role):
            new_max_position = new_max_position.position
        COGS_CONFIG.set(self.config_name, "remove_double_posts_max_role_position", str(new_max_position))
        asyncio.create_task(delete_message_if_text_channel(ctx))
        level_display = await self._create_role_level_display(new_max_position)
        embed_data = await self.bot.make_generic_embed(title=f"remove_double_posts_max_role_position was set to __{new_max_position}__",
                                                       description=level_display,
                                                       thumbnail=None)
        await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none(), delete_after=120)


# endregion[Commands]

# region [Helper]

    async def _create_role_level_display(self, new_level: int) -> str:
        raw_all_roles = sorted(self.bot.antistasi_guild.roles, key=lambda x: x.position)
        all_roles = {role.position: role.name for role in raw_all_roles}
        max_len = max(len(role.name) for role in raw_all_roles)
        text = f"Level: {'Name'.center(max_len+3)}\n{'='*max_len}\n"
        text += '\n'.join(f"+ {key}: {value.center(max_len + 3)}" if key > new_level else f"- {key}: {value.center(max_len + 3)}{' '*(3-len(str(key)))}<--" for key, value in all_roles.items())
        return CodeBlock(text, 'diff')

    async def _message_double_post_author(self, content: str, author: discord.Member, channel: discord.TextChannel, files: List[discord.File]):
        title = "Your Message was removed!"
        description = "**Your Message:**\n" + textwrap.indent(content.strip(), '> ')
        fields = []
        if self.remove_double_post_is_dry_run is True:
            fields.append(self.bot.field_item(name="**__YOUR MESSAGE WAS NOT DELETED__**",
                          value="As this feature is still in its `testing-phase`. If you think the bot made an error in flagging your post as double post, please contact `Giddi` or post in the `bot-commands` channel", inline=False))
        fields += [self.bot.field_item(name='Reason', value="The Message is identical to a Message that was already posted by you in the __**Antistasi**__ Guild a short time ago", inline=False),
                   self.bot.field_item(name='Posted in Channel', value=embed_hyperlink(channel.name, self.bot.get_channel_link(channel.id)), inline=False)]
        image = None
        if len(files) > 0:
            fields.append(self.bot.field_item(name='Attachments',
                          value=ListMarker.make_list([f"`{att_file.filename}`" for att_file in files], indent=1), inline=False))
            image = files.pop(0) if files[0].filename.split('.')[-1] in IMAGE_EXTENSIONS else None

        if "help" in set(map(lambda x: x.casefold(), self.whitespace_regex.split(content))):
            fields.append(self.bot.field_item(name='__**If you are asking for Help**__'.upper(),
                          value=f"Please only post once in the channel {embed_hyperlink('***HELP***', self.bot.get_channel_link('help'))} and be patient!", inline=False))

        footer = {'text': "This has been logged and Admins have been notified"}

        embed_data = await self.bot.make_generic_embed(title=title, description=description, fields=fields, image=image, thumbnail='warning', footer=footer)

        await author.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

        if files:
            await author.send(files=files, allowed_mentions=discord.AllowedMentions.none())
        log.debug("Author %s has been notified", author.display_name)

    async def _notify_double_post_to_channel(self, content: str, author: discord.Member, channel: discord.TextChannel, files: List[discord.File], amount_reposted: int, message_link: str):
        fields = [self.bot.field_item(name="Author", value=f"{author.mention} (`{author.name}`)", inline=False),
                  self.bot.field_item(name="In Channel", value=channel.mention, inline=False),
                  self.bot.field_item(name='Times Reposted', value=amount_reposted, inline=False),
                  self.bot.field_item(name='Original Message Link', value=embed_hyperlink('Original Message', message_link), inline=False),
                  self.bot.field_item(name='Content', value=CodeBlock(textwrap.shorten(content, width=1000, placeholder="...[SHORTENED]"), 'fix'), inline=False)]
        image = None
        if len(files) > 0:
            fields.append(self.bot.field_item(name='Attachments',
                          value=f"The following attachment of the deleted message can be found attached to this message.\n{ListMarker.make_list([att_file.filename for att_file in files], indent=1)}", inline=False))
            image = files.pop(0) if files[0].filename.split('.')[-1] in IMAGE_EXTENSIONS else None
        if self.remove_double_post_is_dry_run is True:
            fields.append(self.bot.field_item(name='**__MESSAGE WAS NOT DELETED__**', value="Reason: `Testing-phase`", inline=False))
        embed_data = await self.bot.make_generic_embed(title='Double Post Deleted', fields=fields, image=image, thumbnail='warning')

        await self.notify_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

        if files:
            await self.notify_channel.send(files=files, allowed_mentions=discord.AllowedMentions.none())

    async def _notify_double_post_to_webhook(self, content: str, author: discord.Member, channel: discord.TextChannel, files: List[discord.File], amount_reposted: int, message_link: str, webhook_url: str):
        fields = [self.bot.field_item(name="Author", value=f"{author.mention} (`{author.name}`)", inline=False),
                  self.bot.field_item(name="In Channel", value=channel.mention, inline=False),
                  self.bot.field_item(name='Times Reposted', value=amount_reposted, inline=False),
                  self.bot.field_item(name='Original Message Link', value=embed_hyperlink('Original Message', message_link), inline=False),
                  self.bot.field_item(name='Content', value=CodeBlock(textwrap.shorten(content, width=1000, placeholder="...[SHORTENED]"), 'fix'), inline=False)]
        image = None
        if len(files) > 0:
            fields.append(self.bot.field_item(name='Attachments',
                          value=f"The following attachment of the deleted message can be found attached to this message.\n{ListMarker.make_list([att_file.filename for att_file in files], indent=1)}", inline=False))
            image = files.pop(0) if files[0].filename.split('.')[-1] in IMAGE_EXTENSIONS else None
        if self.remove_double_post_is_dry_run is True:
            fields.append(self.bot.field_item(name='**__MESSAGE WAS NOT DELETED__**', value="Reason: `Testing-phase`", inline=False))
        embed_data = await self.bot.make_generic_embed(title='Double Post Deleted', fields=fields, image=image, thumbnail='warning')
        if files:
            embed_data['files'].append(files)
        webhook = discord.Webhook.from_url(webhook_url, adapter=discord.AsyncWebhookAdapter(self.bot.aio_request_session))
        await webhook.send(**embed_data, username="Double Post Notification", avatar_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Warning.svg/1200px-Warning.svg.png", allowed_mentions=discord.AllowedMentions.none())
# endregion[Helper]

# region [SpecialMethods]

    def __repr__(self):
        return f"{self.name}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

    # def cog_unload(self):
    #     log.debug("Cog '%s' UNLOADED!", str(self))
# endregion[SpecialMethods]

# region[Main_Exec]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(PurgeMessagesCog(bot))

# endregion[Main_Exec]
