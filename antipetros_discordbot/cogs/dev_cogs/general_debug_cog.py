

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import random
from time import time
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
import asyncio
from textwrap import dedent
from dotenv import load_dotenv
from datetime import datetime
import shutil
from zipfile import ZipFile, ZIP_LZMA
from tempfile import TemporaryDirectory
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import commands
from emoji import demojize
from webdav3.client import Client
from icecream import ic
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from dateparser import parse as date_parse
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import async_seconds_to_pretty_normal, make_config_name, generate_bot_data, dict_from_attached_json, antipetros_repo_rel_path
from antipetros_discordbot.utility.checks import log_invoker, allowed_channel_and_allowed_role_2, command_enabled_checker, allowed_requester, only_giddi, has_attachments
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.gidtools_functions import bytes2human, pathmaker, writejson, loadjson, writeit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import CogState
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.emoji_handling import create_emoji_custom_name, normalize_emoji
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.nextcloud import get_nextcloud_options
from antipetros_discordbot.utility.data_gathering import gather_data
from antipetros_discordbot.utility.exceptions import NotAllowedChannelError
from pyyoutube import Api
from inspect import getmembers, getsourcefile, getsource, getsourcelines, getfullargspec, getmodule, getcallargs, getabsfile, getmodulename, getdoc, getfile, cleandoc, classify_class_attrs

from antipetros_discordbot.utility.sqldata_storager import AioMetaDataStorageSQLite
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

COG_NAME = "GeneralDebugCog"
CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion [Constants]

# region [TODO]

# TODO: create regions for this file
# TODO: Document and Docstrings


# endregion [TODO]


class GeneralDebugCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Cog for debug or test commands, should not be enabled fo normal Bot operations.
    """
    config_name = CONFIG_NAME
    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.WORKING | CogState.OPEN_TODOS | CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING | CogState.DOCUMENTATION_MISSING | CogState.FOR_DEBUG,
                             "2021-02-06 05:26:32",
                             "a296317ad6ce67b66c11e18769b28ef24060e5dac5a0b61a9b00653ffbbd9f4e521b2481189f075d029a4e9745892052413d2364e0666a97d9ffc7561a022b07")}
    required_config_data = dedent("""
                                  """)

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support

        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
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
        self.meta_db = AioMetaDataStorageSQLite()
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

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))

    @commands.Cog.listener(name="on_raw_reaction_add")
    async def emoji_tester(self, payload):
        disable = True

        if disable is True:
            return
        emoji = payload.emoji

        if emoji.is_custom_emoji():
            log.debug("custom emoji as str(): '%s'", str(emoji))
            log.debug("custom emoji id: '%s'", emoji.id)
            log.debug("custom emoji name: '%s'", emoji.name)
            log.debug("custom emoji demojized: '%s'", demojize(str(emoji)))
            log.debug("custom emoji hash: '%s'", hash(emoji))
            log.debug("custom emoji normalized: '%s'", normalize_emoji(emoji.name))
        elif emoji.is_unicode_emoji():
            log.debug("unicode emoji as str(): '%s'", str(emoji))
            log.debug("unicode emoji id: '%s'", emoji.id)
            log.debug("unicode emoji name: '%s'", emoji.name)
            log.debug("unicode emoji demojized: '%s'", demojize(emoji.name))
            log.debug("unicode emoji hash: '%s'", hash(emoji))
            log.debug("unicode emoji customized name: '%s'", create_emoji_custom_name(str(emoji)))
            log.debug("unicode emoji normalized: '%s'", normalize_emoji(emoji.name))

    @auto_meta_info_command(enabled=get_command_enabled('roll'))
    async def roll_blocking(self, ctx, target_time: int = 1):
        start_time = time()
        time_multiplier = 151267
        random_stats_funcs = [("mean", mean),
                              ("median", median),
                              ("stdev", stdev),
                              ("variance", variance),
                              ("mode", mode),
                              ("harmonic_mean", harmonic_mean),
                              ("median_grouped", median_grouped),
                              ("pvariance", pvariance),
                              ('amount', len),
                              ('sum', sum)]
        roll_data = [random.randint(1, 10) for _ in range(target_time * time_multiplier)]

        stats_data = {}
        log.debug("starting calculating statistics")
        for key, func in random_stats_funcs:
            stats_data[key] = round(func(roll_data), ndigits=2)
            log.debug('finished calculating "%s"', key)
        time_taken_seconds = int(round(time() - start_time))
        time_taken = await async_seconds_to_pretty_normal(time_taken_seconds) if time_taken_seconds != 0 else "less than 1 second"
        await ctx.send(embed=await make_basic_embed(title='Roll Result', text='this is a long blocking command for debug purposes', symbol='debug_2', duration=time_taken, ** stats_data))

    @auto_meta_info_command()
    async def request_server_restart(self, ctx):

        if ctx.prefix != "<@&800769712879042612> ":

            return

        servers = ["COMMUNITY_SERVER_1", "TEST_SERVER_1", "TEST_SERVER_2"]
        await ctx.send(f"please specify the server name in the next 20 seconds | OPTIONS: {', '.join(servers)}")
        user = ctx.author
        channel = ctx.channel

        def check(m):
            return m.author.name == user.name and m.channel.name == channel.name
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=20.0)
            if any(server.casefold() in msg.content.casefold() for server in servers):
                for server in servers:
                    if server.casefold() in msg.content.casefold():
                        _server = server
            else:
                await ctx.send('No valid answer received, aborting request, you can always try again')
                return
            await ctx.send("Did the commander save and is everyone ready for a restart? answer time: 20 seconds | OPTIONS: YES, NO")
            try:
                msg_2 = await self.bot.wait_for('message', check=check, timeout=20.0)
                if msg_2.content.casefold() == 'yes':
                    is_saved = 'yes'
                elif msg_2.content.casefold() == 'no':
                    is_saved = 'no'
                else:
                    await ctx.send('No valid answer received, aborting request, you can always try again')
                    return
                await ctx.send("notifying admin now")
                member = await self.bot.retrieve_antistasi_member(576522029470056450)
                await member.send(f"This is a notification from {ctx.author.name}!\nHe requests a server restart for server {_server}, saved and ready: {is_saved}")
                await ctx.send(f"I have notified {member.name} per DM!")
            except asyncio.TimeoutError:
                await ctx.send('No answer received, aborting request, you can always try again')
                return

        except asyncio.TimeoutError:
            await ctx.send('No answer received, aborting request, you can always try again')
            return

    @auto_meta_info_command()
    async def save_embed(self, ctx, message: discord.Message):
        if len(message.embeds) == 0:
            await ctx.send("the message has no embed, aborting")
            return

        embed = message.embeds[0]
        embed_dict = embed.to_dict()
        writejson(embed_dict, pathmaker(APPDATA["saved_embeds"], f"{message.id}.json"))
        await ctx.send(f'saved embed from message {message.id}')

    async def _get_unique_save_message_path(self, name: str, in_format: str, in_round: int = 0):
        if in_round == 0:
            full_name = f"{name}.{in_format}"
        else:
            full_name = f"{name}_{in_round}.{in_format}"
        path = pathmaker(APPDATA['temp_files'], full_name)
        if os.path.isfile(path) is True:
            return await self._get_unique_save_message_path(name=name, in_format=in_format, in_round=in_round + 1)
        return path

    @auto_meta_info_command()
    async def save_message(self, ctx: commands.context, channel_id: int, message_id: int, file_format: str = 'md'):
        channel = await self.bot.channel_from_id(channel_id)
        message = await channel.fetch_message(message_id)
        path = await self._get_unique_save_message_path('saved_message', file_format)
        content = message.content
        writeit(path, content)
        await ctx.send(f'message saved as `{os.path.basename(path)}`', delete_after=60)

    @auto_meta_info_command()
    async def quick_latency(self, ctx):
        await ctx.send(f"{round(self.bot.latency * 1000)} ms")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name

    @auto_meta_info_command()
    async def pin_multiple_messages(self, ctx: commands.Context, reason: str, *messages: discord.Message):
        if ctx.channel.name.casefold() not in ['bot-testing', 'bot-development']:
            await ctx.reply(f"Command only usable in {', '.join(['bot-testing', 'bot-development'])}", delete_after=30)
            await ctx.message.delete()
            return

        log.debug(f"Reason for pinning message: {reason=}")
        for message in messages:
            await message.pin(reason=reason)
        await ctx.message.delete()

    @auto_meta_info_command(aliases=['pin'])
    async def pin_message(self, ctx: commands.Context, *, reason: str):
        if ctx.channel.name.casefold() not in ['bot-testing', 'bot-development']:
            await ctx.reply(f"Command only usable in {', '.join(['bot-testing', 'bot-development'])}", delete_after=30)
            await ctx.message.delete()
            return
        if ctx.message.reference.resolved is None:
            await ctx.send('you need to reply to a message, that should be pinned, aborting!', delete_after=30)
            await ctx.message.delete()
            return
        message = ctx.message.reference.resolved
        log.debug(f"Reason for pinning message: {reason=}")
        await message.pin(reason=reason)
        await ctx.message.delete()

    @auto_meta_info_command(enabled=True)
    @has_attachments(1)
    @log_invoker(log, 'info')
    async def make_embed(self, ctx: commands.Context):
        attachment = ctx.message.attachments[0]
        embed_dict = await dict_from_attached_json(attachment)
        print(embed_dict.get('embed'))
        embed = discord.Embed.from_dict(embed_dict.get('embed'))
        print(embed)
        await ctx.send(embed=embed)

    @auto_meta_info_command(aliases=['unpin'])
    async def unpin_message(self, ctx: commands.Context, *, reason: str):
        if ctx.channel.name.casefold() not in ['bot-testing', 'bot-development']:
            return
        if ctx.message.reference.resolved is None:
            await ctx.send('you need to reply to a message, that should be pinned, aborting!')
            return
        message = ctx.message.reference.resolved
        log.debug(f"{reason=}")
        await message.unpin(reason=reason)
        await ctx.send(f'UNpinned message {message.id}', delete_after=60)
        await ctx.message.delete()

    async def _apply_overwrites(self, channel: discord.TextChannel, permissions: dict, selector: discord.Role):
        for name, value in channel.overwrites_for(selector):
            if value is not None:
                permissions[name] = value
        return permissions

    @auto_meta_info_command()
    async def all_channel_permissions(self, ctx: commands.Context, member: discord.Member = None, display_mode: str = 'only_true', filter_category: str = None):
        json_path = f"{member.display_name}_permissions.json"
        writejson({}, json_path)
        for channel in self.bot.antistasi_guild.channels:
            if filter_category is None:
                if channel.category is not None and channel.category.name not in ["Voice Channels"]:
                    await self.check_bot_channel_permissions(ctx, channel, member, display_mode, json_path)
                    await asyncio.sleep(5)
            else:
                if channel.category is not None and channel.category.name.casefold() == filter_category.casefold():
                    await self.check_bot_channel_permissions(ctx, channel, member, display_mode)
                    await asyncio.sleep(5)

    @auto_meta_info_command(aliases=['channel_permissions'])
    async def check_bot_channel_permissions(self, ctx: commands.Context, channel: discord.TextChannel = None, member: discord.Member = None, display_mode: str = 'only_true', json_file=None):
        channel = ctx.channel if channel is None else channel
        member = self.bot.bot_member if member is None else member
        roles = member.roles
        role_names = ', '.join(map(lambda x: x.name, roles))
        role_ids = ', '.join(map(lambda x: str(x.id), roles))
        y = roles.pop(0)

        permissions = {}
        for name, value in channel.permissions_for(member):
            permissions[name] = value
        for selector in roles:

            permissions = await self._apply_overwrites(channel=channel, permissions=permissions, selector=selector)
            if json_file is not None:
                json_data = loadjson(json_file)
                json_data[channel.name] = permissions
                writejson(json_data, json_file)
        if display_mode.casefold() == 'only_true':
            description = '```ini\n' + f'\n{"-"*35}\n'.join(f"{permission_name} = {' '*(25-len(permission_name))} {permission_bool}" for permission_name, permission_bool in permissions.items() if permission_bool is True) + '\n```'
        elif display_mode.casefold() == 'all':
            permission_list = [f"{'+' if permission_bool is True else '-'} {permission_name} = {' '*(25-len(permission_name))} {permission_bool}" for permission_name, permission_bool in permissions.items()]
            description = '```diff\n' + '\n'.join(sorted(permission_list, key=lambda x: x.endswith('True'), reverse=True)) + '\n```'
        elif display_mode.casefold() == 'only_false':
            description = '```ini\n' + f'\n{"-"*35}\n'.join(f"{permission_name} = {' '*(25-len(permission_name))} {permission_bool}" for permission_name, permission_bool in permissions.items() if permission_bool is False) + '\n```'
        else:
            raise AttributeError(f'no such displaymode - "{display_mode}"')
        embed_data = await self.bot.make_generic_embed(title=f'Permissions for **__{member.name}__** in **__{channel.name.upper()}__**', description=description, thumbnail=None, footer='not_set')
        await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none(), delete_after=300)

    @ commands.command()
    async def check_embed_gif(self, ctx: commands.Context):
        embed_data = await self.bot.make_generic_embed(title="check embed gif", image=APPDATA['COMMAND_the_dragon.gif'])
        await ctx.send(**embed_data)

    @ commands.command()
    async def get_prefixes(self, ctx: commands.Context):
        prefixes = await self.bot.get_prefix(ctx.message)
        prefixes = list(set([prefix.strip() for prefix in prefixes]))
        await ctx.send(str(prefixes))

    # @ commands.command()
    # @ commands.is_owner()
    # async def send_the_configs(self, ctx: commands.Context):
    #     data = loadjson(APPDATA['Admin Lead_members.json'])
    #     for item in data:
    #         admin_lead_member = await self.bot.retrieve_antistasi_member(item.get('id'))
    #         cogs_config_file = discord.File(APPDATA['cogs_config.ini'])
    #         base_config_file = discord.File(APPDATA['base_config.ini'])
    #         await admin_lead_member.send('**From Giddi**:\nAttached are the bot configs, they are commented as best I can right now, but I am always available for questions. You can change them directly and send them back to me(giddi).\n\n*I use the bot to send this message to not have to write it 3 times*', files=[base_config_file, cogs_config_file])

    @ commands.command(aliases=['clr-scrn'])
    async def the_bots_new_clothes(self, ctx: commands.Context):
        msg = ZERO_WIDTH * 20 + '\n'
        await ctx.send('THE BOTS NEW CLOTHES' + (msg * 60))

        await ctx.message.delete()

    async def get_save_path(self, save_folder, name, in_round=0):
        if in_round == 0:
            path = pathmaker(save_folder, name)
        else:
            path = pathmaker(save_folder, f"{name.split('.')[0]}_{in_round}.{name.split('.')[-1]}")
        if os.path.exists(path) is False:
            return path
        return await self.get_save_path(save_folder, name, in_round + 1)

    @ auto_meta_info_command()
    async def get_all_attachments(self, ctx: commands.Context, channel: discord.TextChannel, amount_to_scan: int = None):
        if ctx.author.id not in [152532555600494593, 576522029470056450, 346595708180103170]:
            return
        to_large = False
        delete_after = 300
        wanted_extensions = ['jpg', 'png', 'svg', 'jpeg', 'psd', 'xcf']
        msg = f'...try to collect all images from `{channel.name}`'
        if amount_to_scan is not None:
            msg += f' in the last `{amount_to_scan}` messages'
        await ctx.send(msg, delete_after=delete_after)
        save_folder = pathmaker(APPDATA['temp_files'], f"attachments_from_channel_{channel.name.replace(' ','_').lower()}")
        if os.path.exists(save_folder) is False:
            os.makedirs(save_folder)
        await ctx.send(f'...scraping all attachments from `{channel.name}`', delete_after=delete_after)
        async for message in channel.history(limit=amount_to_scan):
            if len(message.attachments) != 0:
                for attachment in message.attachments:
                    # if any(attachment.filename.casefold().endswith('.' + wanted_ext.casefold()) for wanted_ext in wanted_extensions):
                    save_path = await self.get_save_path(save_folder, attachment.filename)
                    log.debug('SAVING image "%s"', os.path.basename(save_path))
                    with open(save_path, 'wb') as f:
                        await attachment.save(f)
        await ctx.send(f"...I have collected `{len(os.listdir(save_folder))}` attachments from `{channel.name}`", delete_after=delete_after)
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
        zip_path = await self.get_save_path(APPDATA['temp_files'], f"attachments_from_channel_{channel.name.replace(' ','_').lower()}_{timestamp}.zip")
        await ctx.send('...compressing collected attachments', delete_after=delete_after)
        with ZipFile(zip_path, 'w', compression=ZIP_LZMA) as zippy:
            for file_item in os.scandir(save_folder):
                if file_item.is_file():
                    log.debug('COMPRESSING image "%s"', file_item.name)
                    zippy.write(file_item.path, file_item.name)
                    await asyncio.sleep(0)
        await ctx.send(f"...zip file has a size of `{bytes2human(os.stat(zip_path).st_size,annotate=True)}`", delete_after=delete_after)

        client = Client(get_nextcloud_options())
        await ctx.send("...Starting upload to Dev-Drive", delete_after=delete_after)
        async with ctx.typing():
            await self.bot.execute_in_thread(client.upload_sync, f"collected_attachments_discord/{os.path.basename(zip_path)}", zip_path)
            await ctx.send(f"...uploaded to Dev-drive as `collected_attachments_discord/{os.path.basename(zip_path)}`", delete_after=delete_after)

        log.debug("cleaning up '%s'", zip_path)
        os.remove(zip_path)
        log.debug('cleaning up "%s"', save_folder)
        shutil.rmtree(save_folder)
        if os.path.isdir(save_folder) is True:
            os.remove(save_folder)

    @ auto_meta_info_command(enabled=True)
    async def write_data(self, ctx):
        await gather_data(self.bot)
        await ctx.send(embed=await make_basic_embed(title='Data Collected', text='Data was gathered and written to the assigned files', symbol='save', collected_data='This command only collected fixed data like role_ids, channel_ids,...\n', reason='Data is collected and saved to a json file so to not relying on getting it at runtime, as this kind of data is unchanging', if_it_changes='then this command can just be run again'))

    @ auto_meta_info_command(enabled=True)
    async def show_command_names(self, ctx):

        _out = []

        for cog_name, cog_object in self.bot.cogs.items():
            for command in cog_object.get_commands():
                _out.append('__**' + str(command.name) + '**__' + ': ```\n' + str(command.help).split('\n')[0] + '\n```')
        await self.bot.split_to_messages(ctx, '\n---\n'.join(_out), split_on='\n---\n')

    @ auto_meta_info_command(enabled=True)
    async def mention_nomas(self, ctx):
        nomas_member = await self.bot.retrieve_antistasi_member(320739533417218048)
        mention_string = nomas_member.mention
        await ctx.send(f"Something {mention_string}", allowed_mentions=discord.AllowedMentions.none())

    @ auto_meta_info_command(enabled=True)
    async def check_reload_mech(self, ctx):
        await self.bot.reload_cog_from_command_name("flip_coin")

    @auto_meta_info_command(enabled=True)
    async def create_role_by_name_and_assign_to_all(self, ctx: commands.context, role_name: str, *, reason: str):
        role = await self.bot.antistasi_guild.create_role(name=role_name, permissions=discord.Permissions.none(), color=self.bot.get_discord_color('pink'), hoist=False, mentionable=False, reason=reason)
        await ctx.send(f"Created role {role.mention}, now applying to all", allowed_mentions=discord.AllowedMentions.none())
        for member in self.antistasi_guild.members:
            await member.add_roles(role)
            await asyncio.sleep(3)
        await ctx.reply('Adding of roles completed!')

    @auto_meta_info_command()
    async def mock_subscribe_thing(self, ctx: commands.Context, *topics: str):
        emojis = ["1️⃣", "2️⃣", "3️⃣"]
        fields = []
        for index, topic in enumerate(topics):
            role = '$mock_role_' + topic + '_subscriber'
            field = self.bot.field_item(name=topic, value=f"react with {emojis[index]} to subscribe to the Topic `{topic}`, you will get the role {role}")
            fields.append(field)

        embed_data = await self.bot.make_generic_embed(title='Topic Subscription', description=f"\@mock_everybody to get notified for a topic react to this message.\navailable topics:", fields=fields, footer={'text': 'to unsubscribe just take your reaction away from this message'})

        msg = await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        for i in range(len(topics)):
            await msg.add_reaction(emojis[i])

    @auto_meta_info_command(enabled=True)
    async def dump_permissions(self, ctx: commands.Context):
        async with ctx.typing():
            for bot_member in [self.antidevtros_member, self.antipetros_member]:
                permission_dict = {}
                for channel in self.bot.antistasi_guild.channels:
                    if channel.type is discord.ChannelType.text:
                        permission_dict[channel.name] = {name: value for name, value in channel.permissions_for(bot_member)}
                writejson(permission_dict, f"{bot_member.display_name.casefold()}_permission_dump.json")
                await ctx.send(f"dumped permissions for {bot_member.display_name}")
            await ctx.send(f"finished dumping permission for Giddis Bots")

    @auto_meta_info_command()
    async def check_not_allowed_channel(self, ctx):
        raise NotAllowedChannelError(ctx, ['dev-thrash'])

    @auto_meta_info_command()
    async def get_antistasi_youtube_videos(self, ctx):
        base_youtube_watch_url = "https://www.youtube.com/watch?v="
        api = Api(api_key=os.getenv('GOOGLE_API_KEY'))
        channel = api.get_channel_info(channel_id="UCsh0jHpXZyv3MlXvCGj_OfQ")
        uploads = channel.items[0].contentDetails.relatedPlaylists.uploads
        playlist = api.get_playlist_items(playlist_id=uploads, count=None)
        vids = []
        for item in playlist.items:
            title = item.snippet.title
            link = base_youtube_watch_url + str(item.contentDetails.videoId)
            description = item.snippet.description
            image = item.snippet.thumbnails.maxres
            if image is None:
                image = item.snippet.thumbnails.high
            if image is None:
                image = item.snippet.thumbnails.standard
            if image is None:
                image = item.snippet.thumbnails.medium
            if image is None:
                image = item.snippet.thumbnails.default
            image = image.url
            date = date_parse(item.contentDetails.videoPublishedAt)
            vids.append((title, date, link, description, image))
        vids = sorted(vids, key=lambda x: x[0], reverse=True)
        for item in vids:
            embed_data = await self.bot.make_generic_embed(title=item[0], description=item[3] + '\n\n' + item[2], image=str(item[4]), timestamp=item[1])
            await ctx.send(**embed_data)

    @auto_meta_info_command()
    @only_giddi()
    async def get_all_from_embed_user(self, ctx):
        async with ctx.typing():
            names = []
            channel = self.bot.get_channel(584070905840533516)
            async for msg in channel.history(limit=999999):
                reactions = msg.reactions
                for reaction in reactions:
                    async for user in reaction.users():
                        names.append(user.name)
            names = list(set(names))
            with TemporaryDirectory() as tempdir:
                path = pathmaker(tempdir, 'reaction_users.txt')
                with open(path, 'w') as f:
                    f.write('\n'.join(names))
                file = discord.File(path)
                await ctx.send(file=file)
            msg_names = []
            channel = self.bot.get_channel(795439678127996958)
            async for msg in channel.history(limit=999999):
                msg_names.append(msg.author.name)
            msg_names = list(set(msg_names))
            with TemporaryDirectory() as tempdir:
                path = pathmaker(tempdir, 'msg_user_event_suggestion.txt')
                with open(path, 'w') as f:
                    f.write('\n'.join(msg_names))
                file = discord.File(path)
                await ctx.send(file=file)
            msg_names = []
            channel = self.bot.get_channel(790353924640473110)
            async for msg in channel.history(limit=999999):
                msg_names.append(msg.author.name)
            msg_names = list(set(msg_names))
            with TemporaryDirectory() as tempdir:
                path = pathmaker(tempdir, 'msg_user_event_discussion.txt')
                with open(path, 'w') as f:
                    f.write('\n'.join(msg_names))
                file = discord.File(path)
                await ctx.send(file=file)

    @auto_meta_info_command()
    async def init_edit_embed_check(self, ctx: commands.Context):
        embed_data = await self.bot.make_generic_embed(title='Testing Embed Editing', description="This is the original",
                                                       fields=[self.bot.field_item(name='embed field', value='this is original'),
                                                               self.bot.field_item(name="another field", value='this is also an original')],
                                                       timestamp=datetime.strptime('1989-04-23_23-23-23', "%Y-%m-%d_%H-%M-%S"),
                                                       thumbnail="under_construction")

        self.edit_embed_message = await ctx.send(**embed_data)

    @auto_meta_info_command()
    async def change_edit_embed_check(self, ctx: commands.Context):
        if self.edit_embed_message is None:
            await ctx.send('edit_embed_message is None')
            return
        embed_data = await self.bot.make_generic_embed(title='Testing Embed Editing', description="This is the changed",
                                                       fields=[self.bot.field_item(name='embed field', value='changed this'),
                                                               self.bot.field_item(name="another field", value='this is also changed')],
                                                       timestamp=datetime.utcnow(),
                                                       thumbnail="data")
        await asyncio.sleep(10)
        await self.edit_embed_message.edit(**embed_data)

    @auto_meta_info_command()
    async def pr_log_entries(self, ctx: commands.Context):
        base_youtube_watch_url = "https://www.youtube.com/watch?v="
        api = Api(api_key=os.getenv('GOOGLE_API_KEY'))
        channel = api.get_channel_info(channel_id="UCsh0jHpXZyv3MlXvCGj_OfQ")
        uploads = channel.items[0].contentDetails.relatedPlaylists.uploads
        playlist = api.get_playlist_items(playlist_id=uploads, count=None)
        vids = []
        for item in playlist.items:
            title = item.snippet.title
            link = base_youtube_watch_url + str(item.contentDetails.videoId)
            description = item.snippet.description
            image = item.snippet.thumbnails.maxres
            if image is None:
                image = item.snippet.thumbnails.high
            if image is None:
                image = item.snippet.thumbnails.standard
            if image is None:
                image = item.snippet.thumbnails.medium
            if image is None:
                image = item.snippet.thumbnails.default
            image = image.url
            date = date_parse(item.contentDetails.videoPublishedAt)
            vids.append((title, date, link, description, image))
        vids = sorted(vids, key=lambda x: x[1], reverse=True)
        newest = vids[0]
        await ctx.send(f"""**Platform:** Youtube
