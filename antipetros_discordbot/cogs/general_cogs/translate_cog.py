
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import re
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands
from googletrans import LANGUAGES, Translator
from typing import Optional
from textwrap import dedent
import discord
from discord import AllowedMentions
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from emoji import emojize

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import delete_message_if_text_channel
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.converters import LanguageConverter
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, auto_meta_info_command
from antipetros_discordbot.utility.general_decorator import async_log_profiler
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ListMarker

from typing import Optional, TYPE_CHECKING
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, auto_meta_info_command
from antipetros_discordbot.utility.general_decorator import async_log_profiler, universal_log_profiler

if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot

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
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))  # location of this file, does not work if app gets compiled to exe with pyinstaller

# endregion[Constants]


class TranslateCog(AntiPetrosBaseCog):
    """
    Collection of commands that help in translating text to different Languages.
    """
    # region [ClassAttributes]

    public = True
    meta_status = CogMetaStatus.WORKING
    long_description = ""
    extra_info = ""

    required_config_data = {'base_config': {},
                            'cogs_config': {"emoji_translate_listener_enabled": "yes",
                                            "emoji_translate_listener_allowed_channels": "bot-testing",
                                            "emoji_translate_listener_allowed_roles": "all"}}
    required_folder = []
    required_files = []

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
                          'Netherlands': 'nl'}


# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.translator = Translator()
        self.flag_emoji_regex = re.compile(r'REGIONAL INDICATOR SYMBOL LETTER (?P<letter>\w)')
        self.color = "violet"
        self.ready = False
        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]


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

    async def _emoji_translate_checks(self, payload):
        if self.ready is False or self.bot.setup_finished is False:
            return False
        command_name = "emoji_translate_listener"
        channel = self.bot.get_channel(payload.channel_id)
        if channel.type is not discord.ChannelType.text:
            return False
        if self.allowed_channels(command_name) != ['all'] and channel.name.casefold() not in self.allowed_channels(command_name):
            return False

        if COGS_CONFIG.retrieve(self.config_name, command_name + '_enabled', typus=bool, direct_fallback=False) is False:
            return False

        member = payload.member
        if member.bot is True:
            return False

        emoji_name = normalize_emoji(payload.emoji.name)
        if emoji_name not in self.language_emoji_map:
            return False

        if self.allowed_roles(command_name) != ['all'] and all(role.name.casefold() not in self.allowed_roles(command_name) for role in member.roles):
            return False

        return True

    @commands.Cog.listener(name="on_raw_reaction_add")
    @async_log_profiler
    async def emoji_translate_listener(self, payload):
        """
        Translates a Message when you add a Flag Emoji to it.
        The flag emoji represents the language you want the message translated to.
        The translated message is then send to you via DM.

        """

        if await self._emoji_translate_checks(payload) is False:
            return
        channel = self.bot.get_channel(payload.channel_id)
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.errors.NotFound:
            return
        country_code = self.language_emoji_map.get(normalize_emoji(payload.emoji.name))

        if message.embeds != []:
            log.debug('translating embed')
            await self.translate_embed(payload.member, channel, message, message.embeds[0], country_code)
            return

        translated = self.translator.translate(text=message.content, dest=country_code, src="auto")
        # TODO: Make embed with Hyperlink
        await payload.member.send(f"{message.jump_url}\n**in {LANGUAGES.get(country_code)}:**\n {translated.text.strip('.')}", allowed_mentions=AllowedMentions.none())

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

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def translate(self, ctx, to_language_id: Optional[LanguageConverter] = "english", *, text_to_translate: str):
        """
        Translates text into multiple different languages.

        Tries to auto-guess input language.

        Args:
            text_to_translate (str): the text to translate, quotes are optional
            to_language_id (Optional[LanguageConverter], optional): either can be the name of the language or an language code (iso639-1 language codes). Defaults to "english".

        Example:
                @AntiPetros translate german This is the Sentence to translate

        Info:
            Your invoking message gets deleted!
        """
        translated = self.translator.translate(text=text_to_translate, dest=to_language_id, src="auto")

        await ctx.send(f"__from {ctx.author.display_name}:__ *{translated.text}*")
        await ctx.message.delete()

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role()
    @commands.cooldown(1, 120, commands.BucketType.channel)
    async def available_languages(self, ctx: commands.Context):
        """
        Sends a list of all available languages, that can be used with the `translate` command.

        Example:
            @AntiPetros available_languages

        Info:
            Your invoking message gets deleted and after 120 seconds the message with the list of languages gets deleted too.
        """
        text = ListMarker.make_list(list(LANGUAGES.values()))

        await ctx.send(text, delete_after=120, allowed_mentions=discord.AllowedMentions.none())
        await delete_message_if_text_channel(ctx)
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

    def cog_check(self, ctx):
        return True

    async def cog_command_error(self, ctx, error):
        pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name

    # def cog_unload(self):
    #     log.debug("Cog '%s' UNLOADED!", str(self))

# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(TranslateCog(bot))
