"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import traceback
from datetime import datetime
from typing import Tuple
import re
# * Third Party Imports --------------------------------------------------------------------------------->
from discord import Embed, ChannelType
from fuzzywuzzy import fuzz
from fuzzywuzzy import process as fuzzprocess
from discord.ext import commands
import discord
import asyncio
from io import BytesIO
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from rich import inspect as rinspect
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import async_seconds_to_pretty_normal, async_split_camel_case_string
from antipetros_discordbot.utility.exceptions import MissingAttachmentError, NotNecessaryRole, IsNotTextChannelError, NotNecessaryDmId, NotAllowedChannelError, NotNecessaryRole, ParseDiceLineError, NameInUseError, CustomEmojiError, ParameterErrorWithPossibleParameter
from antipetros_discordbot.utility.gidtools_functions import loadjson
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.bot_support.sub_support.sub_support_helper.cooldown_dict import CoolDownDict
from antipetros_discordbot.utility.enums import UpdateTypus
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
    from antipetros_discordbot.bot_support.bot_supporter import BotSupporter
# endregion[Imports]

# region [TODO]

# TODO: rebuild whole error handling system
# TODO: make it so that creating the embed also sends it, with more optional args

# TODO: Handlers needed: discord.ext.commands.errors.DisabledCommand,ParameterError,discord.ext.MissingRequiredArgument

# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
EMBED_SYMBOLS = loadjson(APPDATA["embed_symbols.json"])
# endregion[Constants]


