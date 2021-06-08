# region [Imports]

# * Standard Library Imports -->
import gc
import os
from typing import List, TYPE_CHECKING
from datetime import datetime
import asyncio
import unicodedata

# * Third Party Imports -->
from validator_collection import validators
import validator_collection
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
# from fuzzywuzzy import fuzz, process
import aiohttp
import discord
from discord.ext import tasks, commands, flags
from async_property import async_property

# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.misc import check_if_url, delete_message_if_text_channel, url_is_alive
from antipetros_discordbot.utility.checks import log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, auto_meta_info_command
from antipetros_discordbot.utility.exceptions import NeededClassAttributeNotSet, TeamMemberRoleNotFoundError


from typing import List, TYPE_CHECKING
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, auto_meta_info_command

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
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class TeamItem:

    config_name = None
    bot = None
    description_thumbnail = "https://i3.lensdump.com/i/Im1Q53.png"

    def __init__(self, team_name: str, channel: discord.TextChannel):
        if self.config_name is None:
            raise NeededClassAttributeNotSet('config_name', self.__class__.__name__)
        if self.bot is None:
            raise NeededClassAttributeNotSet('bot', self.__class__.__name__)
        self.name = team_name
        self.channel = channel
        self.header_message = None
        self.all_member_list_message = None
        self.config_option_names = {'description': f"{self.name.casefold().replace(' ','_')}_description",
                                    'join_description': f"{self.name.casefold().replace(' ','_')}_join_description",
                                    'image': f"{self.name.casefold().replace(' ','_')}_image",
                                    'extra_role': f"{self.name.casefold().replace(' ','_')}_extra_role"}

    @property
    def max_postition(self):
        return max([role.position for role in [self.lead_role, self.member_role, self.helper_role, self.extra_role] if role is not None])

    @property
    def section_seperator(self):
        seperator_char = COGS_CONFIG.retrieve(self.config_name, 'section_seperator_char', typus=str, direct_fallback='=')
        seperator_sequence = seperator_char * 64
        return seperator_sequence[:64]

    @property
    def sub_section_seperator(self):
        sub_seperator_char = COGS_CONFIG.retrieve(self.config_name, 'sub_section_seperator_char', typus=str, direct_fallback='-')
        sub_seperator_sequence = sub_seperator_char * 20
        return sub_seperator_sequence[:20]

    @property
    def description(self):
        description = COGS_CONFIG.retrieve(self.config_name, self.config_option_names.get('description'), typus=str, direct_fallback='not_set')
        if description == 'not_set':
            return None
        return description

    @property
    def join_description(self):
        join_description = COGS_CONFIG.retrieve(self.config_name, self.config_option_names.get('join_description'), typus=str, direct_fallback='not_set')
        if join_description == 'not_set':
            return None
        return join_description

    @property
    def image(self):
        image = COGS_CONFIG.retrieve(self.config_name, self.config_option_names.get('image'), typus=str, direct_fallback='not_set')
        if image == 'not_set':
            return discord.Embed.Empty
        return image

    @property
    def member_role(self):
        return self.bot.role_from_string(self.name)

    @property
    def helper_role(self):
        if "team" in self.name.casefold():
            helper_role_name = self.name.casefold().replace(' team', ' helper')
            helper_role = self.bot.role_from_string(helper_role_name)
            if helper_role is None:
                helper_role_name = f"Trial {self.name}"
                helper_role = self.bot.role_from_string(helper_role_name)
            return helper_role

    @property
    def lead_role(self):
        lead_role_name = f"{self.name} Lead"
        return self.bot.role_from_string(lead_role_name)

    @property
    def extra_role(self):
        extra_role_name = COGS_CONFIG.retrieve(self.config_name, self.config_option_names.get('extra_role'), typus=str, direct_fallback='not_set')
        if extra_role_name == 'not_set':
            return None
        return self.bot.role_from_string(extra_role_name)

    @property
    def member_list_string(self):
        if self.lead_list_string is not None:
            return '\n'.join(f"{member.mention} {member.display_name}" for member in self.member_role.members if f"{member.mention} {member.display_name}" not in self.lead_list_string)
        return '\n'.join(f"{member.mention} {member.display_name}" for member in self.member_role.members)

    @property
    def helper_list_string(self):
        if self.helper_role is None:
            return None
        if self.lead_list_string is not None:
            return '\n'.join(f"{member.mention} {member.display_name}" for member in self.helper_role.members if f"{member.mention} {member.display_name}" not in self.lead_list_string)
        return '\n'.join(f"{member.mention} {member.display_name}" for member in self.helper_role.members)

    @property
    def lead_list_string(self):
        if self.lead_role is None:
            return None
        return '\n'.join(f"{member.mention} {member.display_name}" for member in self.lead_role.members)

    @property
    def extra_role_list_string(self):
        if self.extra_role is None:
            return None
        return '\n'.join(f"{member.mention} {member.display_name}" for member in self.extra_role.members)

    async def header_embed(self):
        embed = discord.Embed(title=self.name, color=self.member_role.color)
        embed.set_image(url=self.image)
        embed.add_field(name="**What do they do:**", value=f"*{self.description}*", inline=False)
        embed.add_field(name="**How to join:**", value=f"*{self.join_description}*", inline=False)
        return embed

    async def all_member_list_text(self):
        text = ""
        if self.lead_list_string is not None:
            text += f"\n{self.sub_section_seperator}\n{self.sub_section_seperator[0] * 5}{self.lead_role.mention}\n{self.sub_section_seperator}\n\n{self.lead_list_string}\n\n"
        text += f"\n{self.sub_section_seperator}\n{self.sub_section_seperator[0] * 5}{self.member_role.mention}\n{self.sub_section_seperator}\n\n{self.member_list_string}\n\n"
        if self.helper_role is not None:
            text += f"\n{self.sub_section_seperator}\n{self.sub_section_seperator[0] * 5}{self.helper_role.mention}\n{self.sub_section_seperator}\n\n{self.helper_list_string}\n\n"
        if self.extra_role is not None:
            text += f"\n{self.sub_section_seperator}\n{self.sub_section_seperator[0] * 5}{self.extra_role.mention}\n{self.sub_section_seperator}\n\n{self.extra_role_list_string}\n\n"
        text += f"{self.section_seperator}\n\n{ZERO_WIDTH}"
        return text

    async def create_messages(self):
        if self.member_role is None:
            log.warning("No Member Role found for Team '%s', Not creating message for this Team", self.name)
            raise TeamMemberRoleNotFoundError
        log.debug("Creating Team Roster Header for '%s'", self.name)
        self.header_message = await self.channel.send(embed=await self.header_embed(), allowed_mentions=discord.AllowedMentions.none())
        await asyncio.sleep(1)
        log.debug("Creating Team Roster List for '%s'", self.name)
        self.all_member_list_message = await self.channel.send(await self.all_member_list_text(), allowed_mentions=discord.AllowedMentions.none())
        log.debug("Finished Team Roster messages creation for '%s'", self.name)

    async def update(self):
        if self.member_role is None:
            log.warning("No Member Role found for Team '%s', Removing Team messages!", self.name)
            await self.delete_messages()
            raise TeamMemberRoleNotFoundError
        if self.header_message is None:
            raise AttributeError(f"No header_message set for Team '{self.name}'")
        if self.all_member_list_message is None:
            raise AttributeError(f"No all_member_list_message set for Team '{self.name}'")
        log.debug("Updating Team Roster Header for '%s'", self.name)
        await self.header_message.edit(embed=await self.header_embed(), allowed_mentions=discord.AllowedMentions.none())
        await asyncio.sleep(1)
        log.debug("Updating Team Roster List for '%s'", self.name)
        await self.all_member_list_message.edit(content=await self.all_member_list_text(), allowed_mentions=discord.AllowedMentions.none())
        log.debug("Finished Updating Team Roster messages for '%s'", self.name)

    def to_dict(self):
        return {'team_name': self.name,
                'channel_id': self.channel.id,
                'header_message_id': self.header_message.id,
                'all_member_list_message_id': self.all_member_list_message.id}

    @classmethod
    async def from_dict(cls, in_values: dict):
        team_name = in_values.get('team_name')
        channel = cls.bot.channel_from_id(in_values.get('channel_id'))
        header_message = await channel.fetch_message(in_values.get('header_message_id'))
        all_member_list_message = await channel.fetch_message(in_values.get('all_member_list_message_id'))

        team_item = cls(team_name, channel)
        team_item.header_message = header_message
        team_item.all_member_list_message = all_member_list_message
        return team_item

    async def delete_messages(self):
        if self.header_message is None or self.all_member_list_message is None:
            log.warning("no messages set for Team '%s'", self.name)
            return
        log.debug('Removing Team roster message of Team "%s"', self.name)
        await self.header_message.delete()
        await self.all_member_list_message.delete()


