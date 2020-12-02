
# * Standard Library Imports -->
import os
from datetime import datetime
# * Third Party Imports -->
import discord
from discord import DiscordException
from fuzzywuzzy import process as fuzzprocess
from discord.ext import commands

# * Local Imports -->
from antipetros_discordbot.utility.message_helper import add_to_embed_listfield
from antipetros_discordbot.utility.gidtools_functions import pathmaker
from antipetros_discordbot.data.config.config_singleton import CONFIG_DIR, BASE_CONFIG, COGS_CONFIG
from antipetros_discordbot.utility.misc import seconds_to_pretty
import gidlogger as glog

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# region [Logging]

log = glog.aux_logger(__name__)
log.debug(glog.imported(__name__))

# endregion[Logging]


class Administration(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.is_debug = BASE_CONFIG.getboolean('general_settings', 'is_debug')
        self.all_configs = [BASE_CONFIG, COGS_CONFIG]
        self.allowed_channels = set(COGS_CONFIG.getlist('save_suggestions', 'allowed_channels'))
        self.allowed_dm_invoker_ids = list(map(int, COGS_CONFIG.getlist('admin', 'allowed_dm_ids')))
        self.config_dir = CONFIG_DIR

    @commands.Cog.listener(name='on_ready')
    async def extra_cog_setup(self):
        log.info(f"{self} Cog ----> nothing to set up")

    async def get_available_configs(self):  # sourcery skip: dict-comprehension
        found_configs = {}
        for _file in os.scandir(self.config_dir):
            if 'config' in _file.name and os.path.splitext(_file.name)[1] in ['.ini', '.json', '.yaml', '.toml']:
                found_configs[os.path.splitext(_file.name)[0]] = _file.name
        return found_configs

    async def config_file_to_discord_file(self, config_name):
        config_path = pathmaker(self.config_dir, config_name) if '/' not in config_name else config_name
        return discord.File(config_path, config_name)

    async def match_config_name(self, config_name_input):
        available_configs = await self.get_available_configs()
        _result = fuzzprocess.extractOne(config_name_input, choices=available_configs.keys(), score_cutoff=80)
        if _result is None:
            return None
        else:
            return pathmaker(self.config_dir, available_configs[_result[0]])

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('admin', 'allowed_roles'))
    async def reload_all_ext(self, ctx):
        if ctx.channel.name not in self.allowed_channels:
            return
        _extensions_list = []
        BASE_CONFIG.read()
        COGS_CONFIG.read()
        reloaded_extensions = ''
        _base_location = BASE_CONFIG.get('general_settings', 'cogs_location')
        for _extension in BASE_CONFIG.options('extensions'):
            if BASE_CONFIG.getboolean('extensions', _extension) is True:
                _location = _base_location + '.' + _extension
                try:
                    self.bot.unload_extension(_location)
                    self.bot.load_extension(_location)
                    reloaded_extensions += f"> __'{_extension}'__ was **SUCCESSFULLY** reloaded!\n\n"
                except DiscordException as error:
                    log.error(error)

        _delete_time = 5 if self.is_debug is True else 30
        await ctx.send(f"**successfully reloaded the following extensions:**\n{reloaded_extensions}", delete_after=_delete_time)
        await ctx.message.delete(delay=float(_delete_time - (_delete_time // 2)))

    @commands.command(name='die_antipetros_die')
    @commands.has_any_role(*COGS_CONFIG.getlist('admin', 'allowed_roles'))
    async def shutdown(self, ctx):
        if ctx.channel.name in self.allowed_channels:
            await ctx.send('cya!')
            await self.bot.logout()

    @commands.command(name='list_configs')
    @commands.dm_only()
    async def list_configs(self, ctx):
        if ctx.author.id in self.allowed_dm_invoker_ids:
            available_configs = await self.get_available_configs()
            _embed = discord.Embed(title="Anti Petros Report")
            await add_to_embed_listfield(_embed, 'Available Configs', available_configs.keys(), prefix='-')
            await ctx.send(embed=_embed)
            log.info("config list send to '%s'", ctx.author.name)

    @commands.command(name='send_config')
    @commands.dm_only()
    async def config_request(self, ctx, config_name='all'):
        if ctx.author.id in self.allowed_dm_invoker_ids:
            available_configs = await self.get_available_configs()
            requested_configs = []
            if config_name.casefold() == 'all':
                requested_configs = [conf_file_name for key, conf_file_name in available_configs.items()]

            else:
                _req_config_path = await self.match_config_name(config_name)
                requested_configs.append(os.path.basename(_req_config_path))

            if requested_configs == []:
                await ctx.send(f'I was **NOT** able to find a config named `{config_name}`!\nTry again with `all` as argument, or request the available configs with the command `list_configs`')
            else:
                for req_config in requested_configs:
                    _msg = f"Here is the file for the requested config `{req_config}`"
                    _file = await self.config_file_to_discord_file(req_config)
                    await ctx.send(_msg, file=_file)
                log.info("requested configs (%s) send to %s", ", ".join(requested_configs), ctx.author.name)

    @commands.command(name='overwrite_config')
    @commands.dm_only()
    async def overwrite_config_from_file(self, ctx, config_name):
        if ctx.author.id not in self.allowed_dm_invoker_ids:
            return
        if len(ctx.message.attachments) > 1:
            await ctx.send('please only send a single file with the command')
            return
        _file = ctx.message.attachments[0]
        _config_path = await self.match_config_name(config_name)
        if _config_path is None:
            await ctx.send(f'could not find a config that fuzzy matches `{config_name}`')
        else:
            await _file.save(_config_path)
            for cfg in self.all_configs:
                cfg.read()
            await ctx.send(f'saved your file as `{os.path.basename(_config_path)}`.\n\n_You may have to reload the Cogs or restart the bot for it to take effect!_')

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def add_to_blacklist(self, ctx, user_id: int):
        if ctx.channel.name not in self.allowed_channels:
            return
        user = await self.bot.fetch_user(user_id)
        if user is None:
            await ctx.send(f"Can not find a User with the id '{str(user_id)}'!")
            return
        if user.bot is True:
            await ctx.send("the user you are trying to add is a **__BOT__**!\n\nThis can't be done!")
            return
        current_blacklist = self.bot.blacklist_user
        current_blacklist.append(user_id)
        BASE_CONFIG.set('blacklist', 'user', current_blacklist)
        BASE_CONFIG.save()
        if self.bot.is_debug is True:
            await user.send(f"***THIS IS JUST A TEST, SORRY FOR THE DM BOTHER***\n\nYou have been put on my __BLACKLIST__, you won't be able to invoke my commands.\n\nIf you think this was done in error or other questions, contact **__{self.bot.contact_user}__** per DM!")
        else:
            await user.send(f"You have been put on my __BLACKLIST__, you won't be able to invoke my commands.\n\nIf you think this was done in error or other questions, contact **__{self.bot.contact_user}__** per DM!")
        await ctx.send(f"User '{user.name}' with the id '{user.id}' was added to my blacklist, he wont be able to invoke my commands!\n\nI have also notified him by DM of this fact!")

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def remove_from_blacklist(self, ctx, user_id: int):
        if ctx.channel.name not in self.allowed_channels:
            return
        user = await self.bot.fetch_user(user_id)
        if user is None:
            await ctx.send(f"Can not find a User with the id '{str(user_id)}'!")
            return
        current_blacklist = self.bot.blacklist_user
        if user.id not in current_blacklist:
            await ctx.send(f"User '{user.name}' with User_id '{user.id}' is currently **__NOT__** in my ***Blacklist***\n and can therefor not be removed from the ***Blacklist***!")
            return

        for index, item in enumerate(current_blacklist):
            if item == user_id:
                to_delete_index = index
                break
        current_blacklist.pop(to_delete_index)
        BASE_CONFIG.set('blacklist', 'user', current_blacklist)
        BASE_CONFIG.save()
        if self.bot.is_debug is True:
            await user.send("***THIS IS JUST A TEST, SORRY FOR THE DM BOTHER***\n\nYou have been **__REMOVED__** from my Blacklist.\n\nYou can again invoke my commands again!")
        else:
            await user.send("You have been **__REMOVED__** from my Blacklist.\n\nYou can again invoke my commands again!")
        await ctx.send(f"User '{user.name}' with User_id '{user.id}' was removed from my Blacklist.\n\nHe is now able again, to invoke my commands!")

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def tell_uptime(self, ctx):
        if ctx.channel.name not in self.allowed_channels:
            return
        now_time = datetime.utcnow()
        delta_time = now_time - self.bot.start_time
        seconds = round(delta_time.total_seconds())
        await ctx.send(f"__Uptime__ -->\n\t\t| {str(seconds_to_pretty(seconds))}")
        log.info(f"reported uptime to '{ctx.author.name}'")

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def delete_msg(self, ctx, msg_id: int):
        if ctx.channel.name not in self.allowed_channels:
            return
        channel = ctx.channel
        message = await channel.fetch_message(msg_id)
        await message.delete()
        await ctx.message.delete()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__


def setup(bot):
    bot.add_cog(Administration(bot))
