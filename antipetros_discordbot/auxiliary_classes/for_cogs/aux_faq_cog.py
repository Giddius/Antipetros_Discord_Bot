"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

import os
from datetime import datetime
import re
# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->
from PIL import Image, ImageDraw, ImageFont
from async_property import async_property, async_cached_property
import discord
import asyncio
from discord.ext import commands


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.gidtools_functions import pathmaker
from antipetros_discordbot.utility.exceptions import FaqNumberParseError, FaqQuestionParseError, FaqAnswerParseError, ClassAttributesNotSetError
# endregion[Imports]

# region [TODO]

# TODO: Refractor and sort whole image logic

# TODO: Maybe better parser

# TODO: check if asyncio image creation or to_thread image creation is better

# endregion [TODO]

# region [AppUserData]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class FaqItem:
    __slots__ = ("_raw_content",
                 "creation_date_time",
                 "url",
                 "_image",
                 "number",
                 "_number_thumbnail",
                 "question",
                 "answer")
    bot = None
    faq_channel = None
    question_parse_emoji = "🇶"
    answer_parse_emoji = "🇦"
    question_emoji = None
    answer_emoji = None
    config_name = None
    number_regex = re.compile(r".*?FAQ No.*?(?P<faq_number>\d+)", re.IGNORECASE)
    question_regex = re.compile(r"🇶(?P<question>.*)")
    answer_regex = re.compile(r"🇦(?P<answer>.*)", re.DOTALL)
    background_image = None
    start_font_size = 125

    def __init__(self, raw_content: str, created_at: datetime, url: str, image: discord.Attachment = None) -> None:
        self._check_class_attr()
        self._raw_content = str(raw_content)
        self.creation_date_time = created_at
        self.url = url
        self._image = image
        self.number = self._get_number()
        self._number_thumbnail = None
        self.question = self._get_question()
        self.answer = self._get_answer()

    @classmethod
    def set_background_image(cls):

        image_name = COGS_CONFIG.retrieve(cls.config_name, 'numbers_background_image', typus=str, direct_fallback="ASFlagexp.png")
        image_path = APPDATA[image_name]
        cls.background_image = Image.open(image_path).copy()

    def _check_class_attr(self):
        if self.bot is None:
            raise ClassAttributesNotSetError('bot')
        if self.question_parse_emoji is None:
            raise ClassAttributesNotSetError('question_parse_emoji')
        if self.answer_parse_emoji is None:
            raise ClassAttributesNotSetError('answer_parse_emoji')
        if self.config_name is None:
            raise ClassAttributesNotSetError('config_name')

    def _get_number(self):
        number_match = self.number_regex.match(self._raw_content)
        if number_match:
            return int(number_match.group('faq_number'))
        else:
            raise FaqNumberParseError(self._raw_content, self.url)

    @property
    def antistasi_icon(self):
        return BASE_CONFIG.retrieve('embeds', 'antistasi_author_icon', typus=str, direct_fallback="https://pbs.twimg.com/profile_images/1123720788924932098/C5bG5UPq.jpg")

    def _get_question(self):
        question_match = self.question_regex.search(self._raw_content)
        if question_match:
            question_emoji = self.question_parse_emoji if self.question_emoji is None else self.question_emoji
            return f"{question_emoji} {question_match.group('question').strip()}"
        else:
            raise FaqQuestionParseError(self._raw_content, self.url)

    def _get_answer(self):
        answer_match = self.answer_regex.search(self._raw_content)
        if answer_match:
            answer_emoji = self.answer_parse_emoji if self.answer_emoji is None else self.answer_emoji
            answer = answer_match.group('answer').strip()
            return f"{answer_emoji} {answer}"
        else:
            raise FaqAnswerParseError(self._raw_content, self.url)

    @property
    def image(self):
        if self._image is None:
            return None
        return self._image.url

    async def get_number_thumbnail(self):
        if self._number_thumbnail is None:
            self._number_thumbnail = await self._make_number_image()
        return self._number_thumbnail

    async def _get_text_dimensions(self, font):
        # https://stackoverflow.com/a/46220683/9263761
        text_string = str(self.number)
        ascent, descent = font.getmetrics()

        text_width = font.getmask(text_string).getbbox()[2]
        await asyncio.sleep(0)
        text_height = font.getmask(text_string).getbbox()[3] + descent

        return (text_width, text_height)

    async def _make_perfect_fontsize(self, image_width, image_height):
        padding_width = image_width // 5
        padding_height = image_height // 5
        font_size = self.start_font_size
        font = ImageFont.truetype(APPDATA['stencilla.ttf'], font_size)
        text_size = await self._get_text_dimensions(font)
        while text_size[0] <= (image_width - padding_width) and text_size[1] <= (image_height - padding_height):
            font_size += await asyncio.sleep(0, 2)
            font = ImageFont.truetype(APPDATA['stencilla.ttf'], font_size)
            text_size = await self._get_text_dimensions(font)

        return ImageFont.truetype(APPDATA['stencilla.ttf'], font_size - 2)

    async def _make_number_image(self):
        number_string = str(self.number)
        image = self.background_image.copy()
        width, height = image.size
        font = await self._make_perfect_fontsize(width, height)
        draw = await asyncio.to_thread(ImageDraw.Draw, image)
        w, h = await asyncio.to_thread(draw.textsize, number_string, font=font)
        h += int(h * 0.01)
        await asyncio.to_thread(draw.text, ((width - w) / 2, (height - h) / 2), number_string, fill=self.bot.color('white').rgb, stroke_width=width // 25, stroke_fill=(0, 0, 0), font=font)

        return image

    async def to_embed_data(self):
        author = {"name": f"FAQ No {self.number} 🔗", "url": self.url, "icon_url": self.antistasi_icon}
        return await self.bot.make_generic_embed(author=author,
                                                 thumbnail=await self.get_number_thumbnail(),
                                                 image=self.image,
                                                 title=self.question,
                                                 description=self.answer + '\n\n' + self.faq_channel.mention,
                                                 timestamp=self.creation_date_time,
                                                 color="random",
                                                 typus="faq_embed")

    def __repr__(self):
        return f"{self.__class__.__name__}(number={self.number},question={self.question})"


        # region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
