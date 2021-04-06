
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from datetime import datetime, timezone
import asyncio
import secrets
from textwrap import dedent
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from dateparser import parse as date_parse
from discord.ext import flags, tasks, commands
from async_property import async_property
from async_property import async_property
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import make_config_name
from antipetros_discordbot.utility.enums import CogState, UpdateTypus
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role_2, allowed_requester, command_enabled_checker, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command, AntiPetrosFlagCommand
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_give_away_cog import GiveAwayEvent
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH

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
COG_NAME = "GiveAwayCog"
CONFIG_NAME = make_config_name(COG_NAME)
# endregion[Constants]

# region [Helper]

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion [Helper]


class GiveAwayCog(commands.Cog, command_attrs={'name': COG_NAME, "description": "", "hidden": True}):
    """
    Soon
    """
# region [ClassAttributes]

    config_name = CONFIG_NAME
    give_away_data_file = pathmaker(APPDATA['json_data'], 'give_aways.json')
    give_away_item = GiveAwayEvent
    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.FEATURE_MISSING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 05:22:34",
                             "8afa88580ca36d0f7f103683f1fe29c200a2981113b8bb4b8ef9d52a4129de62545f1db6fd27be8c26e2fb52408b9f0f62e07faa4e23adf8e8c5d8864da389b1")}
    required_config_data = dedent("""
                                  embed_thumbnail = https://upload.wikimedia.org/wikipedia/commons/6/62/Gift_box_icon.png
                                  """)
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.give_away_item.bot = self.bot
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        if os.path.isfile(self.give_away_data_file) is False:
            writejson([], self.give_away_data_file)
        self.ready = False
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @async_property
    async def give_aways(self):
        _out = []
        data = loadjson(self.give_away_data_file)
        for item in data:
            _out.append(await GiveAwayEvent.from_dict(item))
        return _out

# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        await asyncio.sleep(5)
        self.check_give_away_ended_loop.start()
        self.clean_emojis_from_reaction.start()
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Loops]

    @tasks.loop(seconds=30, reconnect=True)
    async def check_give_away_ended_loop(self):
        await self.bot.wait_until_ready()
        for give_away_event in await self.give_aways:
            if datetime.utcnow() >= give_away_event.end_date_time:
                await self.give_away_finished(give_away_event)

    @tasks.loop(seconds=5, reconnect=True)
    async def clean_emojis_from_reaction(self):
        await self.bot.wait_until_ready()
        try:
            for give_away_event in await self.give_aways:
                for reaction in give_away_event.message.reactions:
                    if normalize_emoji(str(reaction.emoji)) != normalize_emoji(give_away_event.enter_emoji):
                        await give_away_event.message.clear_reaction(reaction.emoji)
                        await give_away_event.message.clear_reaction(str(reaction))
        except discord.errors.NotFound:
            pass

# endregion [Loops]

# region [Listener]

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.ready is False:
            return
        try:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            if message.author.bot is True:
                return
            for item in await self.give_aways:
                if payload.message_id == item.message.id and normalize_emoji(payload.emoji.name) != normalize_emoji(item.enter_emoji):
                    for reaction in message.reactions:
                        if normalize_emoji(str(reaction.emoji)) != normalize_emoji(item.enter_emoji):
                            await message.clear_reaction(reaction.emoji)
        except discord.errors.NotFound:
            return

# endregion [Listener]

