
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import gc
import os
import unicodedata
from datetime import datetime, timezone
from collections import namedtuple
import asyncio
# * Third Party Imports --------------------------------------------------------------------------------->
import aiohttp
import discord
from discord import File, Embed, DiscordException
from dateparser import parse as date_parse
from discord.ext import flags, tasks, commands
from async_property import async_property
import pytz
import random
import arrow
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.misc import CogConfigReadOnly, save_commands
from antipetros_discordbot.utility.enums import RequestStatus
from antipetros_discordbot.utility.checks import log_invoker, in_allowed_channels, allowed_channel_and_allowed_role
from antipetros_discordbot.utility.named_tuples import LINK_DATA_ITEM, GiveAwayEventItem
from antipetros_discordbot.utility.embed_helpers import EMBED_SYMBOLS, make_basic_embed
from antipetros_discordbot.utility.sqldata_storager import LinkDataStorageSQLite
from antipetros_discordbot.utility.gidtools_functions import writeit, loadjson, pathmaker, writejson, create_file, create_folder
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper

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
CONFIG_NAME = "give_away"
# endregion[Constants]

# region [Helper]

_from_cog_config = CogConfigReadOnly(CONFIG_NAME)

# endregion [Helper]

# "GiveAwayEventItem" =  ['name', 'channel_name', 'message_id', 'enter_emoji', 'end_date_time', 'end_message', 'amount_winners']
ExpItem = namedtuple("ExpItem", ['name', 'end_date_time', 'message', 'old_msg_id', 'channel_name'])


class GiveAwayCog(commands.Cog, command_attrs={'name': "GiveAwayCog", "description": ""}):
    """
    Soon
    """
# region [ClassAttributes]

    give_away_data_file = pathmaker(APPDATA['json_data'], 'give_aways.json')
    give_away_item = GiveAwayEventItem
    docattrs = {'show_in_readme': True,
                'is_ready': False}
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.give_aways = None
        if os.path.isfile(self.give_away_data_file) is False:
            writejson([], self.give_away_data_file)
        if os.environ.get('INFO_RUN', '') == "1":
            save_commands(self)
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]


# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        await self.load_give_aways()
        await asyncio.sleep(5)
        self.check_give_away_ended_loop.start()
        log.debug('setup for cog "%s" finished', str(self))

# endregion [Setup]

# region [Loops]

    @tasks.loop(minutes=1, reconnect=True)
    async def check_give_away_ended_loop(self):
        if self.give_aways is None:
            await self.load_give_aways()
        for give_away_event in self.give_aways:
            if arrow.utcnow() >= give_away_event.end_date_time:
                await self.give_away_finished(give_away_event)

# endregion [Loops]

# region [Listener]

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        for item in self.give_aways:
            if payload.message_id == item.message_id and payload.emoji != item.enter_emoji:
                for reaction in message.reactions:
                    if reaction.emoji != item.enter_emoji:
                        await reaction.remove(payload.member)

# endregion [Listener]