**Activity:** Video
**Additional info:** New Video was posted by `here the name if written in the description`\nTitle -> {newest[0]}\nLink -> {newest[2]}""")
        await ctx.send(f"{ZERO_WIDTH}\n" * 10)
        await asyncio.sleep(5)
        embed_data = await self.bot.make_generic_embed(title='PR Log Entry',
                                                       fields=[self.bot.field_item(name="Platform", value="Youtube"),
                                                               self.bot.field_item(name="Activity", value="New Video"),
                                                               self.bot.field_item(name="Video title", value=newest[0]),
                                                               self.bot.field_item(name="Video Link", value=newest[2])],
                                                       timestamp=newest[1],
                                                       thumbnail="youtube_logo",
                                                       image=newest[4],
                                                       author={"name": "here would be the author from the description", "icon_url": "https://i.postimg.cc/QsBWC6n1/bertha.png"},
                                                       footer={'text': "the timestamp at the bottom is the timestampt the video is posted not the time this message is posted, author above would show the author of the video.\nsadly not be able to embed the video, but if I post a second message afterwards with just the video link it posts an auto embed."})

        entry_message = await ctx.send(**embed_data)
        # pr_lead_member = await self.bot.retrieve_antistasi_member(225100859674066945)

        pr_lead_member = self.bot.creator.member_object
        embed_data = await self.bot.make_generic_embed(title='NEW PR Log Entry',
                                                       description="This is to show you how it can auto notify",
                                                       fields=[self.bot.field_item(name="Platform", value="Youtube"),
                                                               self.bot.field_item(name="Activity", value="New Video"),
                                                               self.bot.field_item(name="link to entry", value=entry_message.jump_url)],
                                                       timestamp=newest[1],
                                                       thumbnail="youtube_logo",
                                                       author={"name": "here would be the author from the description", "icon_url": "https://i.postimg.cc/QsBWC6n1/bertha.png"},
                                                       footer={'text': "the timestamp at the bottom is the timestampt the video is posted not the time this message is posted, author above would show the author of the video.\nsadly not be able to embed the video, but if I post a second message afterwards with just the video link it posts an auto embed."})

        await pr_lead_member.send(**embed_data)

    @auto_meta_info_command()
    async def post_role_call(self, ctx: commands.Context):
        role_description = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."""

        role_join_description = """Liber nusquam insolens has ei, appetere accusamus intellegam id ius. Vivendum intellegat et qui, ei denique consequuntur vix."""

        role_data = {}
        await ctx.send(f'{ZERO_WIDTH}\n__**Team Roster**__\n\n{ZERO_WIDTH}')
        for role in await self.bot.antistasi_guild.fetch_roles():
            if role.name.casefold() not in ['@everyone', 'member', 'trial members', 'server sponsors', 'nitro booster', 'giveawaybot', 'dyno', 'bots', 'old timer', 'steamworkshopalerts', 'call', 'muted', 'raid-helper', 'dcall', 'antidevtros'] and not role.name.casefold().endswith(' lead') and not role.name.casefold().endswith(' helper'):
                role_data[role] = {"position": role.position, 'members': [], 'lead_role': None, "helper_role": None, 'description': role_description, 'how_to_join': role_join_description}
                for member in role.members:
                    role_data[role]['members'].append(member)
                lead_role = await self.bot.role_from_string(role.name + ' Lead')
                if lead_role:
                    role_data[role]['lead_role'][lead_role] = list(member for member in lead_role.members)
                helper_role = await self.bot.role_from_string(role.name.replace(' Team', ' Helper'))
                if helper_role:
                    role_data[role]['helper_role'][helper_role] = list(member for member in helper_role.members)

        role_data = {key: value for key, value in sorted(role_data.items(), key=lambda x: x[1].get('position'), reverse=True)}
        for role, data in role_data.items():
            await ctx.send(f"{role.mention}\n" + "═" * len(role.mention) + f"\n**What do they do:**\n```fix\n{data.get('description').strip()}\n```\n**How to join:**\n```fix\n{data.get('how_to_join')}\n```\n{ZERO_WIDTH}", allowed_mentions=discord.AllowedMentions.none())
            if data.get('members'):
                await ctx.send('\n\n' + '\n'.join(f"{member.mention} {member.display_name}" for member in data.get('members')), allowed_mentions=discord.AllowedMentions.none())
            for sub_role, sub_members in data.get('sub_roles').items():
                await ctx.send('\n' + '⋱' * len(sub_role.mention) + f'\n{sub_role.mention}\n\n' + '\n'.join(f"{member.mention} {member.display_name}" for member in sub_members), allowed_mentions=discord.AllowedMentions.none())

            await ctx.send(f'{ZERO_WIDTH}\n' + '░' * 20 + f'\n\n{ZERO_WIDTH}')

    @auto_meta_info_command()
    async def get_roles(self, ctx: commands.Context):
        _out = {}
        for role in self.bot.antistasi_guild.roles:
            _out[role.name] = {'position': role.position, 'id': role.id, 'mentionable': role.mentionable}

        writejson(_out, 'all_roles.json')

    @auto_meta_info_command()
    async def check_message_mention(self, ctx: commands.Context, message: discord.Message):
        embed_data = await self.bot.make_generic_embed(title='This is a test', description=embed_hyperlink('test', message.jump_url))
        await ctx.send(**embed_data)

    @auto_meta_info_command()
    async def get_cog_info(self, ctx: commands.Context, cog_name: str):
        cog = await self.bot.cog_by_name(cog_name)
        await ctx.send('\n'.join(command.name for command in cog.get_commands()))

        await ctx.send(await antipetros_repo_rel_path(getsourcefile(cog.__class__)))
        command = [command for command in self.bot.commands if command.cog is cog][0]
        await ctx.send(command.name)
        await ctx.send("```py\n" + getsource(command.callback) + "\n```")
        await ctx.send(cleandoc(getdoc(cog)))

    @auto_meta_info_command()
    async def dump_to_meta_db(self, ctx: commands.Context):
        await self.meta_db.insert_cogs(self.bot)
        await ctx.send('done')

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))

    async def cog_check(self, ctx):
        if ctx.author.id == self.bot.creator.id:
            return True
        return False


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(GeneralDebugCog(bot)))
