

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import random
from time import time
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
import asyncio
from pprint import pprint, pformat
from dotenv import load_dotenv
from datetime import datetime
import shutil
from zipfile import ZipFile, ZIP_LZMA
from tempfile import TemporaryDirectory

# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import commands, flags, tasks
from emoji import demojize, emojize, emoji_count
from emoji.unicode_codes import EMOJI_UNICODE_ENGLISH
from webdav3.client import Client
from icecream import ic
from typing import TYPE_CHECKING
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from dateparser import parse as date_parse
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import antipetros_repo_rel_path, async_seconds_to_pretty_normal, generate_bot_data
from antipetros_discordbot.utility.checks import has_attachments, only_giddi
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.gidtools_functions import bytes2human, pathmaker, writejson, loadjson, writeit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, AntiPetrosBaseGroup, CommandCategory, auto_meta_info_command
from antipetros_discordbot.utility.emoji_handling import create_emoji_custom_name, normalize_emoji
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.nextcloud import get_nextcloud_options
from antipetros_discordbot.utility.data_gathering import gather_data
from antipetros_discordbot.utility.exceptions import NotAllowedChannelError
from antipetros_discordbot.utility.converters import CogConverter, CommandConverter
from pyyoutube import Api
from inspect import cleandoc, getdoc, getmembers, getsource, getsourcefile
from antipetros_discordbot.utility.sqldata_storager import general_db
from marshmallow import Schema, fields
from rich import inspect as rinspect
from antipetros_discordbot.engine.replacements.helper.help_embed_builder import HelpEmbedBuilder
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
# endregion [Imports]

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


# endregion [Constants]

# region [TODO]

# TODO: create regions for this file
# TODO: Document and Docstrings


# endregion [TODO]

class RoleSchema(Schema):
    color = fields.Function(lambda obj: (obj.color.r, obj.color.g, obj.color.b))
    created_at = fields.Function(lambda obj: obj.created_at.isoformat(timespec='seconds'))
    tags = fields.Function(lambda obj: {'is_bot_managed': obj.tags.is_bot_managed(), 'is_integration': obj.tags.is_integration(), 'is_premium_subscriber': obj.tags.is_premium_subscriber()} if obj.tags is not None else {})
    permissions = fields.Function(lambda obj: dict(obj.permissions))
    guild = fields.Function(lambda obj: obj.guild.name)
    members = fields.Function(lambda obj: [member.name + '_' + str(member.id) for member in obj.members])

    class Meta:
        additional = ('mention', 'mentionable', 'managed', 'id', 'hoist', 'name', 'position')


