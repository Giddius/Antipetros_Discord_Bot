
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import gc
import os
import asyncio
import unicodedata
from datetime import datetime
import re
from typing import List, Tuple, Set, Union, Optional

import random
from io import BytesIO
from textwrap import indent, dedent
# * Third Party Imports --------------------------------------------------------------------------------->
import aiohttp
from jinja2 import BaseLoader, Environment
import discord
from discord import File, Embed, DiscordException
from discord.ext import tasks, commands
from async_property import async_property
from PIL import Image, ImageDraw, ImageFont
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from icecream import ic
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.misc import CogConfigReadOnly, day_to_second, save_commands, hour_to_second, minute_to_second, make_config_name
from antipetros_discordbot.utility.enums import RequestStatus
from antipetros_discordbot.utility.checks import log_invoker, allowed_channel_and_allowed_role_2, command_enabled_checker, allowed_requester, owner_or_admin
from antipetros_discordbot.utility.named_tuples import LINK_DATA_ITEM
from antipetros_discordbot.utility.embed_helpers import EMBED_SYMBOLS, make_basic_embed

from antipetros_discordbot.utility.gidtools_functions import writeit, loadjson, pathmaker, writejson, clearit, appendwriteit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import CogState
from antipetros_discordbot.utility.replacements import auto_meta_info_command
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

COG_NAME = 'FaqCog'

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]

# region [Helper]

_from_cog_config = CogConfigReadOnly(CONFIG_NAME)

# endregion [Helper]


class FaqCog(commands.Cog, command_attrs={'name': COG_NAME, "description": ""}):

    """
    Creates Embed FAQ items.

    """
# region [ClassAttributes]
    config_name = CONFIG_NAME
    faq_data_file = APPDATA["cleaned_faqs.json"]
    templated_faq_data_file = APPDATA["templated_faq.json"]
    q_emoji = "🇶"
    a_emoji = "🇦"
    faq_symbol = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/FAQ_icon.svg/1280px-FAQ_icon.svg.png"
    embed_color = "blue"

    docattrs = {'show_in_readme': True,
                "is_ready": (CogState.WORKING | CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 03:33:42",
                             "6e72c93ce50bf8f6a95d55b1a8c1c8b51588f5a804902c2ba57c9f5b2afe3f35b31b5bc52d3f6a71b1a887e82345453771c797b53e41780e4beaff3388b64331")}

    required_config_data = dedent("""
                                        use_templated_faq = yes
                                        faq_channel = faq
                                        numbers_background_image = faq_num_background.png
                                        antistasi_decoration_pre = **
                                        antistasi_decoration_corpus = Antistasi
                                        antistasi_decoration_post = **
                                        link_decoration_pre =
                                        link_decoration_post =
                                        step_decoration_pre =
                                        step_decoration_post =
                                        number = 1️⃣, 2️⃣, 3️⃣, 4️⃣, 5️⃣, 6️⃣, 7️⃣, 8️⃣, 9️⃣
                                        emphasis_decoration_pre = ***
                                        emphasis_decoration_post = ***""")


# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot):

        self.bot = bot
        self.support = self.bot.support
        self.faq_image_folder = APPDATA['faq_images']
        self.faq_embeds = {}
        self.jinja_env = Environment(loader=BaseLoader())
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def use_templated(self):
        return COGS_CONFIG.retrieve(self.config_name, 'use_templated_faq', typus=bool, direct_fallback=False)

    @property
    def all_faq_data(self):
        return loadjson(self.faq_data_file)

    @property
    def template_vars(self):
        return {"antistasi_decoration": {"pre": COGS_CONFIG.retrieve(self.config_name, 'antistasi_decoration_pre', typus=str, direct_fallback=""),
                                         "corpus": COGS_CONFIG.retrieve(self.config_name, 'antistasi_decoration_corpus', typus=str, direct_fallback="Antistasi"),
                                         "post": COGS_CONFIG.retrieve(self.config_name, 'antistasi_decoration_post', typus=str, direct_fallback="")},
                "link_decoration": {"pre": COGS_CONFIG.retrieve(self.config_name, 'link_decoration_pre', typus=str, direct_fallback=""),
                                    "post": COGS_CONFIG.retrieve(self.config_name, 'link_decoration_post', typus=str, direct_fallback="")},
                "step_decoration": {"pre": COGS_CONFIG.retrieve(self.config_name, 'step_decoration_pre', typus=str, direct_fallback=""),
                                    "post": COGS_CONFIG.retrieve(self.config_name, 'step_decoration_post', typus=str, direct_fallback="")},
                "emphasis_decoration": {"pre": COGS_CONFIG.retrieve(self.config_name, 'emphasis_decoration_pre', typus=str, direct_fallback=""),
                                        "post": COGS_CONFIG.retrieve(self.config_name, 'emphasis_decoration_post', typus=str, direct_fallback="")},
                "number": COGS_CONFIG.retrieve(self.config_name, 'number', typus=list, direct_fallback="['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20']")}


