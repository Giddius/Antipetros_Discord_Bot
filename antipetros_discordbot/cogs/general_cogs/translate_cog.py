
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from datetime import datetime
import re
# * Third Party Imports --------------------------------------------------------------------------------->
from pytz import timezone, country_timezones
from fuzzywuzzy import fuzz
from fuzzywuzzy import process as fuzzprocess
from discord.ext import commands
from googletrans import LANGUAGES, Translator
from typing import Optional
import unicodedata
from textwrap import dedent
import emoji
import discord
from icecream import ic
from discord import AllowedMentions
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.misc import CogConfigReadOnly, day_to_second, save_commands, hour_to_second, minute_to_second, make_config_name
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role_2, allowed_requester, command_enabled_checker
from antipetros_discordbot.utility.named_tuples import CITY_ITEM, COUNTRY_ITEM
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.cogs import get_aliases, get_doc_data
from antipetros_discordbot.utility.converters import LanguageConverter
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import RequestStatus, CogState
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
COG_NAME = "TranslateCog"
CONFIG_NAME = make_config_name(COG_NAME)
get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]


class TranslateCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Soon
    """
    # region [ClassAttributes]

    language_dict = {value: key for key, value in LANGUAGES.items()}
    language_emoji_map = {'Germany': 'de',
                          'Austria': 'de',
                          'Russia': 'ru',
                          'United_Kingdom': 'en',
                          'Australia': 'en',
                          'United_States': 'en',
                          'Greece': 'el',
                          'South_Africa': 'af',
                          'Norway': 'no',
                          'Portugal': 'pt',
                          'France': 'fr',
                          'Spain': 'es',
                          'Israel': 'he',
                          'Kuwait': 'ar',
                          'Syria': 'ar',
                          'Turkey': 'tr',
                          'Japan': 'ja',
                          'Slovenia': 'sl',
                          'Croatia': 'hr',
                          'Serbia': 'sr',
                          'Bosnia_&_Herzegovina': 'bs',
                          'Macedonia': 'mk',
                          'Montenegro': 'hr',
                          'Czechia': 'cs',
                          'Poland': 'pl',
                          'Slovakia': 'sk',
                          'rainbow_flag_selector': 'eo',
                          'Albania': 'sq',
                          'China': 'zh-tw',
                          'South_Korea': 'ko',
                          'Hungary': 'hu',
                          'Netherlands': 'nl'
                          }
    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.WORKING | CogState.FEATURE_MISSING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 03:40:46",
                             "29d140f50313ab11e4ec463a204b56dbcba90f86502c5f4a027f4d1ab7f25525dcf97a5619fd1b88709b95e6facb81a7620b39551c98914dcb6f6fbf3038f542")}

    required_config_data = dedent("""
                                        emoji_translate_listener_enabled = yes
                                        emoji_translate_listener_allowed_channels = bot-testing
                                        emoji_translate_listener_allowed_roles = member""")
    config_name = CONFIG_NAME
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.translator = Translator()
        self.flag_emoji_regex = re.compile(r'REGIONAL INDICATOR SYMBOL LETTER (?P<letter>\w)')
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]


# endregion [Properties]

# region [Setup]


    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


    async def _emoji_translate_checks(self, payload):
        command_name = "emoji_translate_listener"
        channel = self.bot.get_channel(payload.channel_id)

        if get_command_enabled(command_name) is False:
            return False

        member = payload.member
        if member.bot is True:
            return False

        channel = self.bot.get_channel(payload.channel_id)
        if channel.type is not discord.ChannelType.text:
            return False

        if channel.name.casefold() not in self.allowed_channels(command_name):
            return False

        emoji_name = normalize_emoji(payload.emoji.name)
        if emoji_name not in self.language_emoji_map:
            return False

        if all(role.name.casefold() not in self.allowed_roles(command_name) for role in member.roles):
            return False

        return True

    @commands.Cog.listener(name="on_raw_reaction_add")
    async def emoji_translate_listener(self, payload):
        if await self._emoji_translate_checks(payload) is False:
            return
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        country_code = self.language_emoji_map.get(normalize_emoji(payload.emoji.name))

        if message.embeds != []:
            log.debug('translating embed')
            await self.translate_embed(payload.member, channel, message, message.embeds[0], country_code)
            return

        translated = self.translator.translate(text=message.content, dest=country_code, src="auto")
        await payload.member.send(f"**in {LANGUAGES.get(country_code)}:**\n {translated.text.strip('.')}", allowed_mentions=AllowedMentions.none())

    async def translate_embed(self, member, channel, message, embed, country_code):
        embed_dict = embed.to_dict()
        if "author" in embed_dict:
            embed_dict['author']['name'] = await self._translate_text(embed_dict['author'].get('name', ''), country_code=country_code)
        if "title" in embed_dict:
            embed_dict['title'] = await self._translate_text(embed_dict.get('title', ''), country_code=country_code)
        if "description" in embed_dict:
            embed_dict['description'] = await self._translate_text(embed_dict.get('description', ''), country_code=country_code)
        if 'footer' in embed_dict:
            embed_dict['footer']['text'] = await self._translate_text(embed_dict['footer'].get('text', ''), country_code=country_code)
        _new_fields = []
        for field in embed_dict.get('fields', []):
            _new_fields.append({'name': await self._translate_text(field.get('name', ''), country_code=country_code),
                                'value': await self._translate_text(field.get('value', ''), country_code=country_code),
                                'inline': field.get('inline', False)})
        embed_dict['fields'] = _new_fields
        await member.send(embed=discord.Embed.from_dict(embed_dict), allowed_mentions=AllowedMentions.none())

    async def _translate_text(self, text: str, country_code: str):
        try:
            return self.translator.translate(text=text, dest=country_code, src='auto').text.strip('.')
        except IndexError:
            return text
        except TypeError:
            return text

# endregion [Listener]

# region [Commands]

    @commands.command(aliases=get_aliases('translate'), **get_doc_data('translate'))
    @allowed_channel_and_allowed_role_2()
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def translate(self, ctx, to_language_id: Optional[LanguageConverter] = "english", *, text_to_translate: str):
        """
        Translates text into multiple different languages.
        Tries to auto-guess input language.

        Args:
            text_to_translate (str): the text to translate, quotes are optional
            to_language_id (Optional[LanguageConverter], optional): either can be the name of the language or an language code (iso639-1 language codes). Defaults to "english".
        """
        translated = self.translator.translate(text=text_to_translate, dest=to_language_id, src="auto")
        await ctx.send(f"__from {ctx.author.display_name}:__ *{translated.text}*")


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [Embeds]


# endregion [Embeds]

# region [HelperMethods]

    @staticmethod
    def get_emoji_name(s):
        return s.encode('ascii', 'namereplace').decode('utf-8', 'namereplace')


# endregion [HelperMethods]

# region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):

        pass


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(TranslateCog(bot)))