class GeneralDebugCog(AntiPetrosBaseCog, command_attrs={'hidden': True}):
    """
    Cog for debug or test commands, should not be enabled fo normal Bot operations.
    """

    public = False
    meta_status = CogMetaStatus.WORKING | CogMetaStatus.OPEN_TODOS | CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.NEEDS_REFRACTORING | CogMetaStatus.DOCUMENTATION_MISSING | CogMetaStatus.FOR_DEBUG

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        load_dotenv("nextcloud.env")
        self.next_cloud_options = {
            'webdav_hostname': f"https://antistasi.de/dev_drive/remote.php/dav/files/{os.getenv('NX_USERNAME')}/",
            'webdav_login': os.getenv('NX_USERNAME'),
            'webdav_password': os.getenv('NX_PASSWORD')
        }
        self.next_cloud_client = Client(self.next_cloud_options)
        self.notified_nextcloud_files = []
        self.bob_user = None
        self.antidevtros_member = None
        self.antipetros_member = None
        self.edit_embed_message = None
        self.general_db = general_db
        self.command_pop_list = []

        glog.class_init_notification(log, self)

    async def on_ready_setup(self):

        self.bob_user = await self.bot.retrieve_antistasi_member(346595708180103170)
        for member in self.bot.antistasi_guild.members:
            if member.bot is True:
                if member.display_name.casefold() == 'antidevtros':
                    self.antidevtros_member = member

                elif member.display_name.casefold() == 'antipetros':
                    self.antipetros_member = member
                else:
                    if self.antidevtros_member is not None and self.antipetros_member is not None:
                        break
        await generate_bot_data(self.bot, self.antipetros_member)
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

    @ auto_meta_info_command()
    async def check_self_dump(self, ctx: commands.Context):
        """
        check if dostring survives. here also
        """
        async with ctx.typing():
            _out = {self.bot.display_name: {}}
            for cog_name, cog_object in self.bot.cogs.items():
                log.info("Dumped %s to Json", cog_name)
                _out[self.bot.display_name][cog_name] = cog_object.dump()
            try:
                writejson(_out, 'cog_dump.json')
            except TypeError as error:
                writeit('cog_dump_errorer.txt', pformat(_out))

        await ctx.send('done')

    @auto_meta_info_command()
    async def check_categories(self, ctx: commands.Context):
        for category_name, category in CommandCategory.all_command_categories.items():

            command_string = ''
            for command in sorted(category.commands, key=lambda x: x.name):
                command_string += f'\n`{command.name}`'
                if len(command_string) >= 950:
                    command_string += '\n...'
                    break
            if not command_string:
                command_string = '[]'
            extra_role_string = '\n'.join(f"`{self.bot.sync_retrieve_antistasi_role(_id).name}`" for _id in category.extra_roles)
            if not extra_role_string:
                extra_role_string = '[]'
            allowed_roles_string = ""

            for role in sorted(map(self.bot.sync_retrieve_antistasi_role, category.allowed_roles), key=lambda x: x.name):

                try:
                    allowed_roles_string += f"\n`{role.name}`"
                except AttributeError:
                    log.critical("AttributeError with role-id '%s' and resulting role '%s'", _id, str(role))
            if not allowed_roles_string:
                allowed_roles_string = "[]"
            embed_data = await self.bot.make_generic_embed(title=category.name,
                                                           description=category.docstring,
                                                           fields=[self.bot.field_item(name='config_name', value=category.config_name),
                                                                   self.bot.field_item(name='commands', value=command_string),
                                                                   self.bot.field_item(name='allowed_roles', value=allowed_roles_string),
                                                                   self.bot.field_item(name='extra_roles', value=extra_role_string)])
            await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @ auto_meta_info_command()
    async def dump_roles(self, ctx: commands.Context):
        async with ctx.typing():
            schema = RoleSchema()
            _out = {}
            for role in self.bot.antistasi_guild.roles:
                if role is not await self.bot.retrieve_antistasi_role(449481990513754112):
                    _out[role.name] = schema.dump(role)
            _out = {key + '_' + str(value.get('id')): value for key, value in sorted(_out.items(), key=lambda x: x[1].get('position'), reverse=True)}
            writejson(_out, 'role_dump.json', sort_keys=False)
            await ctx.send('done', delete_after=90, allowed_mentions=discord.AllowedMentions.none())
            other_admin_role = await self.bot.retrieve_antistasi_role(513318914516844559)
            await self.bot.split_to_messages(ctx, pformat(schema.dump(other_admin_role)), in_codeblock=True)

    @auto_meta_info_command()
    async def check_channel_visibility_checker(self, ctx: commands.Context, member: discord.Member):
        _out = {}
        for channel in self.bot.antistasi_guild.text_channels:
            _out[channel.name] = await self._check_channel_visibility(member, channel.name)

        await ctx.send(pformat(_out), allowed_mentions=discord.AllowedMentions.none(), delete_after=120)

    async def _check_channel_visibility(self, author: discord.Member, channel_name: str):
        channel = await self.bot.channel_from_name(channel_name)
        channel_member_permissions = channel.permissions_for(author)
        if channel_member_permissions.administrator is True or channel_member_permissions.read_messages is True:
            return True
        return False

    @auto_meta_info_command()
    async def dump_command(self, ctx: commands.Context):
        command = self.bot.get_command("check_unmention_everyone")
        writejson(command.dump(), 'blah.json')
        await ctx.send('wuff')

    @auto_meta_info_command()
    async def check_embed_ping(self, ctx: commands.Context, role: discord.Role):
        embed = discord.Embed(title='Test', description=role.mention)
        await ctx.send(embed=embed)

    @auto_meta_info_command()
    async def dump_role(self, ctx: commands.Context, role: discord.Role = None):
        schema = RoleSchema()
        if role is None:
            pass

        data = schema.dump(role)
        name = 'giddis_roles.json' if role is None else role.name.replace(' ', '_') + '.json'
        writejson(data, name)
        await ctx.send('done')

    @auto_meta_info_command()
    async def embed_mention_check(self, ctx: commands.Context, member: discord.Member):

        embed_data = await self.bot.make_generic_embed(Title='Test', description=member.mention)
        await ctx.send(**embed_data)

    @auto_meta_info_command()
    async def tell_len_stored_dicts(self, ctx: commands.Context):
        text = f"{ic.format(len(self.bot.roles_dict))} ||\n{ic.format(len(self.bot.members_dict))} ||\n{ic.format(len(self.bot.channels_dict))} ||"

        await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    async def webhook_test(self, ctx: commands.Context):
        from discord import Webhook, AsyncWebhookAdapter
        from aiohttp import ClientSession
        async with ClientSession() as session:
            webhook = Webhook.from_url('https://discord.com/api/webhooks/837390112730906624/oqQ9P9irf5AGrbV6zM0zSfdnleH-L8cwX6Ou1y-3eqbA00ngzN1wkaXRU39rp_eo8PcS', adapter=AsyncWebhookAdapter(session))
            await webhook.send('hello')

    @auto_meta_info_command()
    async def send_checks(self, ctx: commands.Context, command: CommandConverter):
        await ctx.send('\n'.join(check for check in command.checks))

    @auto_meta_info_command()
    async def show_discord_version(self, ctx: commands.Context):
        from discord import version_info
        await ctx.send('discord.py v{0.major}.{0.minor}.{0.micro}-{0.releaselevel}'.format(version_info))

    @auto_meta_info_command()
    async def show_appinfo(self, ctx: commands.Context):
        from antipetros_discordbot.schemas.extra_schemas.appinfo_schema import AppInfoSchema
        appinfo = await self.bot.application_info()
        schema = AppInfoSchema()
        data = schema.dump(appinfo)
        await ctx.send(pformat(data))

    @auto_meta_info_command()
    async def check_other_guild_emoji(self, ctx: commands.Context):
        other_guild_id = 837389179025096764
        emoji_id = 839097950184931378
        other_guild = self.bot.get_guild(other_guild_id)
        test_emoji = await other_guild.fetch_emoji(emoji_id)
        await ctx.send(test_emoji)

    @ auto_meta_info_command()
    async def check_help_embed_builder(self, ctx: commands.Context, command: CommandConverter):
        async with ctx.typing():
            builder = HelpEmbedBuilder(self.bot, ctx.author, command)

            embed_data = await builder.to_embed()

            await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))

    async def cog_check(self, ctx):
        if ctx.author.id == 576522029470056450:
            return True
        return False


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(GeneralDebugCog(bot))