# endregion [Properties]

# region [Setup]


    async def on_ready_setup(self):
        # await self._load_faq_embeds()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]

# !Proof of concept currently diabled, seems to be only way to be sure

    # @commands.Cog.listener(name='on_message')
    # async def answer_vindicta_mention(self, msg):
    #     if msg.author.bot is True:
    #         return
    #     if any(role.name == 'Member' for role in msg.author.roles):
    #         return
    #     channel = msg.channel
    #     log.debug("answer invicta invoked")
    #     if channel.name not in COGS_CONFIG.getlist(CONFIG_NAME, 'allowed_channels'):
    #         return
    #     log.debug("is correct channel")
    #     content = msg.content

    #     if "vindicta" in content.casefold().split():
    #         log.debug("vindicta in message")
    #         await channel.send(embed=self.faq_embeds.get(1).copy())
    #         await channel.send("this should only be an example of how the bot can react, normaly there is an check if it was said by an member and also a check so it only triggers with new users (it checks the join time). The faq is an example faq of one that would deal with vindicta stuff or you can use a message")

# endregion [Listener]

# region [Commands]


    @auto_meta_info_command(enabled=get_command_enabled('post_faq_by_number'))
    @ allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def post_faq_by_number(self, ctx, faq_numbers: commands.Greedy[int], as_template: bool = None):
        """
        Posts an FAQ as an embed on request.

        Either as an normal message or as an reply, if the invoking message was also an reply.

        Deletes invoking message

        Args:
            faq_numbers (commands.Greedy[int]): minimum one faq number to request, maximum as many as you want seperated by one space (i.e. 14 12 3)
            as_template (bool, optional): if the resulting faq item should be created via the templated items or from the direct parsed faqs.
        """
        as_template = self.use_templated if as_template is None else as_template
        for faq_number in faq_numbers:
            faq_number = str(faq_number)

            if faq_number not in self.all_faq_data:
                await ctx.send(f'No FAQ Entry with the number {faq_number}')
                continue
            embed_data = await self.make_faq_embed(faq_number, from_template=as_template)
            if ctx.message.reference is not None:

                await ctx.send(**embed_data, reference=ctx.message.reference)
            else:
                await ctx.send(**embed_data)
        await ctx.message.delete()

    @auto_meta_info_command(enabled=get_command_enabled("create_faqs_as_embed"))
    @ owner_or_admin()
    @ log_invoker(logger=log, level="info")
    @ commands.cooldown(1, minute_to_second(5), commands.BucketType.channel)
    async def create_faqs_as_embed(self, ctx: commands.Context, as_template: bool = None):
        """
        Posts all faqs ,that it has saved, at once and posts a TOC afterwards.

        Intended to recreate the FAQ's as embeds, or after changing an FAQ to rebuild it

        Args:
            as_template (bool, optional): if the resulting faq item should be created via the templated items or from the direct parsed faqs.
        """
        link_data = []
        as_template = self.use_templated if as_template is None else as_template
        delete_after = None
        async with ctx.typing():
            for faq_number in self.all_faq_data:

                embed_data = await self.make_faq_embed(faq_number, with_author=False, from_template=as_template)
                await ctx.send(f'**{"┳"*30}**', delete_after=delete_after)
                faq_message = await ctx.send(**embed_data, delete_after=delete_after)
                await ctx.send(f'**{"┻"*30}**\n{ZERO_WIDTH}', delete_after=delete_after)
                question = self.all_faq_data[faq_number] if as_template is False else await self.process_template_faq_data(faq_number)
                question = question['content'].get('question')
                link_data.append((faq_number, question, faq_message.jump_url))
                if faq_number != list(self.all_faq_data)[-1]:
                    await asyncio.sleep(random.randint(1, 3) / random.randint(1, 3))
        await self._make_toc(ctx, link_data=link_data)

    @auto_meta_info_command(enabled=get_command_enabled("add_faq_item"))
    @allowed_channel_and_allowed_role_2(in_dm_allowed=True)
    async def add_faq_item(self, ctx: commands.Context, faq_number: Optional[int] = None, from_message: Optional[discord.Message] = None):
        """
        UNFINISHED

        Args:
            faq_number (Optional[int], optional): [description]. Defaults to None.
            from_message (Optional[discord.Message], optional): [description]. Defaults to None.
        """
        if len(ctx.message.attachments) == 0 and from_message is None:
            await ctx.author.send('no input for faq creation, you either need to specify a message to convert or attach an template file')
            return
        if len(ctx.message.attachments) != 0 and from_message is not None:
            await ctx.author.send('either attach a template file or specify a message to convert, both at the same time is not possible')
            return
        if faq_number is None:
            faq_number = len(self.all_faq_data) + 1

    # TODO: Needs reimplementation to make backup and to also read embeds
    # @ commands.command(aliases=get_aliases("get_current_faq_data"), enabled=get_command_enabled("get_current_faq_data"))
    # async def get_current_faq_data(self, ctx: commands.Context):
    #     channel = await self.bot.channel_from_name(COGS_CONFIG.retrieve(self.config_name, "faq_channel", typus=str, direct_fallback='faq'))
    #     faq_num_regex = re.compile(r"\*\*FAQ No (?P<faq_number>\d+)", re.IGNORECASE)
    #     del_time = 30
    #     data = {}
    #     async for message in channel.history():

    #         match = faq_num_regex.match(message.content)
    #         if match:
    #             faq_number = int(match.groupdict().get('faq_number'))
    #             files = []
    #             for attachment in message.attachments:
    #                 file_name = f"faq_{faq_number}_{attachment.filename}"
    #                 path = pathmaker(self.faq_image_folder, file_name)
    #                 with open(path, 'wb') as f:
    #                     await attachment.save(f)
    #                     files.append(file_name)

    #             data[faq_number] = {"content": message.content, "files": files, "created_datetime": message.created_at.strftime(self.bot.std_date_time_format), "link": message.jump_url}
    #     writejson(data, pathmaker(APPDATA['json_data'], "raw_faqs.json"))
    #     await self._transform_raw_faq_data(data)
    #     await ctx.send('Done')


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [Embeds]


