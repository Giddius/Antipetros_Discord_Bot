# jinja2: trim_blocks:True
# jinja2: lstrip_blocks :True
# region [Imports]

# * Standard Library Imports -->
import gc
import os
import re
from typing import List, TYPE_CHECKING
import unicodedata
# * Third Party Imports -->
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
# from fuzzywuzzy import fuzz, process
import aiohttp
import discord
from discord.ext import tasks, commands, flags
from async_property import async_property

# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.misc import async_split_camel_case_string, delete_message_if_text_channel
from antipetros_discordbot.utility.checks import owner_or_admin
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, auto_meta_info_command
from antipetros_discordbot.utility.exceptions import CustomEmojiError, NameInUseError
from antipetros_discordbot.abstracts import BaseReactionInstruction

from typing import List, TYPE_CHECKING
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, auto_meta_info_command
from antipetros_discordbot.utility.general_decorator import universal_log_profiler
import asyncio
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
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class ChannelReactionInstruction(BaseReactionInstruction):
    def __init__(self, name: str, channel: discord.TextChannel, emojis: List):
        self.channel = channel
        super().__init__(name, emojis)

    async def check_trigger(self, message: discord.Message):
        return message.channel is self.channel

    async def get_info_embed(self):
        embed_data = await self.bot.make_generic_embed(title=await async_split_camel_case_string(str(self)),
                                                       description="The bot will react to every Message in the set channel with the set emojis",
                                                       fields=[self.bot.field_item(name='Name', value=self.name),
                                                               self.bot.field_item(name="Channel", value=self.channel.name),
                                                               self.bot.field_item(name="Emojis", value='\n'.join(str(emoji) if isinstance(emoji, discord.Emoji) else emoji for emoji in self.emojis))],
                                                       thumbnail="scream_emoji",
                                                       color='green')
        return embed_data

    def to_dict(self):
        return {"typus": str(self),
                "data": {"name": self.name,
                         "channel_id": self.channel.id,
                         "emojis": [emoji.name if hasattr(emoji, 'name') else str(emoji) for emoji in self.emojis]}
                }

    @classmethod
    def from_dict(cls, **kwargs):
        channel_id = kwargs.get('channel_id')
        channel = cls.bot.channel_from_id(channel_id)
        converted_emojis = []
        custom_emojis = {emoji.name: emoji for emoji in cls.bot.antistasi_guild.emojis}
        for emoji in kwargs.get('emojis'):
            if emoji in custom_emojis:
                emoji = custom_emojis.get(emoji)
            converted_emojis.append(emoji)
        return cls(name=kwargs.get('name'), channel=channel, emojis=converted_emojis)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.channel}, {self.emojis})"


