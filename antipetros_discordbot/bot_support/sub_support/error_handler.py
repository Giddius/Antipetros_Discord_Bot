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

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import async_seconds_to_pretty_normal, async_split_camel_case_string
from antipetros_discordbot.utility.exceptions import MissingAttachmentError, NotNecessaryRole, IsNotTextChannelError, NotNecessaryDmId, NotAllowedChannelError, NotNecessaryRole, ParseDiceLineError, NameInUseError, CustomEmojiError
from antipetros_discordbot.utility.gidtools_functions import loadjson
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.bot_support.sub_support.sub_support_helper.cooldown_dict import CoolDownDict
from antipetros_discordbot.utility.enums import UpdateTypus
# endregion[Imports]

# region [TODO]

# TODO: rebuild whole error handling system
# TODO: make it so that creating the embed also sends it, with more optional args

# TODO: Handlers needed: discord.ext.commands.errors.DisabledCommand,

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
    error_thumbnail = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Dialog-error-round.svg/1200px-Dialog-error-round.svg.png"

    def __init__(self, bot, support):
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
                                   CustomEmojiError: self._handle_custom_emoji_error
                                   }
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
        log.error(f"{event_method} - '{arg_string}' - '{kwarg_string}'")

    async def handle_errors(self, ctx, error):
        error_traceback = '\n'.join(traceback.format_exception(error, value=error, tb=None))

        log.error(error)

        await self.error_handle_table.get(type(error), self._default_handle_error)(ctx, error, error_traceback)
        if ctx.channel.type is ChannelType.text and ctx.command is not None:
            log.error("Error '%s' was caused by '%s' on the content '%s' with args '%s' and traceback --> %s", error.__class__.__name__, ctx.author.name, ctx.message.content, ctx.args, error_traceback)
            if self.delete_invoking_messages is True:
                await ctx.message.delete()

    async def _default_handle_error(self, ctx: commands.Context, error, error_traceback):
        log.error('Ignoring exception in command {}:'.format(ctx.command))
        log.exception(error, exc_info=True, stack_info=False)
        if ctx.channel.type is ChannelType.text:
            await ctx.reply(f'The command had an unspecified __**ERROR**__\n please send {self.bot.creator.member_object.mention} a DM of what exactly you did when the error occured.', delete_after=120, allowed_mentions=discord.AllowedMentions.none())
            await self.bot.message_creator(embed=await self.error_reply_embed(ctx, error, 'Error With No Special Handling Occured', msg=str(error), error_traceback=error_traceback))

    async def _handle_name_in_use_error(self, ctx, error, error_traceback):
        await ctx.send(embed=await self.bot.make_error_embed(ctx, error), delete_after=60)

    async def _handle_custom_emoji_error(self, ctx, error, error_traceback):
        await ctx.send(embed=await self.bot.make_error_embed(ctx, error), delete_after=60)

    async def _handle_command_not_found(self, ctx, error, error_traceback):
        wrong_command_name = ctx.invoked_with
        corrected_command_name, corrected_command_aliases = await self.fuzzy_match_command_name(wrong_command_name)
        await ctx.reply(f"The command `{wrong_command_name}` does not exist!\n\nDid you mean `{corrected_command_name}` with aliases `{', '.join(corrected_command_aliases)}` ?", delete_after=120)

    async def _handle_not_necessary_role(self, ctx, error, error_traceback):
        embed_data = await self.bot.make_generic_embed(footer='default_footer', title='Missing Role', thumbnail=self.error_thumbnail, description=await self.transform_error_msg(error.msg), field=[self.bot.field_item(name='Your Roles:', value='\n'.join(role.name for role in ctx.author.roles))])
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
        msg = await self.transform_error_msg(f"Command '{ctx.command.name}' is on cooldown for '{error.cooldown.type.name.upper()}'. \n{ZERO_WIDTH}\nYou can try again in '{await async_seconds_to_pretty_normal(int(round(error.retry_after, 0)))}'\n{ZERO_WIDTH}")
        if self.cooldown_data.in_data(ctx, error) is True:
            await ctx.message.delete()
            await ctx.author.send(msg)
            return
        await self.cooldown_data.add(ctx, error)
        embed_data = await self.bot.make_generic_embed(title=f'Command is on Cooldown for the scope of {error.cooldown.type.name.upper()}',
                                                       thumbnail="cooldown",
                                                       description=msg)
        await ctx.reply(**embed_data, delete_after=error.retry_after)
        await ctx.message.delete()

    async def error_reply_embed(self, ctx, error, title, msg, error_traceback=None):
        embed = Embed(title=title, description=f"{ZERO_WIDTH}\n{msg}\n{ZERO_WIDTH}", color=self.support.color('red').int, timestamp=datetime.utcnow())
        embed.set_thumbnail(url=EMBED_SYMBOLS.get('warning'))
        # embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        if error_traceback is not None:
            embed.add_field(name='Traceback', value=str(error_traceback)[0:500])
        if ctx.command is not None:
            embed.set_footer(text=f"Command: `{ctx.command.name}`\n{ZERO_WIDTH}\n By User: `{ctx.author.name}`\n{ZERO_WIDTH}\n Error: `{await async_split_camel_case_string(error.__class__.__name__)}`\n{ZERO_WIDTH}\n{ZERO_WIDTH}")
        else:
            embed.set_footer(text=f"text: {ctx.message.content}\n{ZERO_WIDTH}\n By User: `{ctx.author.name}`\n{ZERO_WIDTH}\n Error: `{await async_split_camel_case_string(error.__class__.__name__)}`\n{ZERO_WIDTH}\n{ZERO_WIDTH}")

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

    async def if_ready(self):
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
