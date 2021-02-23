

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import random
from time import time
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
import asyncio
from io import BytesIO
from textwrap import dedent
from typing import Optional
from dotenv import load_dotenv
import lzma
from datetime import datetime
import shutil
from zipfile import ZipFile, ZIP_LZMA
from functools import partial
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext.commands import Greedy
from discord.ext import commands, tasks
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from emoji import demojize
from webdav3.client import Client

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.misc import save_commands, color_hex_embed, async_seconds_to_pretty_normal, make_config_name
from antipetros_discordbot.utility.checks import log_invoker, allowed_channel_and_allowed_role_2, command_enabled_checker, allowed_requester, check_after_invoke
from antipetros_discordbot.utility.named_tuples import MovieQuoteItem
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, bytes2human
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import CogState
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.emoji_handling import create_emoji_custom_name, normalize_emoji
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.nextcloud import NEXTCLOUD_OPTIONS
from antipetros_discordbot.utility.data_gathering import gather_data
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
                'is_ready': (CogState.WORKING | CogState.OPEN_TODOS | CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING | CogState.DOCUMENTATION_MISSING,
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
        glog.class_init_notification(log, self)

    async def on_ready_setup(self):
        self.bob_user = await self.bot.retrieve_antistasi_member(346595708180103170)
        self.query_nextcloud_loop.start()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))

    @tasks.loop(minutes=5)
    async def query_nextcloud_loop(self):
        pass
        # base_folder = "Antistasi_Community_Logs"
        # servers = ["Testserver_2", "Testserver_1", "Testserver_3", "Eventserver", "Mainserver_1", "Mainserver_2"]
        # for server in servers:
        #     path = f"{base_folder}/{server}/Server"
        #     file_data = self.next_cloud_client.list(path, get_info=True)
        #     for file_item in file_data:

        #         if file_item.get('size') is not None and int(file_item.get("size")) > (250 * (1024**2)) and file_item.get('path') not in self.notified_nextcloud_files:
        #             await self.bob_user.send(f"Warning the file '{os.path.basename(file_item.get('path'))}' exceeded 250mb in size.\n Current Size= {bytes2human(int(file_item.get('size')), annotate=True)}, \n Server= {os.path.basename(os.path.dirname(os.path.dirname(file_item.get('path'))))}")
        #             await self.bot.creator.member_object.send(f"Warning the file '{os.path.basename(file_item.get('path'))}' exceeded 250mb in size.\n Current Size= {bytes2human(int(file_item.get('size')), annotate=True)}, \n Server= {os.path.basename(os.path.dirname(os.path.dirname(file_item.get('path'))))}")
        #             self.notified_nextcloud_files.append(file_item.get('path'))

    @commands.Cog.listener(name="on_raw_reaction_add")
    async def emoji_tester(self, payload):
        disable = False

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
    @allowed_channel_and_allowed_role_2()
    @log_invoker(log, 'debug')
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
    @allowed_channel_and_allowed_role_2()
    @commands.cooldown(1, 30, commands.BucketType.channel)
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
    @commands.is_owner()
    async def save_embed(self, ctx, message: discord.Message):
        if len(message.embeds) == 0:
            await ctx.send("the message has no embed, aborting")
            return

        embed = message.embeds[0]
        embed_dict = embed.to_dict()
        writejson(embed_dict, pathmaker(APPDATA["saved_embeds"], f"{message.id}.json"))
        await ctx.send(f'saved embed from message {message.id}')

    @auto_meta_info_command()
    @commands.is_owner()
    async def quick_latency(self, ctx):
        await ctx.send(f"{round(self.bot.latency * 1000)} ms")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name

    @auto_meta_info_command(aliases=['pin'])
    @commands.is_owner()
    async def pin_message(self, ctx: commands.Context, *, reason: str):
        if ctx.channel.name.casefold() not in ['bot-testing', 'bot-development']:
            return
        if ctx.message.reference.resolved is None:
            await ctx.send('you need to reply to a message, that should be pinned, aborting!')
            return
        message = ctx.message.reference.resolved
        log.debug(f"{reason=}")
        await message.pin(reason=reason)
        await ctx.message.delete()

    @auto_meta_info_command(aliases=['unpin'])
    @commands.is_owner()
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

    async def _apply_overwrites(self, channel: discord.TextChannel, permissions: dict, selector):
        for name, value in list(channel.overwrites_for(selector)):
            if value is not None:
                permissions[name] = value
        return permissions

    @auto_meta_info_command(aliases=['channel_permissions'])
    @commands.is_owner()
    async def check_bot_channel_permissions(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None, display_mode: Optional[str] = 'only_true'):
        channel = ctx.channel if channel is None else channel
        bot_member = self.bot.bot_member
        permissions = {}
        for name, value in channel.permissions_for(bot_member):
            permissions[name] = value
        for selector in [self.bot.bot_member] + self.bot.all_bot_roles:
            permissions = await self._apply_overwrites(channel=channel, permissions=permissions, selector=selector)
        if display_mode.casefold() == 'only_true':
            description = '```ini\n' + f'\n{"-"*35}\n'.join(f"{permission_name} = {' '*(25-len(permission_name))} {permission_bool}" for permission_name, permission_bool in permissions.items() if permission_bool is True) + '\n```'
        elif display_mode.casefold() == 'all':
            permission_list = [f"{'+' if permission_bool is True else '-'} {permission_name} = {' '*(25-len(permission_name))} {permission_bool}" for permission_name, permission_bool in permissions.items()]
            description = '```diff\n' + '\n'.join(sorted(permission_list, key=lambda x: x.endswith('True'), reverse=True)) + '\n```'
        elif display_mode.casefold() == 'only_false':
            description = '```ini\n' + f'\n{"-"*35}\n'.join(f"{permission_name} = {' '*(25-len(permission_name))} {permission_bool}" for permission_name, permission_bool in permissions.items() if permission_bool is False) + '\n```'

        embed_data = await self.bot.make_generic_embed(title=f'Permissions for **__{self.bot.display_name.upper()}__** in **__{channel.name.upper()}__**', description=description, thumbnail=None, footer='not_set')
        await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @ commands.command(aliases=get_aliases("delete_msg"))
    @ commands.is_owner()
    async def delete_msg(self, ctx, msg_id: int):

        channel = ctx.channel
        message = await channel.fetch_message(msg_id)
        await message.delete()
        await ctx.message.delete()

    @ commands.command()
    @ commands.is_owner()
    async def check_embed_gif(self, ctx: commands.Context):
        embed_data = await self.bot.make_generic_embed(title="check embed gif", image=APPDATA['COMMAND_the_dragon.gif'])
        await ctx.send(**embed_data)

    @ commands.command()
    @ commands.is_owner()
    async def get_prefixes(self, ctx: commands.Context, message: discord.Message):
        prefixes = await self.bot.get_prefix(message)
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

    @ commands.command()
    @ commands.is_owner()
    async def the_bots_new_clothes(self, ctx: commands.Context):
        msg = ZERO_WIDTH * 20 + '\n'
        await ctx.send('```python\nTHE BOTS NEW CLOTHES:\n' + (msg * 40) + '\n```')
        await ctx.send(msg * 60)
        await ctx.message.delete()

    @commands.after_invoke(check_after_invoke)
    @auto_meta_info_command()
    @ commands.is_owner()
    async def check_a_hook(self, ctx: commands.Context):
        await asyncio.sleep(5)
        await ctx.send("this is inside the command")
        await asyncio.sleep(5)

    async def get_save_path(self, save_folder, name, in_round=0):
        if in_round == 0:
            path = pathmaker(save_folder, name)
        else:
            path = pathmaker(save_folder, f"{name.split('.')[0]}_{in_round}.{name.split('.')[-1]}")
        if os.path.exists(path) is False:
            return path
        return await self.get_save_path(save_folder, name, in_round + 1)

    @commands.after_invoke(check_after_invoke)
    @auto_meta_info_command()
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

        client = Client(NEXTCLOUD_OPTIONS)
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
    @ commands.is_owner()
    async def write_data(self, ctx):
        await gather_data(self.bot)
        await ctx.send(embed=await make_basic_embed(title='Data Collected', text='Data was gathered and written to the assigned files', symbol='save', collected_data='This command only collected fixed data like role_ids, channel_ids,...\n', reason='Data is collected and saved to a json file so to not relying on getting it at runtime, as this kind of data is unchanging', if_it_changes='then this command can just be run again'))

    @ auto_meta_info_command(enabled=True)
    @ commands.is_owner()
    async def show_command_names(self, ctx):

        _out = []

        for cog_name, cog_object in self.bot.cogs.items():
            for command in cog_object.get_commands():
                _out.append('__**' + str(command.name) + '**__' + ': ```\n' + str(command.help).split('\n')[0] + '\n```')
        await self.bot.split_to_messages(ctx, '\n---\n'.join(_out), split_on='\n---\n')


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(GeneralDebugCog(bot)))
