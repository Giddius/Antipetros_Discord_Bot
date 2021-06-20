

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import re
import json
from datetime import datetime, timedelta, timezone
from pprint import pformat
import random
from dotenv import load_dotenv
from io import StringIO, BytesIO
import asyncio
import tempfile
import webbrowser
from discord.ext.commands import Greedy
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance
from itertools import chain
import inspect
from typing import Optional
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import commands, flags, tasks
from emoji import demojize, emojize, emoji_count
from emoji.unicode_codes import EMOJI_UNICODE_ENGLISH
from webdav3.client import Client
from typing import TYPE_CHECKING, Union
from weasyprint import HTML, CSS
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import generate_bot_data, delete_message_if_text_channel
from antipetros_discordbot.utility.gidtools_functions import writejson, loadjson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus, ContextAskAnswer
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, auto_meta_info_command, AntiPetrosBaseCommand
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ListMarker
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock
from antipetros_discordbot.utility.converters import CommandConverter, SeparatedListConverter, RoleOrIntConverter
from antipetros_discordbot.utility.checks import has_attachments, has_image_attachment
from pyyoutube import Api
from antipetros_discordbot.utility.sqldata_storager import general_db
from marshmallow import Schema
from rich import inspect as rinspect
from itertools import chain
from rich.console import Console
from antipetros_discordbot.schemas.bot_schema import AntiPetrosBotSchema
import ftfy
from hashlib import blake2b
import json
from antipetros_discordbot.auxiliary_classes.asking_items import AskConfirmation, AskInput, AskFile, AskInputManyAnswers
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
    from antipetros_discordbot.engine.replacements.context_replacement import AntiPetrosBaseContext
# endregion [Imports]

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


# endregion [Constants]

# region [TODO]

# TODO: create regions for this file
# TODO: Document and Docstrings


# endregion [TODO]

class RoleSchema(Schema):

    class Meta:
        additional = ("id", "name", "mentionable", "position", 'created_at', 'hoist')


