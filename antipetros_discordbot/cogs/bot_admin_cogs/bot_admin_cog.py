

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from datetime import datetime, timedelta
from textwrap import dedent
import random
import asyncio
import re
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import commands, tasks
import gc
from icecream import ic
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from typing import TYPE_CHECKING, List, Dict, Optional, Tuple, Any, Union, Callable, Iterable, Set, Mapping
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import make_config_name, seconds_to_pretty, delete_message_if_text_channel
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, log_invoker, owner_or_admin, only_giddi
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.gidtools_functions import pathmaker, writejson, loadjson
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import make_message_list
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.converters import CogConverter
from antipetros_discordbot.utility.general_decorator import async_log_profiler, sync_log_profiler, universal_log_profiler

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
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class BotAdminCog(AntiPetrosBaseCog, command_attrs={'hidden': True}):
    """
     General Commands and methods that are needed to Administrate the Bot itself.
    """

    public = False
    meta_status = CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    long_description = "Almost all commands are either locked to Admins and Admin Leads or just Admin Leads. The Creator Giddi has an overwrite and can invoke all commands."
    extra_info = "!WARNING! all command invocations are logged.\nSpecific Data that is logged:" + '\n'.join(["date and time", "command name", "prefix used", "user name", "user id", "channel name", "invoking message content"])
    required_config_data = {'base_config': {'general_settings': {"cogs_location": "antipetros_discordbot.cogs"}},
                            'cogs_config': {}}

    alive_phrases_file = pathmaker(APPDATA['fixed_data'], 'alive_phrases.json')
    who_is_trigger_phrases_file = pathmaker(APPDATA['fixed_data'], 'who_is_trigger_phrases.json')
    loop_regex = re.compile(r"\<?(?P<name>[a-zA-Z\.\_]+)\srunning\=(?P<running>True|False)\sclosed\=(?P<closed>True|False)\sdebug\=(?P<debug>True|False)\>", re.IGNORECASE)
    cog_import_base_path = BASE_CONFIG.retrieve('general_settings', 'cogs_location', typus=str, direct_fallback="antipetros_discordbot.cogs")

    required_folder = [RequiredFolder(APPDATA["fixed_data"])]
    required_files = [RequiredFile(alive_phrases_file, [], RequiredFile.FileType.JSON), RequiredFile(who_is_trigger_phrases_file, [], RequiredFile.FileType.JSON)]

    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.latest_who_is_triggered_time = datetime.utcnow()
        self.reaction_remove_ids = []
        self.ready = False
        self.listeners_enabled = {'stop_the_reaction_petros_listener': False,
                                  'who_is_this_bot_listener': False}
        glog.class_init_notification(log, self)

# region [Setup]
    @universal_log_profiler
    async def on_ready_setup(self):
        # self.garbage_clean_loop.start()
        reaction_remove_ids = [self.bot.id] + [_id for _id in self.bot.owner_ids]
        self.reaction_remove_ids = set(reaction_remove_ids)
        await self._update_listener_enabled()
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        if UpdateTypus.CONFIG in typus:
            await self._update_listener_enabled()
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]


# region [Loops]

    @tasks.loop(hours=1)
    @universal_log_profiler
    async def garbage_clean_loop(self):
        await self.bot.wait_until_ready()
        log.info('running garbage clean')
        x = gc.collect()
        log.info('Garbage Clean collected "%s"', x)

# endregion[Loops]

    @property
    @universal_log_profiler
    def alive_phrases(self):
        if os.path.isfile(self.alive_phrases_file) is False:
            writejson(['I am alive!'], self.alive_phrases_file)
        return loadjson(self.alive_phrases_file)

    @property
    @universal_log_profiler
    def who_is_trigger_phrases(self):
        std_phrases = ['who is %BOT_NAME%',
                       'what is %BOT_NAME%',
                       'who the fuck is %BOT_NAME%']
        if os.path.isfile(self.who_is_trigger_phrases_file) is False:
            writejson(std_phrases, self.who_is_trigger_phrases_file)
        return loadjson(self.who_is_trigger_phrases_file)

