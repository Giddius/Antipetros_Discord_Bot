"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import random
from datetime import datetime
from typing import List
import random
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import commands
import arrow
from humanize import naturaltime
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, pickleit
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.checks import owner_or_admin
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
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class EssentialCommandsKeeper(SubSupportBase):
    cog_import_base_path = BASE_CONFIG.get('general_settings', 'cogs_location')
    shutdown_message_pickle_file = pathmaker(APPDATA['temp_files'], 'last_shutdown_message.pkl')
    goodbye_quotes_file = APPDATA['goodbye_quotes.json']

    def __init__(self, bot: commands.Bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.shutdown_message_pickle = None
        self.add_commands()
        glog.class_init_notification(log, self)

    def add_commands(self):
        self.bot.add_command(commands.Command(self.reload_all_ext, aliases=['reload', 'refresh']))
        self.bot.add_command(commands.Command(self.shutdown, aliases=['die', 'rip', 'go-away', 'go_away', 'go.away', 'goaway', 'get_banned']))
        self.bot.add_listener(self.stop_the_reaction_petros, 'on_reaction_add')

    async def stop_the_reaction_petros(self, reaction: discord.Reaction, user):
        message = reaction.message
        author = message.author
        if user.id == 155149108183695360 and author.id in [self.bot.id, self.bot.creator.id]:
            await reaction.remove(user)

    @property
    def shutdown_message_channel(self):
        channel_name = BASE_CONFIG.retrieve("shutdown_message", "channel_name", typus=str, direct_fallback='bot-testing')
        return self.bot.sync_channel_from_name(channel_name)

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

                        reloaded_extensions.append(self.support.field_item(name=_extension, value=f"{ZERO_WIDTH}\n:white_check_mark:\n{ZERO_WIDTH}", inline=False))
                    except commands.DiscordException as error:
                        log.error(error)
            # await self.bot.to_all_cogs('on_ready_setup')
            _delete_time = 15 if self.is_debug is True else 60
            _embed_data = await self.support.make_generic_embed(title="**successfully reloaded the following extensions**", author='bot_author', thumbnail="update", fields=reloaded_extensions)
            await ctx.send(**_embed_data, delete_after=_delete_time)
            await ctx.message.delete(delay=float(_delete_time))

    @owner_or_admin()
    async def shutdown(self, ctx, *, reason: str = 'No reason given'):
        log.debug('shutdown command received from "%s" with reason: "%s"', ctx.author.name, reason)
        await self.shutdown_mechanic()

    async def shutdown_mechanic(self):
        try:
            started_at = self.support.start_time

            started_at_string = arrow.get(started_at).format('YYYY-MM-DD HH:mm:ss')
            online_duration = naturaltime(datetime.utcnow() - started_at).replace(' ago', '')

            embed = await self.support.make_generic_embed(title=random.choice(loadjson(self.goodbye_quotes_file)),
                                                          description=f'{self.bot.display_name} is shutting down.',
                                                          image=BASE_CONFIG.retrieve('shutdown_message', 'image', typus=str, direct_fallback="https://i.ytimg.com/vi/YATREe6dths/maxresdefault.jpg"),
                                                          type=self.support.embed_types_enum.Image,
                                                          fields=[self.support.field_item(name='Online since', value=str(started_at_string), inline=False), self.support.field_item(name='Online for', value=str(online_duration), inline=False)])
            channel = self.shutdown_message_channel
            last_shutdown_message = await channel.send(**embed)
            pickleit({"message_id": last_shutdown_message.id, "channel_id": last_shutdown_message.channel.id}, self.shutdown_message_pickle_file)

        except Exception as error:
            log.error(error, exc_info=False)
        finally:
            await self.bot.close()

    async def if_ready(self):

        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus):
        return
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self):
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return EssentialCommandsKeeper
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
