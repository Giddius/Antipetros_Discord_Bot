"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import re
import random
from textwrap import shorten
from datetime import datetime, timezone
import random
from typing import TYPE_CHECKING, Union
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import commands
import arrow
from humanize import naturaltime
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
import asyncio
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, pickleit, writejson
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import UpdateTypus
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
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
    shutdown_message_pickle_file = pathmaker(APPDATA['misc'], 'last_shutdown_message.pkl')
    goodbye_quotes_file = APPDATA['goodbye_quotes.json']

    def __init__(self, bot: "AntiPetrosBot", support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.shutdown_message_pickle = None

        glog.class_init_notification(log, self)

    async def reload_cog_from_command_name(self, command: Union[str, commands.Command]):
        if isinstance(command, str):
            command = self.bot.commands_map.get(command)

        self.bot.reload_extension(command.module.__name__)

    @ property
    def shutdown_command(self):
        return self.bot.get_command('shutdown')

    def refresh_command(self, command: commands.Command):
        self.bot.remove_command(command.name)
        self.bot.add_command(command)

    async def message_creator(self, message=None, embed=None, file=None):
        if message is None and embed is None:
            message = 'message has no content'
        await self.bot.creator.send(content=message, embed=embed, file=file)

    async def not_implemented(self, ctx: commands.Context):
        embed_data = await self.bot.make_generic_embed(title='NOT IMPLEMENTED',
                                                       description='Sorry but the command is a Placeholder and is not yet implemented',
                                                       author='bot_author',
                                                       footer='feature_request_footer',
                                                       thumbnail="under_construction")
        await ctx.send(**embed_data)

    @property
    def shutdown_message_channel(self):
        channel_name = BASE_CONFIG.retrieve("shutdown_message", "channel_name", typus=str, direct_fallback='bot-testing')
        return self.bot.channel_from_name(channel_name)

    def shutdown_signal(self, *args):
        asyncio.create_task(self.shutdown_mechanic())

    async def shutdown_mechanic(self):
        if BASE_CONFIG.retrieve("shutdown_message", "enable_shutdown_message", typus=bool, direct_fallback=False) is True:
            try:
                started_at = self.support.start_time

                started_at_string = arrow.get(started_at).format('YYYY-MM-DD HH:mm:ss')
                online_duration = naturaltime(datetime.now(timezone.utc) - started_at).replace(' ago', '')

                embed = await self.bot.make_generic_embed(title=random.choice(loadjson(self.goodbye_quotes_file)),
                                                          description=f'{self.bot.display_name} is shutting down.',
                                                          image=BASE_CONFIG.retrieve('shutdown_message', 'image', typus=str, direct_fallback="https://i.ytimg.com/vi/YATREe6dths/maxresdefault.jpg"),
                                                          type=self.support.embed_types_enum.Image,
                                                          thumbnail="red_chain",
                                                          typus="shutdown_embed",
                                                          fields=[self.support.field_item(name='Online since', value=str(started_at_string), inline=False), self.support.field_item(name='Online for', value=str(online_duration), inline=False)])
                channel = self.shutdown_message_channel
                log.info("sending shutdown message")
                last_shutdown_message = await channel.send(**embed)
                pickleit({"message_id": last_shutdown_message.id, "channel_id": last_shutdown_message.channel.id}, self.shutdown_message_pickle_file)

            except Exception as error:
                log.error(error, exc_info=True)

        await self.bot.close()

    async def split_to_messages(self, target: discord.abc.Messageable, message, split_on='\n', in_codeblock=False, syntax_highlighting='json'):
        _out = ''
        chunks = message.split(split_on)
        for chunk in chunks:
            if sum(map(len, _out)) + len(chunk + split_on) < self.bot.max_message_length:
                _out += chunk + split_on
            else:
                if in_codeblock is True:
                    _out = f"```{syntax_highlighting}\n{_out}\n```"
                await asyncio.sleep(1)
                await target.send(_out)

                _out = ''
        if in_codeblock is True:
            _out = f"```{syntax_highlighting}\n{_out}\n```"
        await asyncio.sleep(1)
        await target.send(_out)

    async def process_meta_data(self):
        docstring_regex = re.compile(r"(?P<description>.*?)(?P<args>args\:.*?(?=example\:)?)?(?P<example>example\:.*?)?(?P<extra_info>info\:.*)?$", re.IGNORECASE | re.DOTALL)
        file_path = APPDATA['command_meta_data.json']
        data = loadjson(file_path)
        _new_dict = {}
        for command_name, command_attrs in data.items():
            new_attrs = {'docstring': None,
                         'example': None,
                         'long_description': None,
                         'brief': None,
                         'extra_info': None,
                         'description': None,
                         'short_doc': None} | command_attrs

            if new_attrs.get('docstring'):
                docstring = new_attrs.get('docstring')
                docstring_match = docstring_regex.search(docstring)
                if docstring_match:
                    if not new_attrs.get('description') and docstring_match.group('description'):
                        new_attrs['description'] = await asyncio.sleep(0, '\n'.join(map(lambda x: x.strip(), [line for line in docstring_match.group('description').splitlines() if line != ''])))

                    if not new_attrs.get('example') and docstring_match.group('example'):
                        new_attrs['example'] = await asyncio.sleep(0, '\n'.join(map(lambda x: x.strip(), [line for line in docstring_match.group('example').splitlines() if line != '' and line.strip().casefold() != 'example:'])))

                    if not new_attrs.get('extra_info') and docstring_match.group('extra_info'):
                        new_attrs['extra_info'] = await asyncio.sleep(0, '\n'.join(map(lambda x: x.strip(), [line for line in docstring_match.group('extra_info').splitlines() if line != '' and line.strip().casefold() != 'info:'])))

                    if not new_attrs.get('short_doc') and docstring_match.group('description'):
                        new_attrs['short_doc'] = await asyncio.sleep(0, list(map(lambda x: x.strip(), [line for line in docstring_match.group('description').splitlines() if line != '']))[0])

                    if not new_attrs.get('brief') and new_attrs.get('short_doc'):
                        brief = new_attrs.get("short_doc")
                        new_attrs['brief'] = await asyncio.sleep(0, shorten(brief, 30))

            _new_dict[command_name] = await asyncio.sleep(0, new_attrs)
        await asyncio.to_thread(writejson, _new_dict, file_path)

    async def on_ready_setup(self):

        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug("'%s' sub_support was UPDATED", str(self))

    async def retire(self):
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return EssentialCommandsKeeper
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
