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

from discord.ext import commands


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.exceptions import FaqNumberParseError, FaqQuestionParseError, FaqAnswerParseError, ClassAttributesNotSetError
# endregion[Imports]

# region [TODO]


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

    def __init__(self, raw_content: str, created_at: datetime, url: str, image: discord.Attachment = None) -> None:
        self._check_class_attr()
        self._raw_content = raw_content
        self.creation_date_time = created_at
        self.url = url
        self._image = image
        self.number = self._get_number()

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

    @async_property
    async def question(self):
        question_match = self.question_regex.search(self._raw_content)
        if question_match:
            question_emoji = self.question_parse_emoji if self.question_emoji is None else self.question_emoji
            return f"{question_emoji} {question_match.group('question').strip()}"
        else:
            raise FaqQuestionParseError(self._raw_content, self.url)

    @async_property
    async def answer(self):
        answer_match = self.answer_regex.search(self._raw_content)
        if answer_match:
            answer_emoji = self.answer_parse_emoji if self.answer_emoji is None else self.answer_emoji
            answer = answer_match.group('answer').strip()
            return f"{answer_emoji} {answer}"
        else:
            raise FaqAnswerParseError(self._raw_content, self.url)

    @async_property
    async def image(self):
        if self._image is None:
            return None
        return self._image.url

    @async_cached_property
    async def number_image(self):
        return await self.bot.execute_in_thread(self._make_number_image, self.number)

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
        draw.text(((width - w) / 2, (height - h) / 2), number_string, fill=self.bot.color('white').rgb, stroke_width=width // 25, stroke_fill=(0, 0, 0), font=font)
        return image

    async def to_embed_data(self):
        author = {"name": f"FAQ No {self.number} 🔗", "url": self.url, "icon_url": self.antistasi_icon}
        return await self.bot.make_generic_embed(author=author,
                                                 thumbnail=await self.number_image,
                                                 image=await self.image,
                                                 title=await self.question,
                                                 description=await self.answer + '\n\n' + self.faq_channel.mention,
                                                 timestamp=self.creation_date_time,
                                                 color="random")


        # region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
