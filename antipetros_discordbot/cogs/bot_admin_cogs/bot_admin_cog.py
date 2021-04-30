

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from datetime import datetime
import random
import asyncio
import re
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import commands, tasks
import gc
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from typing import List, TYPE_CHECKING
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import delete_message_if_text_channel
from antipetros_discordbot.utility.checks import log_invoker, only_giddi, owner_or_admin
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, RequiredFolder, auto_meta_info_command
from antipetros_discordbot.utility.gidtools_functions import pathmaker, writejson, loadjson
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.converters import CogConverter
from antipetros_discordbot.utility.general_decorator import universal_log_profiler

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


class BotAdminCog(AntiPetrosBaseCog, command_attrs={'hidden': True, 'categories': CommandCategory.META}):
    """
     General Commands and methods that are needed to Administrate the Bot itself.
    """
# region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    required_config_data = {'base_config': {'general_settings': {"cogs_location": "antipetros_discordbot.cogs"}},
                            'cogs_config': {}}

    alive_phrases_file = pathmaker(APPDATA['fixed_data'], 'alive_phrases.json')
    who_is_trigger_phrases_file = pathmaker(APPDATA['fixed_data'], 'who_is_trigger_phrases.json')
    loop_regex = re.compile(r"\<?(?P<name>[a-zA-Z\.\_]+)\srunning\=(?P<running>True|False)\sclosed\=(?P<closed>True|False)\sdebug\=(?P<debug>True|False)\>", re.IGNORECASE)
    cog_import_base_path = BASE_CONFIG.retrieve('general_settings', 'cogs_location', typus=str, direct_fallback="antipetros_discordbot.cogs")

    required_folder = [RequiredFolder(APPDATA["fixed_data"])]
    required_files = [RequiredFile(alive_phrases_file, [], RequiredFile.FileType.JSON), RequiredFile(who_is_trigger_phrases_file, [], RequiredFile.FileType.JSON)]


# endregion[ClassAttributes]

# region [Init]

    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.latest_who_is_triggered_time = datetime.utcnow()
        self.reaction_remove_ids = []
        self.ready = False
        self.listeners_enabled = {'stop_the_reaction_petros_listener': False}
        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)
# endregion[Init]

# region [Setup]
    @universal_log_profiler
    async def on_ready_setup(self):
        # self.garbage_clean_loop.start()
        reaction_remove_ids = [self.bot.id] + [_id for _id in self.bot.owner_ids]
        self.reaction_remove_ids = set(reaction_remove_ids)
        asyncio.create_task(self._update_listener_enabled())
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        if UpdateTypus.CONFIG in typus:
            asyncio.create_task(self._update_listener_enabled())
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Loops]

    @tasks.loop(hours=1)
    @universal_log_profiler
    async def garbage_clean_loop(self):
        if self.ready is False:
            return
        log.info('running garbage clean')
        x = gc.collect()
        log.info('Garbage Clean collected "%s"', x)

# endregion[Loops]

# region [Properties]

    @property
    @universal_log_profiler
    def alive_phrases(self):
        if os.path.isfile(self.alive_phrases_file) is False:
            writejson(['I am alive!'], self.alive_phrases_file)
        return loadjson(self.alive_phrases_file)


# endregion[Properties]

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
            asyncio.create_task(reaction.remove(user))


# endregion[Listener]

    @auto_meta_info_command(aliases=['reload', 'refresh'])
    @commands.is_owner()
    async def reload_all_ext(self, ctx):
        """
        Reloads all enabled extensions.

        Currently not working perfectly, it is recommended to just restart the bot.

        Example:
            @AntiPetros reload_all_ext
        """
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
        """
        Shuts the bot down, via normal shutdown procedure.

        Args:
            reason (str, optional): The Reason that should be written to the Log of the Bot. Defaults to 'No reason given'.

        Example:
            @AntiPetros shutdown
        """
        log.critical('shutdown command received from "%s" with reason: "%s"', ctx.author.name, reason)
        await ctx.message.delete()
        await self.bot.shutdown_mechanic()

    @ auto_meta_info_command(aliases=['you_dead?', 'are-you-there', 'poke-with-stick'])
    async def life_check(self, ctx: commands.Context):
        """
        Checks if the bot is running, receiving messages and capable to answer, or even if two instances are running.

        This is a more fun version of a `pong` command

        Example:
            @AntiPetros life_check
        """
        if random.randint(0, len(self.alive_phrases)) == 0:
            file = discord.File(APPDATA['bertha.png'])
            await ctx.reply('My assistent will record your command for me, please speak into her Banhammer', file=file)
            return
        await ctx.reply(random.choice(self.alive_phrases))

    @ auto_meta_info_command()
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def add_to_blacklist(self, ctx, user: discord.Member):
        """
        Adds a User to the Bots Blacklist.

        The User will not be able to trigger the bot as long as he is on the Blacklist. Best to use user-id as the parameter.

        Args:
            user (discord.Member): A discord User of the Guild. Input can be name or Id, but best to use Id.

        Example:
            @AntiPetros add_to_blacklist 576522029470056450
        """
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
        """
        Removes a User from the Blacklist.

        Best to use user-id as the parameter.

        Args:
            user (discord.Member): A discord User of the Guild. Input can be name or Id, but best to use Id.

        Example:
            @AntiPetros remove_from_blacklist 576522029470056450
        """

        await self.bot.unblacklist_user(user)
        await ctx.send(f"I have unblacklisted user {user.name}")

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
    @only_giddi()
    async def send_loop_info(self, ctx: commands.Context, loop_attr: str = None):
        """
        Tells which loop is running.

        """
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
        """
        Unloads a specific Cog.

        This disables all functionality and all backgroundtasks associated with that Cog. It also sets the config to not load the cog, so it does not get reloaded on accident.

        Args:
            cog (CogConverter): Name of the Cog, case-INsensitive. prefix `Cog` is optional.

        Example:
            @AntiPetros disable_cog Klimbim
        """
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
        """
        Gives a List of all currently active and loaded Cogs.

        Example:
            @AntiPetros current_cogs
        """
        text = ""
        for cog_name, cog_object in self.bot.cogs.items():
            text += f"NAME: {cog_name}, CONFIG_NAME: {cog_object.config_name}\n{'-'*10}\n"
        await self.bot.split_to_messages(ctx, text, in_codeblock=True, syntax_highlighting='fix')

    @ auto_meta_info_command()
    @owner_or_admin()
    async def query_rate_limited(self, ctx: commands.Context):
        """
        Checks if the bot is rate limited currently.

        The bot checks this every 30 min anyways (and logs the result), this command checks it on demand.

        Example:
            @AntiPetros query_rate_limited
        """
        result = self.bot.is_ws_ratelimited()
        verbose_result = "**IS**" if result is True else "**IS NOT**"
        color = 'red' if result is True else "green"
        thumbnail = "cross_mark" if result is True else "check_mark"
        embed_data = await self.bot.make_generic_embed(title="Rate Limit Check", description=f"The Bot {verbose_result} currently Rate Limited.", color=color, thumbnail=thumbnail)
        await ctx.send(**embed_data)


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
    bot.add_cog(BotAdminCog(bot))

# endregion[Main_Exec]