# endregion [Embeds]

# region [HelperMethods]


    async def _transform_raw_faq_data(self, data):
        new_data = {}
        clearit('check_faq.txt')
        for faq_number, faq_data in data.items():
            appendwriteit('check_faq.txt', faq_data.get('content') + f'\n\n{"#"*50}\n\n')
            new_data[faq_number] = faq_data
            title, content = faq_data.get('content').replace(u'\ufeff', '').split('\n🇶')
            question_content, answer_content = content.split('\n🇦')
            new_data[faq_number]['content'] = {"title": title, "question": question_content, "answer": answer_content}
        writejson(new_data, pathmaker(APPDATA['json_data'], 'cleaned_faqs.json'))

    @ staticmethod
    def _get_text_dimensions(text_string, font):
        # https://stackoverflow.com/a/46220683/9263761
        ascent, descent = font.getmetrics()

        text_width = font.getmask(text_string).getbbox()[2]
        text_height = font.getmask(text_string).getbbox()[3] + descent

        return (text_width, text_height)

    def _make_perfect_fontsize(self, text, image_width, image_height):
        padding_width = image_width // 5
        padding_height = image_height // 5
        font_size = 16
        font = ImageFont.truetype(APPDATA['stencilla.ttf'], font_size)
        text_size = self._get_text_dimensions(text, font)
        while text_size[0] <= (image_width - padding_width) and text_size[1] <= (image_height - padding_height):
            font_size += 1
            font = ImageFont.truetype(APPDATA['stencilla.ttf'], font_size)
            text_size = self._get_text_dimensions(text, font)

        return ImageFont.truetype(APPDATA['stencilla.ttf'], font_size - 1)

    def _make_number_image(self, number: int):
        number_string = str(number)
        image = Image.open(APPDATA[COGS_CONFIG.retrieve(self.config_name, 'numbers_background_image', typus=str, direct_fallback="ASFlagexp.png")]).copy()
        width, height = image.size
        font = self._make_perfect_fontsize(number_string, width, height)
        draw = ImageDraw.Draw(image)
        w, h = draw.textsize(number_string, font=font)
        h += int(h * 0.01)
        draw.text(((width - w) / 2, (height - h) / 2), number_string, fill=self.support.color('white').rgb, stroke_width=width // 25, stroke_fill=(0, 0, 0), font=font)
        return image

    async def make_faq_embed(self, faq_number, with_author: bool = True, with_image: bool = True, from_template: bool = False):

        faq_data = self.all_faq_data.get(faq_number) if from_template is False else await self.process_template_faq_data(faq_number)

        question = f"{self.q_emoji} {faq_data['content'].get('question').strip()}"

        answer = f"{ZERO_WIDTH} \n {self.a_emoji}\n{faq_data['content'].get('answer').strip()}\n{ZERO_WIDTH}"
        author = "not_set"
        if with_author is True:
            author = {"name": f"FAQ No {faq_number}", "url": faq_data.get('link'), "icon_url": "https://pbs.twimg.com/profile_images/1123720788924932098/C5bG5UPq.jpg"}

        embed_data = await self.bot.make_generic_embed(author=author,
                                                       thumbnail=await self.bot.execute_in_thread(self._make_number_image, faq_number) if with_image is True else "no_thumbnail",
                                                       image=APPDATA[faq_data.get('file')] if faq_data.get('file') != "" else None,
                                                       title=question,
                                                       description=answer,
                                                       footer="not_set",
                                                       timestamp=datetime.strptime(faq_data.get('creation_time'), self.bot.std_date_time_format),
                                                       color="random")
        return embed_data

    async def process_template_faq_data(self, faq_number):
        raw_data = loadjson(self.templated_faq_data_file).get(str(faq_number))

        question_template = self.jinja_env.from_string(raw_data['content'].get('question'))
        raw_data['content']['question'] = question_template.render(**self.template_vars)
        answer_template = self.jinja_env.from_string(raw_data['content'].get('answer'))
        raw_data['content']['answer'] = answer_template.render(**self.template_vars)
        return raw_data

    async def _number_with_emojis(self, number: int):
        digit_emojis = {"0": "0️⃣",
                        "1": "1️⃣",
                        "2": "2️⃣",
                        "3": "3️⃣",
                        "4": "4️⃣",
                        "5": "5️⃣",
                        "6": "6️⃣",
                        "7": "7️⃣",
                        "8": "8️⃣",
                        "9": "9️⃣"}
        _out = ""
        for char in str(number):
            _out += digit_emojis.get(char)
        return _out

    async def _make_toc(self, ctx, link_data: List[Tuple[int, str, str]]):
        fields = []
        for faq_number, question, link in link_data:
            faq_emoji_number = await self._number_with_emojis(int(faq_number))
            fields.append(self.bot.field_item(name=f"No. {faq_emoji_number} {ZERO_WIDTH} {question}", value=f"{link} 🔗\n{ZERO_WIDTH}", inline=False))

        async for embed_data in self.bot.make_paginatedfields_generic_embed(title="FAQ Table of Contents", fields=fields):
            await ctx.send(**embed_data)
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
    bot.add_cog(attribute_checker(FaqCog(bot)))