# region [Listener]
    @commands.Cog.listener(name='on_reaction_add')
    @universal_log_profiler
    async def stop_the_reaction_petros_listener(self, reaction: discord.Reaction, user):
        if self.ready is False:
            return
        if self.listeners_enabled.get("stop_the_reaction_petros_listener", False) is False:
            return
        message = reaction.message
        author = message.author
        if user.id == 155149108183695360 and author.id in self.reaction_remove_ids:
            await reaction.remove(user)

    @commands.Cog.listener(name='on_message')
    @universal_log_profiler
    async def who_is_this_bot_listener(self, msg: discord.Message):
        if self.ready is False:
            return
        if self.listeners_enabled.get("who_is_this_bot_listener", False) is False:
            return

        channel = msg.channel
        if channel.type is not discord.ChannelType.text:
            return False

        if channel.name.casefold() not in self.allowed_channels("who_is_this_bot_listener"):
            return False
        if any(trigger_phrase.replace('%BOT_NAME%', self.bot.display_name).casefold() in msg.content.casefold() for trigger_phrase in self.who_is_trigger_phrases):
            log.debug('who_is_this_bot_listener triggered')
            if datetime.utcnow() > self.latest_who_is_triggered_time + timedelta(minutes=1):
                image = self.bot.portrait_url
                embed_data = await self.bot.make_generic_embed(title=f'WHO IS {self.bot.display_name.upper()}', description='I am an custom made Bot for this community!',
                                                               fields=[self.bot.field_item(name='What I can do', value=f'Get a description of my features by using `@{self.bot.display_name} help`', inline=False),
                                                                       self.bot.field_item(name='Who created me', value=f'I was created by {self.bot.creator.member_object.mention}, for the Antistasi Community')],
                                                               image=image,
                                                               thumbnail=None)
                await msg.reply(**embed_data, delete_after=60)
                log.info("'%s' was triggered by '%s' in '%s'", "who_is_this_bot_listener", msg.author.name, msg.channel.name)
                self.latest_who_is_triggered_time = datetime.utcnow()