class TeamRosterCog(AntiPetrosBaseCog, command_attrs={"categories": CommandCategory.ADMINTOOLS, "hidden": True}):
    """
    Keeps a team roster up to date, updates it everytime a role on the Discord Guild changes or gets added or is removed.
    """
# region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING | CogMetaStatus.WORKING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {}}
    team_item_data_file = pathmaker(APPDATA['json_data'], "team_items.json")

    required_folder = []
    required_files = [RequiredFile(team_item_data_file, {"last_changed_message": None, "team_items": []}, RequiredFile.FileType.JSON)]


# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.team_items = None
        self.last_changed_message = None
        TeamItem.config_name = self.config_name
        TeamItem.bot = self.bot
        self.color = "yellowgreen"
        self.ready = False
        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]


# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        await self.bot.antistasi_guild.chunk(cache=True)
        await self._load_team_items()
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        await self.bot.antistasi_guild.chunk(cache=True)
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]

    @commands.Cog.listener(name="on_member_update")
    async def member_roles_changed_listener(self, before: discord.Member, after: discord.Member):
        if any([self.ready, self.bot.setup_finished]) is False or self.bot.is_debug is True:
            return
        if before.roles != after.roles:
            log.debug("updating Team Roster because role on Member was changed")
            await self._update_team_roster()

    @commands.Cog.listener(name="on_guild_role_create")
    async def role_added_listener(self, role: discord.Role):
        if any([self.ready, self.bot.setup_finished]) is False or self.bot.is_debug is True:
            return
        log.debug("updating Team Roster because new role was created")
        await self._update_team_roster()

    @commands.Cog.listener(name="on_guild_role_delete")
    async def role_removed_listener(self, role: discord.Role):
        if any([self.ready, self.bot.setup_finished]) is False or self.bot.is_debug is True:
            return
        log.debug("updating Team Roster because role was deleted")
        await self._update_team_roster()

    @commands.Cog.listener(name="on_guild_role_update")
    async def role_updated_listener(self, before: discord.Role, after: discord.Role):
        if any([self.ready, self.bot.setup_finished]) is False or self.bot.is_debug is True:
            return
        log.debug("updating Team Roster because role was modifed")
        await self._update_team_roster()