# region [Commands]

    async def give_away_finished(self, event_item):
        channel = await self.bot.channel_from_name(event_item.channel_name)

        msg = await channel.fetch_message(event_item.message_id)

        users = []
        for reaction in msg.reactions:
            if reaction.emoji == event_item.enter_emoji:
                users = await reaction.users().flatten()
                users = [user for user in users if user.bot is False]

        winners = random.choices(users, k=event_item.amount_winners)
        await channel.send(event_item.end_message)
        await channel.send('\n'.join([winner.display_name for winner in winners]))
        await msg.delete()
        self.give_aways.remove(event_item)
        await self.save_give_aways()

    @flags.add_flag("--end-date", type=str, default="5min")
    @flags.add_flag("--name", type=str)
    @flags.add_flag("--num-winners", type=int, default=1)
    @flags.add_flag("--end-message", type=str, default="give away has finished!")
    @flags.add_flag("--start-message", type=str)
    @commands.command(aliases=get_aliases("create_giveaway"), cls=flags.FlagCommand)
    @allowed_channel_and_allowed_role(config_name=CONFIG_NAME, in_dm_allowed=False)
    @log_invoker(logger=log, level="info")
    async def create_giveaway(self, ctx, **flags):
        give_away_name = flags.get('name')
        if give_away_name in [item.name for item in self.give_aways]:
            await ctx.send(f"Name '{give_away_name}' already is in use for another active give away")
            return
        date_string = 'in ' + flags.get('end_date')
        end_date_time = date_parse(date_string).astimezone(timezone.utc)
        end_date_time = end_date_time.replace(second=0)
        await ctx.message.delete()
        confirm_embed = await self.bot.make_generic_embed(title='Do you want to start a give away with these parameters?', fields=[self.bot.field_item('Name', give_away_name, False),
                                                                                                                                   self.bot.field_item('Number of Winners', flags.get('num_winners'), False),
                                                                                                                                   self.bot.field_item('End Date', end_date_time.strftime("%Y.%m.%d %H:%M:%S UTC"), False),
                                                                                                                                   self.bot.field_item('Start Message', flags.get('start_message'), False),
                                                                                                                                   self.bot.field_item('End Message', flags.get('end_message'), False)],
                                                          footer={'text': '5min to answer'})
        confirm_message = await ctx.send(**confirm_embed)
        await confirm_message.add_reaction('✅')
        await confirm_message.add_reaction('❎')

        def check_confirm(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❎']

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=300.0, check=check_confirm)
        except asyncio.TimeoutError:
            await confirm_message.delete()
            await ctx.send('give_away initiation aborted, because of time out')
            return
        else:
            await confirm_message.delete()
            if str(reaction.emoji) == '❎':
                await ctx.send('give_away initiation aborted, user abort')
                return

            embed_data = await self.bot.make_generic_embed(author='default_author',
                                                           footer='default_footer',
                                                           title=flags.get('start_message'),
                                                           fields=[self.bot.field_item('Give Away ends at', end_date_time.strftime("%H:%M UTC"), False)])
            give_away_message = await ctx.send(**embed_data)
            await give_away_message.add_reaction("🎁")
            self.give_aways.append(self.give_away_item(name=give_away_name,
                                                       channel_name=ctx.channel.name,
                                                       message_id=give_away_message.id,
                                                       enter_emoji="🎁",
                                                       end_date_time=end_date_time,
                                                       end_message=flags.get('end_message'),
                                                       amount_winners=flags.get('num_winners')))
            await self.save_give_aways()

    @ commands.command(aliases=get_aliases("abort_give_away"))
    @ allowed_channel_and_allowed_role(config_name=CONFIG_NAME, in_dm_allowed=False)
    @ log_invoker(logger=log, level="info")
    async def abort_give_away(self, ctx):
        pass

    @ commands.command(aliases=get_aliases("finish_give_away"))
    @ allowed_channel_and_allowed_role(config_name=CONFIG_NAME, in_dm_allowed=False)
    @ log_invoker(logger=log, level="info")
    async def finish_give_away(self, ctx):
        pass


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [Embeds]


# endregion [Embeds]

# region [HelperMethods]


    async def load_give_aways(self):
        self.give_aways = [] if self.give_aways is None else self.give_aways
        for item in loadjson(self.give_away_data_file):
            item['end_date_time'] = datetime.fromisoformat(item['end_date_time'])
            self.give_aways.append(self.give_away_item(**item))

    async def save_give_aways(self):

        give_away_data = [item._asdict() for item in self.give_aways]
        for item in give_away_data:
            item['end_date_time'] = item['end_date_time'].isoformat()
        writejson(give_away_data, self.give_away_data_file)

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
        self.check_give_away_ended_loop.stop()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(GiveAwayCog(bot))