# endregion[Listener]

    @auto_meta_info_command(aliases=['reload', 'refresh'])
    @commands.is_owner()
    async def reload_all_ext(self, ctx):
        BASE_CONFIG.read()
        COGS_CONFIG.read()
        reloaded_extensions = []
        do_not_reload_cogs = BASE_CONFIG.retrieve('extension_loading', 'do_not_reload_cogs', typus=List[str], direct_fallback=[])
        async with ctx.typing():
            for _extension in BASE_CONFIG.options('extensions'):
                if _extension not in do_not_reload_cogs and BASE_CONFIG.retrieve('extensions', _extension, typus=bool, direct_fallback=False) is True:
                    _location = self.cog_import_base_path + '.' + _extension
                    try:
                        self.bot.unload_extension(_location)

                        self.bot.load_extension(_location)
                        log.debug('Extension Cog "%s" was successfully reloaded from "%s"', _extension.split('.')[-1], _location)
                        _category, _extension = _extension.split('.')
                        for cog_name, cog_object in self.bot.cogs.items():
                            if cog_name.casefold() == _extension.split('.')[-1].replace('_', '').casefold():
                                await cog_object.on_ready_setup()
                                break

                        reloaded_extensions.append(self.bot.field_item(name=_extension, value=f"{ZERO_WIDTH}\n:white_check_mark:\n{ZERO_WIDTH}", inline=False))
                    except commands.DiscordException as error:
                        log.error(error)
            # await self.bot.to_all_cogs('on_ready_setup')
            _delete_time = 15 if self.bot.is_debug is True else 60
            _embed_data = await self.bot.make_generic_embed(title="**successfully reloaded the following extensions**", author='bot_author', thumbnail="update", fields=reloaded_extensions)
            await ctx.send(**_embed_data, delete_after=_delete_time)
            await ctx.message.delete(delay=float(_delete_time))

    @auto_meta_info_command(aliases=['die', 'rip', 'go-away', 'go_away', 'go.away', 'goaway', 'get_banned'])
    @owner_or_admin()
    async def shutdown(self, ctx, *, reason: str = 'No reason given'):
        log.critical('shutdown command received from "%s" with reason: "%s"', ctx.author.name, reason)
        await ctx.message.delete()
        await self.bot.shutdown_mechanic()

    @auto_meta_info_command()
    @owner_or_admin()
    async def tell_version(self, ctx: commands.Context):
        embed_data = await self.bot.make_generic_embed(title=self.bot.display_name.title(), description='**Version**  ' + str(os.getenv('ANTIPETROS_VERSION')),
                                                       thumbnail=self.bot.portrait_url)
        await ctx.send(**embed_data)

    @auto_meta_info_command()
    @owner_or_admin()
    @log_invoker(log, "warning")
    async def add_who_is_phrase(self, ctx, *, phrase: str):
        current_phrases = self.who_is_trigger_phrases

        if phrase.casefold() in map(lambda x: x.casefold(), current_phrases):
            await ctx.send(f'phrase `{phrase}` already in `who_is_trigger_phrases`')
            return
        current_phrases.append(phrase)
        writejson(current_phrases, self.who_is_trigger_phrases_file)
        await ctx.send(f"Added phrase `{phrase}` to `who_is_trigger_phrases`")

    @ auto_meta_info_command(aliases=['you_dead?', 'are-you-there', 'poke-with-stick'])
    async def life_check(self, ctx: commands.Context):
        if random.randint(0, len(self.alive_phrases)) == 0:
            file = discord.File(APPDATA['bertha.png'])
            await ctx.reply('My assistent will record your command for me, please speak into her Banhammer', file=file)
            return
        await ctx.reply(random.choice(self.alive_phrases))

    @ auto_meta_info_command()
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def add_to_blacklist(self, ctx, user: discord.Member):

        if user.bot is True:
            # TODO: make as embed
            await ctx.send("the user you are trying to add is a **__BOT__**!\n\nThis can't be done!")
            return
        blacklisted_user = await self.bot.blacklist_user(user)
        if blacklisted_user is not None:
            await ctx.send(f"User '{user.name}' with the id '{user.id}' was added to my blacklist, he wont be able to invoke my commands!")
        else:
            await ctx.send("Something went wrong while blacklisting the User")

    @ auto_meta_info_command()
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def remove_from_blacklist(self, ctx, user: discord.Member):

        await self.bot.unblacklist_user(user)
        await ctx.send(f"I have unblacklisted user {user.name}")

    @ auto_meta_info_command()
    async def tell_uptime(self, ctx):

        now_time = datetime.utcnow()
        delta_time = now_time - self.bot.start_time
        seconds = round(delta_time.total_seconds())
        # TODO: make as embed
        await ctx.send(f"__Uptime__ -->\n| {str(seconds_to_pretty(seconds))}")

    @auto_meta_info_command()
    @commands.is_owner()
    async def send_log_file(self, ctx: commands.Context, which_logs: str = 'newest'):
        """
        Gets the log files of the bot and post it as a file to discord.

        You can choose to only get the newest or all logs.

        Args:
            which_logs (str, optional): [description]. Defaults to 'newest'. other options = 'all'

        Example:
            @AntiPetros send_log_file all
        """
        log_folder = APPDATA.log_folder
        if which_logs == 'newest':

            for file in os.scandir(log_folder):
                if file.is_file() and file.name.endswith('.log'):
                    discord_file = discord.File(file.path)
                    await ctx.send(file=discord_file)

        elif which_logs == 'all':
            for file in os.scandir(log_folder):
                if file.is_file() and file.name.endswith('.log'):
                    discord_file = discord.File(file.path)
                    await ctx.send(file=discord_file)

            for old_file in os.scandir(pathmaker(log_folder, 'old_logs')):
                if old_file.is_file() and old_file.name.endswith('.log'):
                    discord_file = discord.File(old_file.path)
                    await ctx.send(file=discord_file)
        log.warning("%s log file%s was requested by '%s'", which_logs, 's' if which_logs == 'all' else '', ctx.author.name)

    @auto_meta_info_command()
    @commands.is_owner()
    async def invocation_prefixes(self, ctx: commands.Context):
        prefixes = self.bot.command_prefix(self.bot, ctx.message)
        prefixes = sorted(prefixes, key=lambda x: '@' in x, reverse=True)
        mod_prefixes = []
        for prefix in prefixes:
            if not prefix.startswith('<@'):
                prefix = f'{prefix}'
            if '@' in prefix and prefix.replace('!', '') in [prfx.replace('!', '') for prfx in mod_prefixes]:
                pass
            else:
                mod_prefixes.append(prefix)
        embed_data = await self.bot.make_generic_embed(title='Invocation Prefixes', description=make_message_list(mod_prefixes),
                                                       thumbnail=None,
                                                       timestamp=None,
                                                       author='bot_author')
        cmsg = await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        await asyncio.sleep(60)
        await cmsg.delete()
        await ctx.message.delete()

    @auto_meta_info_command()
    @commands.is_owner()
    async def all_aliases(self, ctx: commands.Context):
        all_aliases = []
        for command in self.bot.walk_commands():
            if command.aliases:
                all_aliases.append(f"`{command.name}`\n```python\n" + '\n'.join(command.aliases) + "\n```")

        await self.bot.split_to_messages(ctx, '\n\n'.join(all_aliases), split_on='\n\n')

    @auto_meta_info_command()
    @only_giddi()
    async def send_loop_info(self, ctx: commands.Context, loop_attr: str = None):
        loop_attr = 'name' if loop_attr is None else loop_attr
        if loop_attr.casefold() not in self.loop_regex.groupindex.keys():
            await ctx.send(f"`{loop_attr}` is not a valid value for the parameter `loop_attr`.\nNeeds to be one of " + ', '.join(f"`{g_name}`" for g_name in self.loop_regex.groupindex.keys()), delete_after=120)
            await delete_message_if_text_channel(ctx)
            return
        loop = asyncio.get_event_loop()
        loop_string = str(loop)  # "<uvloop.Loop running=True closed=False debug=False>"
        loop_match = self.loop_regex.match(loop_string)
        await ctx.send(loop_match.group(loop_attr.casefold()))

    @auto_meta_info_command()
    @owner_or_admin()
    async def disable_cog(self, ctx: commands.Context, cog: CogConverter):
        name = cog.qualified_name
        await ctx.send(f"Trying to disable Cog `{name}`")
        self.bot.remove_cog(name)
        import_path = cog.__module__.split('.', 2)[-1]
        if import_path.split('.')[0] not in ['bot_admin_cogs', 'discord_admin_cogs', 'dev_cogs']:
            BASE_CONFIG.set("extensions", import_path, "no")
            BASE_CONFIG.save()
            await ctx.send(f"Set BASE_CONFIG import setting for Cog `{name}` to `no`")
        await ctx.send(f"removed Cog `{name}` from the the current bot process!")

    @auto_meta_info_command()
    @owner_or_admin()
    async def current_cogs(self, ctx: commands.Context):
        text = ""
        for cog_name, cog_object in self.bot.cogs.items():
            text += f"NAME: {cog_name}, CONFIG_NAME: {cog_object.config_name}\n{'-'*10}\n"
        await self.bot.split_to_messages(ctx, text, in_codeblock=True, syntax_highlighting='fix')

# region [Helper]
    @universal_log_profiler
    async def _update_listener_enabled(self):
        for listener_name in self.listeners_enabled:
            self.listeners_enabled[listener_name] = COGS_CONFIG.retrieve(self.config_name, listener_name + '_enabled', typus=bool, direct_fallback=False)


# endregion[Helper]

    def cog_check(self, ctx):
        return True

    async def cog_command_error(self, ctx, error):
        pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    def __repr__(self):
        return f"{self.qualified_name}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):
        # self.garbage_clean_loop.stop()
        log.debug("Cog '%s' UNLOADED!", str(self))

# region[Main_Exec]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(BotAdminCog(bot)))

# endregion[Main_Exec]