# endregion [Listener]

# region [Commands]

    @auto_meta_info_command()
    @commands.is_owner()
    @log_invoker(log, 'critical')
    async def initialize_team_roster(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Creates the Team roster messages.

        This should not have to be called more than once.

        Args:
            channel (discord.TextChannel): Id of channel to build the Team roster (can also use name, but id is safer)

        Example:
            @AntiPetros initialize_team_roster 712054600278081600

        Info:
            When this command is used, it logs the user!
        """
        async with ctx.typing():
            teams = COGS_CONFIG.retrieve(self.config_name, 'team_names', typus=List[str], direct_fallback=[])
            if teams == []:
                embed_data = await self.bot.make_generic_embed(title='No team_names set in Config', description="you have to specify team_names in the config",
                                                               thumbnail="cancelled")
                await ctx.reply(**embed_data, delete_after=120)
                await delete_message_if_text_channel(ctx)
                return
            await self.bot.antistasi_guild.chunk(cache=True)
            self.team_items = []
            self.last_changed_message = None
            for team_name in teams:
                self.team_items.append(TeamItem(team_name, channel))
            self.team_items = sorted(self.team_items, key=lambda x: x.max_postition, reverse=True)
            for item in self.team_items:
                try:
                    await item.create_messages()
                except TeamMemberRoleNotFoundError:
                    self.team_items.remove(item)

            await asyncio.sleep(5)
            await self.create_last_changed_message(channel)
            await self._save_team_items()
            await ctx.send("finished creating Team Roster", delete_after=60)
            await delete_message_if_text_channel(ctx)

    @auto_meta_info_command()
    @commands.is_owner()
    @log_invoker(log, 'critical')
    async def force_update_team_roster(self, ctx: commands.Context):
        """
        Forces the Team Roster to update.

        Can be used often, as there is no negative consequence to it.

        It is provided as a fallback if the automation does not trigger.

        Example:
            @AntiPetros force_update_team_roster

        Info:
            When this command is used, it logs the user!
        """
        for team_item in self.team_items:
            try:
                await team_item.update()
            except TeamMemberRoleNotFoundError:
                self.team_items.remove(team_item)
                await self._save_team_items()
        await self.update_last_changed_message()
        await ctx.author.send('Updated Team Roster!')

        await delete_message_if_text_channel(ctx)

    @auto_meta_info_command()
    @commands.is_owner()
    @log_invoker(log, 'critical')
    async def delete_and_redo_team_roster(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Deletes the Team roster messages and completely redoes them.

        Ultima Ratio version of "force_update_team_roster".

        The Channel has to be entered, as this provides is also an option to change the Team roster channel.

        Args:
            channel (discord.TextChannel): Id of channel to build the Team roster (can also use name, but id is safer)

        Example:
            @AntiPetros delete_and_redo_team_roster 712054600278081600

        Info:
            When this command is used, it logs the user!
        """
        for item in self.team_items:
            await item.delete_messages()
        await self.last_changed_message.delete()
        await self.initialize_team_roster(ctx, channel)

    @auto_meta_info_command()
    @log_invoker(log, 'critical')
    async def team_roster_change_description(self, ctx: commands.Context, team: str, *, new_description: str):
        team_item = {item.name.casefold(): item for item in self.team_items}.get(team.casefold(), None)
        if team_item is None:
            await self._send_team_not_found_embed(ctx, team)
            return

        if team_item.lead_role not in ctx.author.roles:
            await self._send_not_team_lead_embed(ctx, team_item)
            return

        COGS_CONFIG.set(self.config_name, team_item.config_option_names.get('description'), str(new_description))
        await self.force_update_team_roster(ctx)
        await self._send_updated_embed(ctx, team_item, 'Description')

    @auto_meta_info_command()
    @log_invoker(log, 'critical')
    async def team_roster_change_join_description(self, ctx: commands.Context, team: str, *, new_join_description: str):
        team_item = {item.name.casefold(): item for item in self.team_items}.get(team.casefold(), None)
        if team_item is None:
            await self._send_team_not_found_embed(ctx, team)
            return

        if team_item.lead_role not in ctx.author.roles:
            await self._send_not_team_lead_embed(ctx, team_item)
            return

        COGS_CONFIG.set(self.config_name, team_item.config_option_names.get('join_description'), str(new_join_description))
        await self.force_update_team_roster(ctx)
        await self._send_updated_embed(ctx, team_item, 'Join Description')

    @auto_meta_info_command()
    @log_invoker(log, 'critical')
    async def team_roster_change_extra_role(self, ctx: commands.Context, team: str, *, extra_role_name: str):
        team_item = {item.name.casefold(): item for item in self.team_items}.get(team.casefold(), None)
        if team_item is None:
            await self._send_team_not_found_embed(ctx, team)
            return

        if team_item.lead_role not in ctx.author.roles:
            await self._send_not_team_lead_embed(ctx, team_item)
            return

        COGS_CONFIG.set(self.config_name, team_item.config_option_names.get('extra_role'), str(extra_role_name))
        await self.force_update_team_roster(ctx)
        await self._send_updated_embed(ctx, team_item, 'Extra Role')

    @auto_meta_info_command()
    @log_invoker(log, 'critical')
    async def team_roster_change_image(self, ctx: commands.Context, team: str, *, image_url: str):
        team_item = {item.name.casefold(): item for item in self.team_items}.get(team.casefold(), None)
        if team_item is None:
            await self._send_team_not_found_embed(ctx, team)
            return

        if team_item.lead_role not in ctx.author.roles:
            await self._send_not_team_lead_embed(ctx, team_item)
            return
        if await check_if_url(image_url) is False or await url_is_alive(self.bot, image_url) is False:
            embed_data = await self.bot.make_generic_embed(title='Invalid URL', description=f"The URL `{image_url}` is either invalid or dead! Image has to be an https URL that points to an image.\nExample: `https://i3.lensdump.com/i/Im1Q53.png`",
                                                           thumbnail="cancelled")
            await ctx.send(**embed_data, delete_after=120, allowed_mentions=discord.AllowedMentions.none())
            await delete_message_if_text_channel(ctx)
            return
        COGS_CONFIG.set(self.config_name, team_item.config_option_names.get('image'), image_url)
        await self.force_update_team_roster(ctx)
        await self._send_updated_embed(ctx, team_item, 'Image')


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]

    async def _update_team_roster(self):
        for team_item in self.team_items:
            try:
                await team_item.update()
            except TeamMemberRoleNotFoundError:
                self.team_items.remove(team_item)
                await self._save_team_items()
        await self.update_last_changed_message()

    async def _send_updated_embed(self, ctx: commands.Context, team_item: TeamItem, field: str):
        embed_data = await self.bot.make_generic_embed(title=f'{field} updated', description=f"{field} for Team `{team_item.name}` was updated!",
                                                       thumbnail="update")
        await ctx.send(**embed_data, delete_after=120, allowed_mentions=discord.AllowedMentions.none())
        await delete_message_if_text_channel(ctx)

    async def _send_team_not_found_embed(self, ctx: commands.Context, team: str):
        fields = []
        for team_name in (item.name for item in self.team_items):
            fields.append(self.bot.field_item(name=team_name, value=ZERO_WIDTH))
        embed_data = await self.bot.make_generic_embed(title=f'Team "{team}" not found', description=f"Team `{team}` not found in current teams, current teams:",
                                                       fields=fields,
                                                       thumbnail="cancelled")
        await ctx.send(**embed_data, delete_after=120)
        await delete_message_if_text_channel(ctx)

    async def _send_not_team_lead_embed(self, ctx: commands.Context, team_item: TeamItem):
        embed_data = await self.bot.make_generic_embed(title='Not your Team', description=f"To modify an item you have to be Team lead of that Team!\nYou do not have the necessary role {team_item.lead_role.mention} !",
                                                       thumbnail="cancelled")
        await ctx.send(**embed_data, delete_after=120, allowed_mentions=discord.AllowedMentions.none())
        await delete_message_if_text_channel(ctx)

    async def update_last_changed_message(self):
        embed = discord.Embed(title='Last Modified', description=datetime.utcnow().strftime(self.bot.std_date_time_format) + ' UTC', timestamp=datetime.utcnow(), color=self.bot.fake_colorless)
        embed.set_footer(text='last modified your local time')
        embed.set_author(**self.bot.special_authors.get('bot_author'))
        log.debug('Updating Team Roster last modified message')
        await self.last_changed_message.edit(embed=embed)

    async def create_last_changed_message(self, channel: discord.TextChannel):
        embed = discord.Embed(title='Last Modified', description=datetime.utcnow().strftime(self.bot.std_date_time_format) + ' UTC', timestamp=datetime.utcnow(), color=self.bot.fake_colorless)
        embed.set_footer(text='last modified your local time')
        embed.set_author(**self.bot.special_authors.get('bot_author'))
        self.last_changed_message = await channel.send(embed=embed)

    async def _load_team_items(self):
        if os.path.isfile(self.team_item_data_file) is False:
            writejson({"team_items": [], "last_changed_message": None}, self.team_item_data_file)
        self.team_items = []
        for item in loadjson(self.team_item_data_file).get('team_items'):
            self.team_items.append(await TeamItem.from_dict(item))
        last_changed_data = loadjson(self.team_item_data_file).get('last_changed_message')
        if last_changed_data is not None:
            last_changed_channel = self.bot.channel_from_id(last_changed_data.get('channel_id'))
            self.last_changed_message = await last_changed_channel.fetch_message(last_changed_data.get('message_id'))

    async def _save_team_items(self):
        data = {"team_items": [item.to_dict() for item in self.team_items],
                'last_changed_message': {'channel_id': self.last_changed_message.channel.id,
                                         'message_id': self.last_changed_message.id}}
        writejson(data, self.team_item_data_file)

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

    # def cog_unload(self):
    #     log.debug("Cog '%s' UNLOADED!", str(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(TeamRosterCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