class GeneralDebugCog(AntiPetrosBaseCog, command_attrs={'hidden': True}):
    """
    Cog for debug or test commands, should not be enabled fo normal Bot operations.
    """

    public = False
    meta_status = CogMetaStatus.WORKING | CogMetaStatus.OPEN_TODOS | CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.NEEDS_REFRACTORING | CogMetaStatus.DOCUMENTATION_MISSING | CogMetaStatus.FOR_DEBUG

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.ready = False
        self.bob_user = None
        self.antidevtros_member = None
        self.antipetros_member = None
        self.edit_embed_message = None
        self.general_db = general_db
        self.attachment_type_file = pathmaker(APPDATA['debug'], "attachment_types.json")
        if os.path.isfile(self.attachment_type_file) is False:
            writejson([], self.attachment_type_file)
        glog.class_init_notification(log, self)

    @commands.Cog.listener(name='on_message')
    async def collect_attachment_types(self, message: discord.Message):
        if os.getenv("COLLECT_ATTACHMENT_TYPES_ENABLED", "0") != "1":
            return
        collected_types = []
        if message.attachments is not None and len(message.attachments) > 0:
            for attachment in message.attachments:
                collected_types.append(attachment.content_type)

        data = loadjson(self.attachment_type_file).copy()
        data += collected_types
        data = list(set(data))

        writejson(data, self.attachment_type_file)
        log.debug("collected attachment data types %s", ','.join(collected_types))

    async def on_ready_setup(self):

        self.bob_user = await self.bot.fetch_antistasi_member(346595708180103170)
        for member in self.bot.antistasi_guild.members:
            if member.bot is True:
                if member.display_name.casefold() == 'antidevtros':
                    self.antidevtros_member = member

                elif member.display_name.casefold() == 'antipetros':
                    self.antipetros_member = member
                else:
                    if self.antidevtros_member is not None and self.antipetros_member is not None:
                        break
        await generate_bot_data(self.bot, self.antipetros_member)

        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):

        log.debug('cog "%s" was updated', str(self))

    @auto_meta_info_command()
    async def tell_sub_supporter(self, ctx: commands.Context):
        text = ListMarker.make_list([str(sub_sup) for sub_sup in self.bot.support.subsupports])
        await ctx.send(text, allowed_mentions=discord.AllowedMentions.none(), delete_after=120)

    @ auto_meta_info_command()
    async def dump_bot(self, ctx: commands.Context):
        schema = AntiPetrosBotSchema()
        data = schema.dump(self.bot)
        with open('bot_dump.json', 'w') as f:
            f.write(json.dumps(data, default=str, sort_keys=True, indent=4))

        await ctx.send('done')

    @ auto_meta_info_command()
    async def cached_msgs(self, ctx: commands.Context):
        data = list(map(lambda x: x.content, self.bot.cached_messages))
        writejson(data, "cached_msgs.json")

    @ auto_meta_info_command()
    async def save_msg(self, ctx: commands.Context, channel: discord.TextChannel, message_id: int):
        msg = await channel.fetch_message(message_id)
        with open(str(message_id) + ".txt", 'w', encoding='utf-8', errors='ignore') as f:
            f.write(msg.content)
        writejson(msg.content, str(message_id) + '.json')
        await ctx.send('done')

    @auto_meta_info_command()
    async def say_bot_emoji(self, ctx: commands.Context):
        for name in self.bot.color_emoji_id_map:
            await ctx.send(await self.bot.get_color_emoji(name))

    @auto_meta_info_command()
    async def force_reconnect(self, ctx: commands.Context, seconds: int, times: int = 2):
        import time
        for i in range(times):
            time.sleep(seconds)
            await ctx.send(f"slept blocking for {seconds} seconds")

    @auto_meta_info_command()
    async def say_best_alias(self, ctx: commands.Context, command: CommandConverter):
        await ctx.send(command.best_alias)

    @auto_meta_info_command()
    async def taken_colors(self, ctx: commands.Context):
        taken = []
        for cog_name, cog_object in sorted(self.bot.cogs.items(), key=lambda x: (x[1].color != 'default', x[1].color)):
            color_emoji = await self.bot.get_color_emoji(cog_object.color)
            await ctx.send(f"{cog_name} | {color_emoji} | {cog_object.color}")
            if cog_object.color in taken and cog_object.color != 'default':
                await ctx.send(f"duplicate color {cog_object.color}")
            taken.append(cog_object.color)
        not_taken = []
        taken = set(taken)
        for color in self.bot.color_emoji_id_map:
            if color not in taken:
                not_taken.append(color)
        await ctx.send('\n'.join(not_taken))

    @auto_meta_info_command()
    async def other_guild_emojis(self, ctx: commands.Context):
        x = {}
        for _emoji in self.bot.bot_testing_guild.emojis:
            name = _emoji.name.casefold()
            if name not in {'antidevtros', 'link_emoji'}:
                x[_emoji.name.casefold()] = _emoji.id
        x['default'] = 839782169303449640
        x = {key: value for key, value in sorted(x.items(), key=lambda x: (x[0] != 'default', x[0]))}
        await ctx.send(CodeBlock(pformat(x, sort_dicts=False), "python"))

    @ auto_meta_info_command()
    async def dump_roles(self, ctx: commands.Context):
        async with ctx.typing():
            schema = RoleSchema()

            with open('role_dump.json', 'w') as f:
                f.write(schema.dumps(list(self.bot.antistasi_guild.roles), many=True))
            await ctx.send('done', delete_after=90, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    async def separated_list_converter_test(self, ctx: commands.Context, *, the_list: SeparatedListConverter(value_type=RoleOrIntConverter(), separator=',', strip_whitespace=True)):
        await ctx.send(ListMarker.make_list(the_list), allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    async def check_message_existing(self, ctx: commands.Context, channel_id: int, message_id: int):
        try:
            await ctx.send(await self.bot.get_message_directly(channel_id, message_id), allowed_mentions=discord.AllowedMentions.none())
        except discord.errors.NotFound as e:
            await ctx.send(e, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    async def check_context(self, ctx: commands.Context):
        async with ctx.continous_typing():
            await ctx.send(str(self.bot))
            await ctx.send(self.bot.creator.mention)

            console = Console(soft_wrap=True, record=True)
            rinspect(ctx, console=console, help=True, all=True)

    @auto_meta_info_command()
    async def check_ask_confirmation(self, ctx):
        answer = await ctx.ask_confirmation("this is a test of the confirmation-method", 60.0)
        await ctx.send(str(answer))
        await delete_message_if_text_channel(ctx)

    @auto_meta_info_command(clear_invocation=True)
    async def check_ask_selection(self, ctx: commands.Context):
        faq_cog = self.bot.cogs.get('FaqCog')

        options = [ctx.option_item(faq_item, name=faq_item.number, description=lambda x:CodeBlock(x.question, "fix"), emoji=faq_item.number) for faq_item in list(faq_cog.faq_items.values())[:10]]

        emojis = list(self.bot.antistasi_guild.emojis)
        random.shuffle(emojis)
        answer = await ctx.ask_selection(description="this is a test of the selection-method", options=options, update_time_left=True, timeout=350)
        if answer in {ContextAskAnswer.NOANSWER, ContextAskAnswer.CANCELED}:
            await ctx.send(answer.name)
            return
        await ctx.send(answer.answer)

    @auto_meta_info_command()
    async def check_ask_input(self, ctx: commands.Context):
        validator = re.compile(r"\*\*.*?\*\*")
        answer = await ctx.ask_input(description='this is a test', validator=validator, case_insensitive=True, timeout=60)
        await ctx.send(answer)

    @auto_meta_info_command()
    async def check_voice_channel_members(self, ctx: commands.Context, voice_channel: discord.VoiceChannel):
        await ctx.send(ListMarker.make_list(member.mention for member in voice_channel.members))

    @auto_meta_info_command()
    async def check_rpc(self, ctx: commands.Context):
        info = await self.bot.application_info()
        from rich import inspect as rinspect
        from rich.console import Console

        temp_console = Console(soft_wrap=True, record=True)
        rinspect(info, all=True, console=temp_console)

        await self.bot.split_to_messages(ctx, temp_console.export_text(), in_codeblock=True, syntax_highlighting="python")
    # def cog_unload(self):
    #     log.debug("Cog '%s' UNLOADED!", str(self))

    @auto_meta_info_command()
    async def concept_report(self, ctx: commands.Context):
        log.critical("%s concept report run was started by %s %s", "!" * 10, ctx.author.name, "!" * 10)

        async def error_answers(answer):
            if answer is confirmation.CANCELED or answer is confirmation.DECLINED:
                await channel.send('Report was canceled')

            elif answer is confirmation.NOANSWER:
                await channel.send("report timed out")
        if ctx.channel.type is discord.ChannelType.private:
            channel = ctx.channel
        else:
            channel = await ctx.author.create_dm() if ctx.author.dm_channel is None else ctx.author.dm_channel
        author = ctx.author
        await delete_message_if_text_channel(ctx)
        confirmation = AskConfirmation(timeout=300, author=author, channel=channel)
        confirmation.description = "Do you want to report another player?"
        answer = await confirmation.ask()
        if answer in confirmation.error_answers or answer is confirmation.DECLINED:
            await error_answers(answer)
            return

        input_question = AskInput(timeout=300, author=author, channel=channel)
        input_question.description = "please state the name of the player"

        player_name = await input_question.ask()

        if player_name in input_question.error_answers:
            await error_answers(player_name)
            return

        files = []
        hook_files = []
        sec_input_question = AskInputManyAnswers(author=author, channel=channel, timeout=500)
        sec_input_question.description = "Please send your report"
        report = await sec_input_question.ask()
        if report in sec_input_question.error_answers:
            await error_answers(report)
            return
        if len(report) >= (self.bot.max_message_length - 100):
            with StringIO() as stringfile:
                stringfile.write(report)
                stringfile.seek(0)
                files.append(discord.File(stringfile, 'report.txt'))
                stringfile.seek(0)
                stringfile.write(report)
                stringfile.seek(0)
                hook_files.append(discord.File(stringfile, 'report.txt'))
            report = 'SEE FILE'
        file_input = AskFile(author=author, channel=channel, timeout=300)

        file_answer = await file_input.ask()
        if file_answer is file_input.CANCELED or file_answer is file_input.NOANSWER:
            await error_answers(file_input)
            return
        log.info(file_answer)

        for attachment in file_answer:
            files.append(await attachment.to_file())

        for attachment in file_answer:
            hook_files.append(await attachment.to_file())
        await self.bot.channel_from_id(645930607683174401).send(f"Report Concerning: `{player_name}`\n\nReport:\n>>> {report}", allowed_mentions=discord.AllowedMentions.none(), files=files)
        webhook = discord.Webhook.from_url("https://discord.com/api/webhooks/854749192189640734/kd3tmI17bErnc6egy8ObrdfV6-Rm79hkPxNFxBjeZDSp4wNv4llJ8EG-9_z_6Awv8Jeu", adapter=discord.AsyncWebhookAdapter(self.bot.aio_request_session))
        await webhook.send(f"Report from {author.mention}\n\nReport Concerning: `{player_name}`\n\nReport:\n>>> {report}", allowed_mentions=discord.AllowedMentions.none(), username="REPORT", avatar_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Warning.svg/1200px-Warning.svg.png", files=hook_files)

    @auto_meta_info_command()
    async def get_server_stati(self, ctx: commands.Context, channel: discord.TextChannel):
        await ctx.send(f'collecting all messages from channel {channel.name}')

        msgs = []
        counter = 0
        async for message in channel.history(limit=None, oldest_first=True):
            async with ctx.typing():
                serialized_message = {"author": {'id': message.author.id, 'name': message.author.name},
                                      "content": message.content,
                                      "created_at": message.created_at.isoformat(),
                                      "edited_at": None}
                if message.edited_at is not None:
                    serialized_message['edited_at'] = message.edited_at.isoformat()
                msgs.append(serialized_message)
                counter += 1
                if counter % 100 == 0:
                    await ctx.send(f"collected message number {counter}", delete_after=120)
                await asyncio.sleep(0)
        writejson(msgs, 'all_server_status_messages.json', sort_keys=False, default=str)
        await ctx.send(f'done, collected {len(msgs)} messages from channel {channel.name}', delete_after=120)

    @auto_meta_info_command()
    async def create_emoji_list(self, ctx: commands.Context):

        await ctx.send('starting command emoji-list', store=True)
        guild = self.bot.bot_testing_guild
        await ctx.send(f"bot-testing-guild is {guild.name}", store=True)

        category_name = 'data'

        category_channel = guild.get_channel(855904969962029098)
        await ctx.send(f"category {category_channel.name} found!", store=True)
        channel_name = "emoji-list"
        await ctx.send(f"creating channel {channel_name}", store=True)
        channel = await guild.create_text_channel(name=channel_name, topic="just and easy way to get emoji id's.", category=category_channel)
        await ctx.send(f"channel {channel.mention} created!", store=True)
        to_post = []
        await ctx.send("collecting emoji data", store=True)
        for emoji in chain(guild.emojis, self.bot.antistasi_guild.emojis):
            text = f"{str(emoji)} | name: {emoji.name} | id: {emoji.id} | guild_name: {emoji.guild.name} | created_at: {emoji.created_at.isoformat(timespec='seconds')} | animated: {emoji.animated} | url: <{emoji.url}> | roles: {emoji.roles}"
            text += '\n' + '─' * 25
            to_post.append(text)
            await asyncio.sleep(0)

        await ctx.send(f"posting emoji data for {len(to_post)} emojis in {channel.mention}", store=True)
        await self.bot.split_to_messages(channel, '\n'.join(to_post), in_codeblock=False, split_on='─' * 25)
        await ctx.send("finished", store=True)
        await ctx.delete_stored_messages(delay=30)
        await delete_message_if_text_channel(ctx)

    @auto_meta_info_command()
    async def server_info_check(self, ctx: commands.Context):
        cog = self.bot.get_cog("CommunityServerInfoCog")
        for s_name in ['mainserver_1', 'mainserver_2']:
            server_item = await cog._get_server_by_name(s_name)
            info = await server_item.get_info()
            info_dict = {name: value for name, value in inspect.getmembers(info) if not name.startswith('__')}
            with StringIO() as stringfile:
                stringfile.write(json.dumps(info_dict, indent=4, sort_keys=False, default=str))
                stringfile.seek(0)
                file = discord.File(stringfile, f"server_info_{s_name}.json")
            await ctx.send(file=file)

    async def _get_as_pil_image(self, attachment: discord.Attachment) -> Image.Image:
        with BytesIO() as bytefile:
            await attachment.save(bytefile)
            bytefile.seek(0)
            _image = Image.open(bytefile)
            _image.load()
        return _image

    def _resize_image(self, image: Image.Image, contrast: float, repeat_enhance: int, color_factor: float) -> Image.Image:
        width, height = image.size
        log.debug("Old width %s, old height %s", width, height)
        if width > height:
            factor = 218 / width
            new_size = (218, height * factor)
        else:
            factor = 218 / height
            new_size = (width * factor, 218)
        log.debug("new size is %s", new_size)

        image_contrast = ImageEnhance.Contrast(image)
        image = image_contrast.enhance(contrast)
        image_color = ImageEnhance.Color(image)
        image = image_color.enhance(color_factor)
        for i in range(repeat_enhance):
            image = image.filter(ImageFilter.DETAIL)
            image = image.filter(ImageFilter.SHARPEN)
            image = image.filter(ImageFilter.EDGE_ENHANCE)
        image.thumbnail(size=new_size, resample=Image.LANCZOS)
        return image

    async def _remove_emoji(self, emoji: discord.Emoji, delay: int = 120):
        await asyncio.sleep(delay)
        await emoji.delete()
        log.info("emoji %s was deleted", emoji)

    @auto_meta_info_command()
    @has_image_attachment(1)
    async def new_emoji(self, ctx: commands.Context, contrast: float, repeat_enhance: int, color_factor: float, *, names: str = None):
        names = [] if names is None else [name for name in names.split() if name != ""]
        for attachment in ctx.message.attachments:
            name = attachment.filename.casefold() if not names else names.pop(0).casefold()
            image = await self._get_as_pil_image(attachment)
            mod_image = await asyncio.to_thread(self._resize_image, image, contrast, repeat_enhance, color_factor)
            with BytesIO() as bytefile:
                mod_image.save(bytefile, format="PNG")
                bytefile.seek(0)
                byte_image = bytefile.read()

            emoji = await self.bot.bot_testing_guild.create_custom_emoji(name=name, image=byte_image)
            await ctx.send(emoji)
            asyncio.create_task(self._remove_emoji(emoji))

    async def cog_check(self, ctx):
        # if ctx.author.id == 576522029470056450:
        #     return True
        # return False
        return True


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(GeneralDebugCog(bot))
