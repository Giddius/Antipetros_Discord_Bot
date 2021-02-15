

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import random
from datetime import datetime

# * Third Party Imports --------------------------------------------------------------------------------->
import arrow
import discord
from discord import DiscordException
from humanize import naturaltime
from fuzzywuzzy import process as fuzzprocess
from discord.ext import commands

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.misc import save_commands, seconds_to_pretty, async_seconds_to_pretty_normal
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role_2
from antipetros_discordbot.utility.named_tuples import FeatureSuggestionItem
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.data_gathering import gather_data
from antipetros_discordbot.utility.message_helper import add_to_embed_listfield
from antipetros_discordbot.utility.gidtools_functions import loadjson, pickleit, pathmaker, writejson, get_pickled
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogState
# endregion[Imports]

# region [TODO]


# TODO: get_logs command
# TODO: get_appdata_location command


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
CONFIG_NAME = 'discord_admin'
# endregion[Constants]


class AdministrationCog(commands.Cog, command_attrs={'hidden': True, "name": "AdministrationCog"}):
    """
    Soon
    """
    # region [ClassAttributes]

    config_name = CONFIG_NAME

    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.OPEN_TODOS | CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING | CogState.OUTDATED | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 05:21:10",
                             "8f8fac3c998a0c078515c34712eff238644084f8de06831e9aa13dc36d42978885790242db11e078f4b8f3aa576af177c5143144351d807347e58797eb614027")}
    # endregion[ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.do_not_reload_cogs = ['admin_cogs.admin_cog', 'admin_cogs.performance_cog']
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Properties]

    @ property
    def allowed_dm_invoker_ids(self):
        return set(map(int, COGS_CONFIG.getlist(self.config_name, 'allowed_dm_ids')))

    @ property
    def allowed_channels(self):
        return set(COGS_CONFIG.getlist(self.config_name, 'allowed_channels'))

# endregion[Properties]

    async def on_ready_setup(self):
        pass

    @ commands.command(aliases=get_aliases("make_feature_suggestion"))
    async def make_feature_suggestion(self, ctx, *, suggestion_content):

        author = ctx.author
        extra_data = (ctx.message.attachments[0].filename, await ctx.message.attachments[0].read()) if len(ctx.message.attachments) != 0 else None

        author_roles = [role.name for role in author.roles if 'everyone' not in role.name.casefold()]

        now = datetime.utcnow()

        extra_data_path = None
        if extra_data is not None:

            extra_data_path = await self.bot.save_feature_suggestion_extra_data(*extra_data)
        fmt = self.bot.std_date_time_format
        mod_message = suggestion_content if len(suggestion_content) < 1024 else 'see next message'
        feature_suggestion_item = FeatureSuggestionItem(author.name, author.nick, author.id, author_roles, author.top_role.name, author.joined_at.strftime(fmt), now.strftime(fmt), mod_message, extra_data_path)
        embed = await make_basic_embed(title='New Feature Suggestion', text=f'send from channel `{ctx.channel.name}`', symbol='save', **feature_suggestion_item._asdict())
        await self.bot.message_creator(embed=embed)
        if mod_message == 'see next message':
            await self.bot.message_creator(message=suggestion_content)
        feature_suggestion_item = feature_suggestion_item._replace(message=suggestion_content)
        await self.bot.add_to_feature_suggestions(feature_suggestion_item)
        await ctx.send(content=f"your suggestion has been sent to the bot creator --> **{self.bot.creator.name}** <--")

    @ commands.command(aliases=get_aliases("add_to_blacklist"))
    @allowed_channel_and_allowed_role_2()
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

    @ commands.command(aliases=get_aliases("remove_from_blacklist"))
    @allowed_channel_and_allowed_role_2()
    async def remove_from_blacklist(self, ctx, user: discord.Member):

        await self.bot.unblacklist_user(user)
        await ctx.send(f"I have unblacklisted user {user.name}")

    @ commands.command(aliases=get_aliases("tell_uptime"))
    @allowed_channel_and_allowed_role_2()
    async def tell_uptime(self, ctx):

        now_time = datetime.utcnow()
        delta_time = now_time - await self.bot.support.start_time
        seconds = round(delta_time.total_seconds())
        # TODO: make as embed
        await ctx.send(f"__Uptime__ -->\n\t\t| {str(seconds_to_pretty(seconds))}")

    @ commands.command(aliases=get_aliases("delete_msg"))
    @allowed_channel_and_allowed_role_2()
    async def delete_msg(self, ctx, msg_id: int):

        channel = ctx.channel
        message = await channel.fetch_message(msg_id)
        await message.delete()
        await ctx.message.delete()

    @ commands.command(aliases=get_aliases("write_data"))
    @ commands.is_owner()
    @ allowed_channel_and_allowed_role_2()
    async def write_data(self, ctx):
        await gather_data(self.bot)
        await ctx.send(embed=await make_basic_embed(title='Data Collected', text='Data was gathered and written to the assigned files', symbol='save', collected_data='This command only collected fixed data like role_ids, channel_ids,...\n', reason='Data is collected and saved to a json file so to not relying on getting it at runtime, as this kind of data is unchanging', if_it_changes='then this command can just be run again'))

    @ commands.command(aliases=get_aliases("show_command_names"))
    @allowed_channel_and_allowed_role_2()
    async def show_command_names(self, ctx):

        _out = []

        for cog_name, cog_object in self.bot.cogs.items():
            for command in cog_object.get_commands():
                _out.append('__**' + str(command.name) + '**__' + ': ```\n' + str(command.help).split('\n')[0] + '\n```')
        await self.bot.split_to_messages(ctx, '\n---\n'.join(_out), split_on='\n---\n')

    def __repr__(self):
        return f"{self.name}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(AdministrationCog(bot))