# region [Commands]

    async def give_away_finished(self, event_item):

        users = []
        for reaction in event_item.message.reactions:
            if normalize_emoji(str(reaction.emoji)) == normalize_emoji(str(event_item.enter_emoji)):
                users = await reaction.users().flatten()
                users = [user for user in users if user.bot is False]
        winners = []
        if len(users) == 0:
            abort_embed_data = await self.bot.make_generic_embed(title='No Participants', description=f'there were no participants at the end of the give away "{event_item.title}"',
                                                                 author='not_set',
                                                                 footer='not_set',
                                                                 thumbnail='cancelled')
            await event_item.author.send(**abort_embed_data)
            await event_item.message.delete()
            await self.remove_give_away(event_item)
            return

        for _ in range(0, min(event_item.amount_winners, len(users))):
            winner_num = secrets.randbelow(len(users))
            winners.append(users.pop(winner_num))

        embed_data = await self.bot.make_generic_embed(title=event_item.title,
                                                       description=event_item.end_message,
                                                       fields=[self.bot.field_item(name=f"{index+1}. Winner", value=winner.name, inline=False) for index, winner in enumerate(winners)],
                                                       footer='not_set',
                                                       thumbnail=COGS_CONFIG.retrieve(self.config_name, 'embed_thumbnail', typus=str, direct_fallback="https://upload.wikimedia.org/wikipedia/commons/6/62/Gift_box_icon.png"))
        await event_item.channel.send(**embed_data)
        await self.notify_author(event_item, winners, len(users) + len(winners))
        await event_item.message.delete()
        await self.remove_give_away(event_item)

    async def notify_author(self, event_item, winners, amount_participants):
        embed_data = await self.bot.make_generic_embed(title=f'Give-Away "{event_item.title}" has finished', description=f'There were {amount_participants} participants',
                                                       fields=[self.bot.field_item(name=f"{index+1}. Winner", value=winner.name, inline=False) for index, winner in enumerate(winners)],
                                                       footer='not_set',
                                                       thumbnail=None)
        await event_item.author.send(**embed_data)

    @flags.add_flag("--title", '-t', type=str, default='Antistasi Give-Away')
    @flags.add_flag("--end-date", "-end", type=str, default="24 hours")
    @flags.add_flag("--num-winners", '-nw', type=int, default=1)
    @flags.add_flag("--end-message", "-emsg", type=str, default="Give away has finished!")
    @flags.add_flag("--start-message", "-smsg", type=str)
    @flags.add_flag("--enter-emoji", '-em', type=str, default="🎁")
    @auto_meta_info_command(cls=flags.FlagCommand, enabled=get_command_enabled("create_giveaway"))
    @allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    @log_invoker(logger=log, level="info")
    async def create_giveaway(self, ctx, **flags):
        give_away_title = flags.get('title')
        if give_away_title in [item.title for item in await self.give_aways]:
            await ctx.send(f"Title '{give_away_title}' already is in use for another active give away")
            return
        date_string = 'in ' + flags.get('end_date')
        end_date_time = date_parse(date_string).astimezone(timezone.utc)
        end_date_time = end_date_time.replace(second=0)

        confirm_embed = await self.bot.make_generic_embed(title='Do you want to start a give away with these parameters?', fields=[self.bot.field_item('Name', give_away_title, False),
                                                                                                                                   self.bot.field_item('Number of Winners', flags.get('num_winners'), False),
                                                                                                                                   self.bot.field_item('End Date', end_date_time.strftime("%Y.%m.%d %H:%M:%S UTC"), False),
                                                                                                                                   self.bot.field_item('Start Message', flags.get('start_message'), False),
                                                                                                                                   self.bot.field_item('End Message', flags.get('end_message'), False),
                                                                                                                                   self.bot.field_item('Participation Emoji', flags.get('enter_emoji'), False)],
                                                          footer={'text': '5 min to answer'})
        confirm_message = await ctx.send(**confirm_embed)
        await confirm_message.add_reaction('✅')
        await confirm_message.add_reaction('❎')

        def check_confirm(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❎']

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=300.0, check=check_confirm)
        except asyncio.TimeoutError:
            await confirm_message.delete()
            timeout_embed_data = await self.bot.make_generic_embed(title='Time-Out',
                                                                   description=f'Give-away initialisation for Give-Away **"{flags.get("title")}"** aborted, because the conformation message timed out without an answer!',
                                                                   author='not_set',
                                                                   footer='not_set',
                                                                   thumbnail='abort',
                                                                   color='red')
            await ctx.send(**timeout_embed_data, delete_after=2 * 60)
            return
        else:
            await confirm_message.delete()
            if str(reaction.emoji) == '❎':
                canceled_embed_data = await self.bot.make_generic_embed(title='Cancelled',
                                                                        description=f'Give-away initialisation for Give-Away **"{flags.get("title")}"** aborted, because of user cancellation!',
                                                                        author='not_set',
                                                                        footer='not_set',
                                                                        thumbnail='abort',
                                                                        color='red')
                await ctx.send(**canceled_embed_data, delete_after=2 * 60)
                return
            await ctx.message.delete()
            embed_data = await self.bot.make_generic_embed(author='default_author',
                                                           title=flags.get('title'),
                                                           description=flags.get('start_message'),
                                                           fields=[self.bot.field_item('Give Away ends at', end_date_time.strftime("%Y.%m.%d %H:%M UTC") + f"\n\nYou have {flags.get('end_date')} to react\n{ZERO_WIDTH}", False),
                                                                   self.bot.field_item('To enter the Give-Away, react to this post with', flags.get("enter_emoji"), False)],
                                                           footer="not_set",
                                                           thumbnail=COGS_CONFIG.retrieve(self.config_name, 'embed_thumbnail', typus=str, direct_fallback="https://upload.wikimedia.org/wikipedia/commons/6/62/Gift_box_icon.png"))
            give_away_message = await ctx.send(**embed_data)
            await give_away_message.add_reaction(flags.get('enter_emoji'))
            await self.add_give_away(self.give_away_item(title=give_away_title,
                                                         enter_emoji=flags.get('enter_emoji'),
                                                         end_date_time=end_date_time,
                                                         end_message=flags.get('end_message'),
                                                         amount_winners=flags.get('num_winners'),
                                                         author=ctx.author,
                                                         channel=ctx.channel,
                                                         message=give_away_message))

    @ auto_meta_info_command(enabled=get_command_enabled("abort_give_away"))
    @ allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    @ log_invoker(logger=log, level="info")
    async def abort_give_away(self, ctx):
        """
        NOT IMPLEMENTED
        """
        await self.bot.not_implemented(ctx)
        return

    @ auto_meta_info_command(enabled=get_command_enabled("finish_give_away"))
    @ allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    @ log_invoker(logger=log, level="info")
    async def finish_give_away(self, ctx):
        """
        NOT IMPLEMENTED
        """
        await self.bot.not_implemented(ctx)
        return


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [Embeds]


# endregion [Embeds]

# region [HelperMethods]


    async def add_give_away(self, give_away_event):
        data = loadjson(self.give_away_data_file)
        data.append(await give_away_event.to_dict())
        writejson(data, self.give_away_data_file)

    async def remove_give_away(self, give_away_event):
        data = loadjson(self.give_away_data_file)
        data.remove(await give_away_event.to_dict())
        writejson(data, self.give_away_data_file)

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
        self.clean_emojis_from_reaction.stop()
        log.debug("Cog '%s' UNLOADED!", str(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(GiveAwayCog(bot)))