class ErrorHandler(SubSupportBase):
    char_to_replace = "'"
    config_name = 'error_handling'
    error_thumbnail = "https://static01.nyt.com/images/2018/05/15/arts/01hal-voice1/merlin_135847308_098289a6-90ee-461b-88e2-20920469f96a-superJumbo.jpg?quality=90&auto=webp"

    def __init__(self, bot: "AntiPetrosBot", support: "BotSupporter"):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.emphasis_regex = re.compile(r"'.*?'")
        self.error_handle_table = {commands.MaxConcurrencyReached: self._handle_max_concurrency,
                                   commands.CommandOnCooldown: self._handle_command_on_cooldown,
                                   commands.errors.BadArgument: self._handle_bad_argument,
                                   MissingAttachmentError: self._handle_missing_attachment,
                                   commands.CheckFailure: self._handle_check_failure,
                                   IsNotTextChannelError: self._handle_not_text_channel,
                                   NotNecessaryDmId: self._handle_not_necessary_dm_id,
                                   NotAllowedChannelError: self._handle_not_allowed_channel,
                                   NotNecessaryRole: self._handle_not_necessary_role,
                                   commands.errors.CommandNotFound: self._handle_command_not_found,
                                   ParseDiceLineError: self._handle_dice_line_error,
                                   NameInUseError: self._handle_name_in_use_error,
                                   CustomEmojiError: self._handle_custom_emoji_error,
                                   commands.errors.BadUnionArgument: self._handle_bad_union_argument,
                                   commands.errors.MissingRequiredArgument: self._handle_missing_required_argument}

        self.cooldown_data = CoolDownDict()

        glog.class_init_notification(log, self)

    @property
    def delete_invoking_messages(self):
        return BASE_CONFIG.retrieve(self.config_name, 'delete_invoking_messages', typus=bool, direct_fallback=False)

    @property
    def delete_reply_after(self):
        _out = BASE_CONFIG.retrieve(self.config_name, 'delete_reply_after', typus=int, direct_fallback=120)
        if _out == 0 or _out <= 0:
            return None
        return _out

    @property
    def emphasis_chars(self):
        format_lut = {'bold': '**',
                      'underlined': '__',
                      'italic': '*',
                      'strikethrough': '~'}
        format_keywords = BASE_CONFIG.retrieve(self.config_name, 'msg_keyword_format', typus=Tuple[str], direct_fallback=[], mod_func=lambda x: x.casefold())
        return (''.join(map(lambda x: format_lut.get(x, ''), format_keywords)), ''.join(map(lambda x: format_lut.get(x, ''), reversed(format_keywords))))

    async def transform_error_msg(self, error_msg):
        before_emphasis, after_emphasis = self.emphasis_chars
        _msg = error_msg
        for orig_word in self.emphasis_regex.findall(error_msg):
            cleaned_word = orig_word.strip("'").strip()
            mod_word = f"{before_emphasis}{cleaned_word.upper()}{after_emphasis}"
            _msg = _msg.replace(orig_word, mod_word)
        return _msg

    async def handle_base_errors(self, event_method, *args, **kwargs):
        kwarg_string = ', '.join(f"{key}: {str(value)}" for key, value in kwargs.items())
        arg_string = ', '.join(str(arg) for arg in args)
        log.error(f"{event_method} - '{arg_string}' - '{kwarg_string}'", exc_info=True)

    async def execute_on_command_errors(self, ctx, error: Exception):

        error_traceback = ''.join(traceback.format_tb(error.__traceback__)) + f"\n\n{'+'*50}\n{error.__cause__}\n{'+'*50}"

        if hasattr(error, 'original'):
            error_traceback = ''.join(traceback.format_tb(error.original.__traceback__)) + f"\n\n{'+'*50}\n{error.__cause__}\n{'+'*50}"

        if hasattr(error, 'error_handler_name') and hasattr(self, error.error_handler_name):
            handle_meth = getattr(self, error.error_handler_name)
        else:
            handle_meth = self.error_handle_table.get(type(error), self._default_handle_error)

        log_error = await handle_meth(ctx, error, error_traceback)
        if ctx.channel.type is ChannelType.text and ctx.command is not None and log_error is not False:
            log.error("Error '%s' was caused by '%s' on the content '%s' with args '%s' and traceback --> %s", error.__class__.__name__, ctx.author.name, ctx.message.content, ctx.args, error_traceback)
            if self.delete_invoking_messages is True:
                await ctx.message.delete()

    async def _default_handle_error(self, ctx: commands.Context, error, error_traceback):
        log.error('Ignoring exception in command {}:'.format(ctx.command))
        log.exception(error, exc_info=True, stack_info=False)
        delete_after = None
        creator_mention = self.bot.creator.display_name
        if ctx.channel.type is ChannelType.text:
            delete_after = 120
            creator_mention = self.bot.creator.mention
        try:
            fields = [self.bot.field_item(name='Error', value=f"`{error.original.__class__.__name__}`", inline=False)]
        except AttributeError:
            fields = [self.bot.field_item(name='Error', value=f"`{error.__class__.__name__}`", inline=False)]
        embed_data = await self.bot.make_generic_embed(title='Giddi Fucked up',
                                                       description=f"**• There is an bug in the code\nor\n• {creator_mention} forgot to set an Error handler!**\n{ZERO_WIDTH}\n> {creator_mention} will be automatically notified so he can fix it, but please message him with the circumstances of this error if you can.",
                                                       image="https://media.giphy.com/media/KsUKNNUEeryJa/giphy.gif",
                                                       fields=fields,
                                                       thumbnail="https://i.postimg.cc/J0zSHgRH/sorry-thumbnail.png",
                                                       color='red')
        await ctx.send(**embed_data, delete_after=delete_after, allowed_mentions=discord.AllowedMentions.none())
        await self.bot.message_creator(embed=await self.error_reply_embed(ctx, error, 'Error With No Special Handling Occured', msg=str(error)), file=await self._make_traceback_file(error_traceback))

    async def _handle_ask_canceled_error(self, ctx, error, error_traceback):
        await error.ask_object.channel.send(error.msg, delete_after=90)
        return False

    async def _handle_ask_timeout_error(self, ctx, error, error_traceback):
        await error.ask_object.channel.send(error.msg, delete_after=90)
        return False

    async def _handle_parameter_error_with_possible_parameter(self, ctx, error, error_traceback):
        embed_data = await error.to_embed(ctx=ctx, bot=self.bot)
        await ctx.send(**embed_data)
        help_command = self.bot.get_command('help')
        await help_command(ctx, in_object=ctx.command)

    async def _handle_name_in_use_error(self, ctx, error, error_traceback):
        await ctx.send(embed=await self.bot.make_error_embed(ctx, error), delete_after=60)

    async def _handle_custom_emoji_error(self, ctx, error, error_traceback):
        await ctx.send(embed=await self.bot.make_error_embed(ctx, error), delete_after=60)

    async def _handle_missing_required_argument(self, ctx: commands.Context, error, error_traceback):
        await ctx.send(error, delete_after=60)
        command = ctx.command
        await ctx.send("Usage:\n" + str(CodeBlock(command.usage, 'css')), delete_after=60)
        await ctx.send("Example:\n" + str(CodeBlock(command.example, 'css')), delete_after=60)

    async def _handle_command_not_found(self, ctx, error, error_traceback):
        wrong_command_name = ctx.invoked_with
        corrected_command_name, corrected_command_aliases = await self.fuzzy_match_command_name(wrong_command_name)
        await ctx.reply(f"The command `{wrong_command_name}` does not exist!\n\nDid you mean `{corrected_command_name}` with aliases `{', '.join(corrected_command_aliases)}` ?", delete_after=120)

    async def _handle_not_necessary_role(self, ctx, error, error_traceback):
        embed_data = await self.bot.make_generic_embed(footer='default_footer', title='Missing Role', thumbnail=self.error_thumbnail, description=await self.transform_error_msg(error.msg), field=[self.bot.field_item(name='Your Roles:', value='\n'.join(role.name for role in ctx.author.roles))])
        await ctx.reply(delete_after=self.delete_reply_after, **embed_data)

    async def _handle_bad_union_argument(self, ctx, error, error_traceback):
        embed_data = await self.bot.make_generic_embed(footer='default_footer', title='Bad Input', thumbnail=self.error_thumbnail, description='Bad input for the command')
        await ctx.reply(delete_after=self.delete_reply_after, **embed_data)

    async def _handle_not_allowed_channel(self, ctx, error, error_traceback):
        embed_data = await self.bot.make_generic_embed(footer='default_footer', title='Wrong Channel', thumbnail=self.error_thumbnail, description=await self.transform_error_msg(error.msg), image='bertha')
        await ctx.reply(delete_after=self.delete_reply_after, **embed_data)

    async def _handle_not_necessary_dm_id(self, ctx, error, error_traceback):
        embed_data = await self.bot.make_generic_embed(footer='default_footer', title='Missing Permission', thumbnail=self.error_thumbnail, description=await self.transform_error_msg(error.msg))
        await ctx.reply(**embed_data)

    async def _handle_not_text_channel(self, ctx, error, error_traceback):
        embed_data = await self.bot.make_generic_embed(footer='default_footer', title='Only allowed in Text Channels', thumbnail=self.error_thumbnail, description=await self.transform_error_msg(error.msg))
        await ctx.reply(**embed_data)

    async def _handle_check_failure(self, ctx, error, error_traceback):
        if self.bot.is_blacklisted(ctx.author) is False:
            await ctx.channel.send(delete_after=self.delete_reply_after, embed=await self.error_reply_embed(ctx,
                                                                                                            error,
                                                                                                            'Missing Permission',
                                                                                                            f'{ctx.author.mention}\n{ZERO_WIDTH}\n **You dont_have Permission to call this Command**\n{ZERO_WIDTH}'))

    async def _handle_missing_attachment(self, ctx, error, error_traceback):
        await ctx.channel.send(delete_after=self.delete_reply_after, embed=await self.error_reply_embed(ctx,
                                                                                                        error,
                                                                                                        'Missing Attachments',
                                                                                                        f'{ctx.author.mention}\n{ZERO_WIDTH}\n **{str(error)}**\n{ZERO_WIDTH}'))

    async def _handle_bad_argument(self, ctx, error, error_traceback):
        await ctx.channel.send(delete_after=self.delete_reply_after, embed=await self.error_reply_embed(ctx,
                                                                                                        error,
                                                                                                        'Wrong Argument',
                                                                                                        f'{ctx.author.mention}\n{ZERO_WIDTH}\n **You tried to invoke `{ctx.command.name}` with an wrong argument**\n{ZERO_WIDTH}\n```shell\n{ctx.command.name} {ctx.command.signature}\n```',
                                                                                                        error_traceback=None))

    async def _handle_dice_line_error(self, ctx, error, error_traceback):
        embed = await self.error_reply_embed(ctx,
                                             error,
                                             title='unable to parse input',
                                             msg='Please only use the format `1d6`')

        embed.add_field(name="Amount", value='`1` number is the amount of dice to roll')
        embed.add_field(name="Type of dice", value="`dx` is type of dice")
        embed.add_field(name="Just like in every Tabletop or RPG", value=ZERO_WIDTH, inline=False)
        await ctx.channel.send(delete_after=self.delete_reply_after, embed=embed)

    async def _handle_max_concurrency(self, ctx, error, error_traceback):

        await ctx.channel.send(embed=await self.error_reply_embed(ctx, error, 'STOP SPAMMING!', f'{ctx.author.mention}\n{ZERO_WIDTH}\n **There can ever only be one instance of this command running, please wait till it has finished**', error_traceback=error_traceback), delete_after=self.delete_reply_after)
        await ctx.message.delete()

    async def _handle_command_on_cooldown(self, ctx, error, error_traceback):
        # TODO: get normal sentence from BucketType, with dynamical stuff (user_name, channel_name,...)
        again_time = await async_seconds_to_pretty_normal(int(round(error.retry_after, 0)))
        msg = await self.transform_error_msg(f"Command '{ctx.command.name}' is on cooldown for '{error.cooldown.type.name.upper()}'. \n{ZERO_WIDTH}\nYou can try again in '{again_time}'\n{ZERO_WIDTH}")
        if self.cooldown_data.in_data(ctx, error) is True:
            try:
                await ctx.message.delete()
            except discord.errors.Forbidden:
                pass
            await ctx.author.send(msg)
            return
        await self.cooldown_data.add(ctx, error)
        embed_data = await self.bot.make_generic_embed(title=f'Command is on Cooldown for the scope of {error.cooldown.type.name.upper()}',
                                                       thumbnail="cooldown",
                                                       description=msg)
        await ctx.reply(**embed_data, delete_after=error.retry_after)
        try:
            await ctx.message.delete()
        except discord.errors.Forbidden:
            pass

    async def _make_traceback_file(self, error_traceback: str):
        bytes_traceback = await asyncio.to_thread(error_traceback.encode, encoding='utf-8', errors='ignore')
        with BytesIO() as bytefile:
            await asyncio.to_thread(bytefile.write, bytes_traceback)
            await asyncio.to_thread(bytefile.seek, 0)
            return discord.File(bytefile, "error_file.txt")

    async def error_reply_embed(self, ctx, error, title, msg, error_traceback=None):
        embed = Embed(title=title, description=f"{ZERO_WIDTH}\n{msg}\n{ZERO_WIDTH}", color=discord.Colour.red(), timestamp=datetime.utcnow())
        embed.set_thumbnail(url=EMBED_SYMBOLS.get('warning'))
        embed.add_field(name="🔗", value=embed_hyperlink("invoking message jump url", ctx.message.jump_url), inline=False)
        embed.add_field(name="prefix used", value=f"`{ctx.prefix}`", inline=False)
        embed.add_field(name='invoking message', value=f"```css\n{ctx.message.content}\n```", inline=False)
        embed.add_field(name="args", value=ctx.args, inline=False)
        embed.add_field(name="kwargs", value=ctx.kwargs, inline=False)

        if ctx.command is not None:
            err_name = await async_split_camel_case_string(error.__class__.__name__)
            embed.set_footer(text=f"Command: `{ctx.command.name}`\n{ZERO_WIDTH}\n By User: `{ctx.author.name}`\n{ZERO_WIDTH}\n Error: `{err_name}`\n{ZERO_WIDTH}\n{ZERO_WIDTH}")
            embed.add_field(name='command used', value=ctx.command.name, inline=False)

        else:
            err_name = await async_split_camel_case_string(error.__class__.__name__)
            embed.set_footer(text=f"text: {ctx.message.content}\n{ZERO_WIDTH}\n By User: `{ctx.author.name}`\n{ZERO_WIDTH}\n Error: `{err_name}`\n{ZERO_WIDTH}\n{ZERO_WIDTH}")
        embed.add_field(name='invoking user', value=ctx.author.name, inline=False)
        error_type = error.__class__.__name__ if not hasattr(error, 'original') else error.original.__class__.__name__
        embed.add_field(name='error type', value=error_type, inline=False)

        return embed

    async def error_message_embed(self, ctx, error, msg=ZERO_WIDTH):
        embed = Embed(title='ERROR', color=self.support.color('orange').int, timestamp=datetime.utcnow(), description=ZERO_WIDTH + '\n' + msg + '\n' + ZERO_WIDTH)
        embed.set_thumbnail(url=EMBED_SYMBOLS.get('warning'))
        try:
            embed.add_field(name=await async_split_camel_case_string(error.__class__.__name__), value=f"error occured with command: {ctx.command.name} and arguments: {str(ctx.args)}")
        except AttributeError:
            embed.add_field(name=await async_split_camel_case_string(error.__class__.__name__), value="command not found\n" + ZERO_WIDTH + '\n', inline=False)
            corrections = fuzzprocess.extract(ctx.message.content.split(' ')[1], [command.name for command in self.bot.commands], scorer=fuzz.token_set_ratio, limit=3)
            if corrections is not None:
                embed.add_field(name='did you mean:', value=ZERO_WIDTH + '\n' + f'\n{ZERO_WIDTH}\n'.join(correction[0] for correction in corrections), inline=False)
            embed.set_footer(text=f'to get a list of all commands use:\n@AntiPetros {self.bot.help_invocation}\n{ZERO_WIDTH}\n{ZERO_WIDTH}')

        return embed

    async def commands_and_alias_mapping(self):
        _out = {}
        for command in self.bot.commands:
            _out[command.name] = list(command.aliases)
        return _out

    async def fuzzy_match_command_name(self, wrong_name):
        best = (None, 0)
        command_and_aliases = await self.commands_and_alias_mapping()
        for command_name, aliases in command_and_aliases.items():
            fuzz_match = fuzzprocess.extractOne(wrong_name, [command_name] + aliases, processor=lambda x: x.casefold())
            if fuzz_match[1] > best[1]:
                best = (command_name, fuzz_match[1])
        return best[0], command_and_aliases.get(best[0])

    async def on_ready_setup(self):
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self):
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return ErrorHandler
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