class WordReactionInstruction(BaseReactionInstruction):
    def __init__(self, name: str, word: str, case_insensitive: bool, emojis: List, exceptions: list = None):
        self._word = word
        self.case_insensitive = case_insensitive
        self.exceptions = {
            'by_role': [],
            'by_channel': [],
            'by_user': [],
            'by_category': []
        }
        self.sort_exceptions(exceptions)
        super().__init__(name, emojis)

    def sort_exceptions(self, exceptions):
        if exceptions is None:
            return
        for item in exceptions:
            if item[0] == 'by_role':
                excepted_role = {role.id: role for role in self.bot.antistasi_guild.roles}.get(item[1])
                if excepted_role is not None:
                    self.exceptions['by_role'].append(excepted_role)

            elif item[0] == 'by_channel':
                excepted_channel = {channel.id: channel for channel in self.bot.antistasi_guild.channels}.get(item[1])
                if excepted_channel is not None:
                    self.exceptions['by_channel'].append(excepted_channel)

            elif item[0] == 'by_user':
                excepted_member = {member.id: member for member in self.bot.antistasi_guild.members}.get(item[1])
                if excepted_member is not None:
                    self.exceptions['by_user'].append(excepted_member)
            elif item[0] == 'by_category':
                except_category = {category.id: category for category in self.bot.antistasi_guild.categories}.get(item[1])
                if except_category is not None:
                    self.exceptions['by_category'].append(except_category)

    @property
    def word(self):
        word = self._word
        return word

    async def check_trigger(self, message: discord.Message):
        for key, value in self.exceptions.items():
            if key == 'by_role':
                if any(role in value for role in message.author.roles):
                    return False
            elif key == 'by_category':
                if message.channel.category in value:
                    return False
            elif key == 'by_channel':
                if message.channel in value:
                    return False
            elif key == 'by_user':
                if message.author in value:
                    return False
        content = message.content
        if self.case_insensitive is True:
            content = content.casefold()
        return self.word in re.split(r"[\!\"\#\$%\&'\(\)\*\+,\-\./:;<=>\?@\[\\\]\^_`\{\|\}\~\s]", content)

    async def get_info_embed(self):
        exceptions_value = []
        for key, value in self.exceptions.items():
            if value != []:
                for item in value:
                    exceptions_value.append(item.mention)
        exceptions_value = '\n'.join(exceptions_value) if exceptions_value != [] else "None"
        embed_data = await self.bot.make_generic_embed(title=await async_split_camel_case_string(str(self)),
                                                       description="The bot will react to every Message that contains the phrase with the set emojis",
                                                       fields=[self.bot.field_item(name='Name', value=self.name),
                                                               self.bot.field_item(name="word", value=self._word),
                                                               self.bot.field_item(name="Emojis", value='\n'.join(str(emoji) if isinstance(emoji, discord.Emoji) else emoji for emoji in self.emojis)),
                                                               self.bot.field_item(name="Case-Insensitive", value="✅" if self.case_insensitive is True else "❎"),
                                                               self.bot.field_item(name="Exceptions", value=exceptions_value)],
                                                       thumbnail="scream_emoji",
                                                       color='green')
        return embed_data

    def to_dict(self):
        exceptions = []
        for key, value in self.exceptions.items():
            for item in value:
                exceptions.append([key, item.id])

        return {"typus": str(self),
                "data": {"name": self.name,
                         "word": self._word,
                         "case_insensitive": self.case_insensitive,
                         "emojis": [emoji.name if hasattr(emoji, 'name') else str(emoji) for emoji in self.emojis],
                         'exceptions': exceptions}
                }

    @classmethod
    def from_dict(cls, **kwargs):
        word = kwargs.get('word')
        case_insensitive = kwargs.get('case_insensitive', False)
        converted_emojis = []
        custom_emojis = {emoji.name: emoji for emoji in cls.bot.antistasi_guild.emojis}
        for emoji in kwargs.get('emojis'):
            if emoji in custom_emojis:
                emoji = custom_emojis.get(emoji)
            converted_emojis.append(emoji)
        return cls(name=kwargs.get('name'), word=word, case_insensitive=case_insensitive, emojis=converted_emojis, exceptions=kwargs.get('exceptions'))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._word}, {self.case_insensitive}, {self.emojis})"


class AutoReactionCog(AntiPetrosBaseCog, command_attrs={"categories": CommandCategory.ADMINTOOLS, "hidden": True}):
    """
    WiP
    """
# region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {}}
    reaction_instructions_data_file = pathmaker(APPDATA['json_data'], "message_reaction_instructions_data.json")
    required_folder = []
    required_files = [RequiredFile(reaction_instructions_data_file, [], RequiredFile.FileType.JSON)]

    custom_emoji_regex = re.compile(r"\<\:(?P<name>.*)\:(?P<id>\d+)\>")


# endregion [ClassAttributes]

# region [Init]


    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        BaseReactionInstruction.bot = self.bot
        self.color = 'purple'
        self.ready = False
        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def reaction_instructions_data(self):
        if os.path.isfile(self.reaction_instructions_data_file) is False:
            writejson([], self.reaction_instructions_data_file)
        return loadjson(self.reaction_instructions_data_file)

    @property
    def reaction_instructions(self):
        _out = []
        for item in self.reaction_instructions_data:
            if item.get('typus') == "ChannelReactionInstruction":
                _out.append(ChannelReactionInstruction.from_dict(**item.get('data')))
            elif item.get('typus') == "WordReactionInstruction":
                _out.append(WordReactionInstruction.from_dict(**item.get('data')))
        return _out

    @property
    def antistasi_custom_emojis(self):
        return {emoji.name: emoji for emoji in self.bot.antistasi_guild.emojis}

# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):

        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


    @commands.Cog.listener(name='on_message')
    async def add_reaction_to_message_sorter_listener(self, msg: discord.Message):
        if self.ready is False:
            return
        try:
            if msg.author.bot is True:
                return
            for instruction in self.reaction_instructions:
                asyncio.create_task(instruction(msg))
        except discord.errors.NotFound:
            return


# endregion [Listener]

# region [Commands]


    @auto_meta_info_command()
    @owner_or_admin(False)
    async def add_channel_reaction_instruction(self, ctx: commands.Context, name: str, channel: discord.TextChannel, *emojis: str):
        if name.casefold() in {item.name.casefold() for item in self.reaction_instructions}:
            raise NameInUseError(name, "Reaction Instructions")
        if len(emojis) > 20:
            await ctx.send('Too many reactions, you can only add 20 reactions to a message (Discord limit)', delete_after=120)
            return
        emojis = [await self._handle_custom_emoji_input(emoji) for emoji in emojis]
        item = ChannelReactionInstruction(name=name, channel=channel, emojis=emojis)
        await self._add_to_reaction_instruction_data(item)
        first_embed = discord.Embed(title='Added Channel Auto Reaction', description="Added the following channel auto reaction item")
        await ctx.send(embed=first_embed, allowed_mentions=discord.AllowedMentions.none())
        info_embed_data = await item.get_info_embed()
        await ctx.send(**info_embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    @owner_or_admin(False)
    async def add_word_reaction_instruction(self, ctx: commands.Context, name: str, word: str, exceptions: str, *emojis):
        if name.casefold() in {item.name.casefold() for item in self.reaction_instructions}:
            raise NameInUseError(name, "Reaction Instructions")
        if len(emojis) > 20:
            await ctx.send('Too many reactions, you can only add 20 reactions to a message (Discord limit)', delete_after=120)
            return
        emojis = [await self._handle_custom_emoji_input(emoji) for emoji in emojis]
        exceptions = await self._handle_exceptions_data(exceptions)
        item = WordReactionInstruction(name=name, word=word, case_insensitive=True, emojis=emojis, exceptions=exceptions)
        await self._add_to_reaction_instruction_data(item)
        first_embed = discord.Embed(title='Added Word Auto Reaction', description="Added the following word auto reaction item")
        await ctx.send(embed=first_embed, allowed_mentions=discord.AllowedMentions.none())
        info_embed_data = await item.get_info_embed()
        await ctx.send(**info_embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    @owner_or_admin(False)
    async def remove_reaction_instruction(self, ctx: commands.Context, instruction_name: str):
        if instruction_name.casefold() not in {item.name.casefold() for item in self.reaction_instructions}:
            await ctx.send(f'Could not find Reaction instruction item with the name `{instruction_name}`', delete_after=120)
            await delete_message_if_text_channel(ctx)
            return
        item = {item.name.casefold(): item for item in self.reaction_instructions}.get(instruction_name.casefold())
        await self._remove_from_reaction_instruction_data(item)
        first_embed = discord.Embed(title="Reaction Instruction Removed", description="The following reaction instruction was removed")
        info_embed_data = await item.get_info_embed()

        await ctx.send(embed=first_embed, allowed_mentions=discord.AllowedMentions.none())
        await ctx.send(**info_embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    @owner_or_admin()
    async def add_exception_to_word_reaction_instruction(self, ctx: commands, instruction_name: str, typus: str, in_id: int):
        if instruction_name.casefold() not in {item.name.casefold() for item in self.reaction_instructions}:
            await ctx.send(f'Could not find Reaction instruction item with the name `{instruction_name}`', delete_after=120)
            await delete_message_if_text_channel(ctx)
            return
        item = {item.name.casefold(): item for item in self.reaction_instructions}.get(instruction_name.casefold())
        if not isinstance(item, WordReactionInstruction):
            await ctx.send(f'Could not find Word Reaction instruction item with the name `{instruction_name}`, exceptions can only be added to WORD REACTION INSTRUCTIONS', delete_after=120)
            await delete_message_if_text_channel(ctx)
            return
        if typus.casefold() not in ['role', 'channel', 'user', 'category']:
            await ctx.send(f"Unknown exception typus `{typus}`, has to be one of: `role`, `channel`, `user`", delete_after=120)
            await delete_message_if_text_channel(ctx)
            return
        item.sort_exceptions([(f"by_{typus.casefold()}", in_id)])
        await self._modify_reaction_instruction_data(item)
        await ctx.send("added exception to item")

    @auto_meta_info_command()
    @owner_or_admin()
    async def change_word_reaction_instruction_option(self, ctx: commands, instruction_name: str, option_name: str, option_value: bool):
        if instruction_name.casefold() not in {item.name.casefold() for item in self.reaction_instructions}:
            await ctx.send(f'Could not find Reaction instruction item with the name `{instruction_name}`', delete_after=120)
            await delete_message_if_text_channel(ctx)
            return
        item = {item.name.casefold(): item for item in self.reaction_instructions}.get(instruction_name.casefold())
        if not isinstance(item, WordReactionInstruction):
            await ctx.send(f'Could not find Word Reaction instruction item with the name `{instruction_name}`, exceptions can only be added to WORD REACTION INSTRUCTIONS', delete_after=120)
            await delete_message_if_text_channel(ctx)
            return
        if option_name.casefold() not in ['case_insensitive']:
            await ctx.send(f"Unknown option `{option_name}`, has to be one of: `case_insensitive`", delete_after=120)
            await delete_message_if_text_channel(ctx)
            return
        setattr(item, option_name, option_value)
        await self._modify_reaction_instruction_data(item)
        await ctx.send("changed option")

    @auto_meta_info_command()
    @owner_or_admin(True)
    async def list_all_reaction_instructions(self, ctx: commands.Context):
        first_embed = discord.Embed(title="All Reaction Instruction", description="I currently have the following reaction instructions active")
        await ctx.send(embed=first_embed, delete_after=180, allowed_mentions=discord.AllowedMentions.none())
        for item in self.reaction_instructions:
            embed_data = await item.get_info_embed()
            await ctx.send(**embed_data, delete_after=180, allowed_mentions=discord.AllowedMentions.none())

# endregion [Commands]


# region [HelperMethods]

    async def _handle_exceptions_data(self, exception_data):
        if exception_data.casefold() == 'none':
            return None
        _out = []
        exception_pairs = exception_data.split(';')
        for pair in exception_pairs:
            typus, value_id = pair.split(',')
            _out.append((typus.strip(), int(value_id.strip())))
        return _out

    async def _handle_custom_emoji_input(self, emoji: str):
        emoji_match = self.custom_emoji_regex.match(emoji)
        if emoji_match:
            name = emoji_match.group('name')
            if name not in self.antistasi_custom_emojis:
                raise CustomEmojiError(name, 'Is not an available custom emoji name')
            return self.antistasi_custom_emojis.get(name)
        return emoji

    async def _modify_reaction_instruction_data(self, modified_item: BaseReactionInstruction):
        all_instructions = self.reaction_instructions
        all_instructions.remove(modified_item)
        all_instructions.append(modified_item)
        await self._save_to_reaction_instructions_data(all_instructions)

    async def _add_to_reaction_instruction_data(self, new_item: BaseReactionInstruction):
        all_instructions = self.reaction_instructions
        all_instructions.append(new_item)
        await self._save_to_reaction_instructions_data(all_instructions)

    async def _remove_from_reaction_instruction_data(self, item_to_remove: BaseReactionInstruction):
        all_instructions = self.reaction_instructions
        all_instructions.remove(item_to_remove)
        await self._save_to_reaction_instructions_data(all_instructions)

    async def _save_to_reaction_instructions_data(self, items: List[BaseReactionInstruction]):
        data = [instruction.to_dict() for instruction in items]
        writejson(data, self.reaction_instructions_data_file)

# endregion [HelperMethods]

# region [SpecialMethods]

    def cog_check(self, ctx):
        return True

    async def cog_command_error(self, ctx, error):
        pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(AutoReactionCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
