
# region [Imports]


import os
from typing import List, Union
import shutil
from inspect import getdoc, getsourcefile
from datetime import datetime, timezone, timedelta
import gidlogger as glog
from collections import Counter
import psutil
import discord
from discord.ext import commands, flags, tasks, ipc
from textwrap import dedent
import asyncio
from functools import cached_property
from antipetros_discordbot.utility.gidsql.facade import AioGidSqliteDatabase
from antipetros_discordbot.utility.gidtools_functions import pathmaker, timenamemaker, limit_amount_files_absolute, bytes2human
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.misc import antipetros_repo_rel_path
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand
# endregion[Imports]

# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')


DB_LOC_SUGGESTIONS = pathmaker(APPDATA['database'], "save_suggestion.db")
SCRIPT_LOC_SUGGESTIONS = APPDATA['save_suggestion_sql']

DB_LOC_GENERAL = pathmaker(APPDATA['database'], "general_antipetros.db")
SCRIPT_LOC_GENERAL = APPDATA['general_db_sql']

ARCHIVE_LOCATION = APPDATA['archive']
LOG_EXECUTION = False

# endregion [Constants]

# region [Logging]


log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)


# endregion[Logging]

class ChannelUsageResult:
    def __init__(self):
        self.result_data = {}

    async def add_data(self, data: dict):
        self.result_data.append(await asyncio.sleep(0, data))

    async def convert_data_to_channels(self, bot):
        temp = []
        for data in self.result_data:
            temp.append(await asyncio.sleep(0, bot.channel_from_id(data)))
        self.result_data = temp

    async def get_as_counter(self) -> Counter:
        return await asyncio.to_thread(Counter, self.result_data)


class MemoryPerformanceItem:
    total_memory = psutil.virtual_memory().total
    initial_memory = int(os.getenv('INITIAL_MEMORY_USAGE'))

    def __init__(self, timestamp, memory_in_use: int):
        self.raw_timestamp = timestamp
        self.date_time = datetime.fromisoformat(self.raw_timestamp)
        self.memory_in_use = memory_in_use
        self.as_percent = (self.memory_in_use / self.total_memory) * 100

    @cached_property
    def pretty_memory_in_use(self):
        return bytes2human(self.memory_in_use, annotate=True)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(timestamp={self.raw_timestamp}, memory_in_use={self.memory_in_use})"

    def __str__(self) -> str:
        return f"{self.date_time.strftime(STANDARD_DATETIME_FORMAT)}: {self.pretty_memory_in_use}, {self.as_percent}%"


class LatencyPerformanceItem:

    def __init__(self, timestamp, latency: int):
        self.raw_timestamp = timestamp
        self.date_time = datetime.fromisoformat(self.raw_timestamp)
        self.latency = latency

    @cached_property
    def pretty_latency(self):
        return str(round(self.latency, ndigits=2)) + ' ms'

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(timestamp={self.raw_timestamp}, latency={self.latency})"

    def __str__(self) -> str:
        return f"{self.date_time.strftime(STANDARD_DATETIME_FORMAT)}: {self.pretty_latency}"


class CpuPerformanceItem:

    def __init__(self, timestamp, usage_percent: int, load_average_1: int, load_average_5: int, load_average_15: int):
        self.raw_timestamp = timestamp
        self.date_time = datetime.fromisoformat(self.raw_timestamp)
        self.usage_percent = usage_percent
        self.load_average_1 = load_average_1
        self.load_average_5 = load_average_5
        self.load_average_15 = load_average_15

    @cached_property
    def pretty_usage_percent(self):
        return str(self.usage_percent) + '%'

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(timestamp={self.raw_timestamp}, usage_percent={self.usage_percent}, load_average_1={self.load_average_1}, load_average_5={self.load_average_5}, load_average_15={self.load_average_15})"

    def __str__(self) -> str:
        return f"{self.date_time.strftime(STANDARD_DATETIME_FORMAT)}: {self.pretty_usage_percent}"


class AioGeneralStorageSQLite:
    command_attr_names = ["help",
                          "brief",
                          "short_doc",
                          "usage",
                          "example",
                          "gif",
                          "github_link",
                          "enabled",
                          "hidden"]

    def __init__(self):
        self.db = AioGidSqliteDatabase(db_location=DB_LOC_GENERAL, script_location=SCRIPT_LOC_GENERAL, log_execution=LOG_EXECUTION)
        self.was_created = self.db.startup_db()
        self.db.vacuum()
        glog.class_init_notification(log, self)

    async def aio_vacuum(self):
        await self.db.aio_vacuum()

    async def insert_command_usage(self, command: Union[commands.Command, AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand]):
        command_name = command.name
        await self.db.aio_write('insert_command_usage', (command_name,))

    async def insert_cogs_many(self, cogs: List[commands.Cog]):
        categories_data = []
        cogs_data = []
        for cog in cogs:
            abs_path = getsourcefile(cog.__class__)
            rel_path = await antipetros_repo_rel_path(abs_path)
            category = os.path.basename(os.path.dirname(rel_path))
            if category not in ['dev_cogs']:
                categories_data.append((category, category))
                cogs_data.append(await asyncio.sleep(0, (str(cog), str(cog), cog.config_name, cog.description, category, rel_path)))

        await self.db.aio_write('insert_cog_category', categories_data)
        await self.db.aio_write('insert_cog', cogs_data)

    async def insert_cog(self, cog: commands.Cog):
        abs_path = getsourcefile(cog.__class__)
        rel_path = await antipetros_repo_rel_path(abs_path)
        category = os.path.basename(os.path.dirname(rel_path))
        if category not in ['dev_cogs']:
            description = dedent(str(getdoc(cog.__class__)))
            await self.db.aio_write('insert_cog_category', (category, category))
            await self.db.aio_write('insert_cog', (str(cog), str(cog), cog.config_name, description, category, rel_path))

    async def insert_image(self, name: str, image_bytes: bytes):
        await self.db.aio_write('insert_image', (name, image_bytes))

    async def insert_commands_many(self, commands_list: List[commands.Command]):
        commands_data = []
        for command in commands_list:
            name = command.name
            cog_name = str(command.cog)
            is_group = 1 if isinstance(command, AntiPetrosBaseGroup) else 0
            params = [name, name, cog_name, is_group]
            for attr_name in self.command_attr_names:
                attr_value = None
                if hasattr(command, attr_name) and getattr(command, attr_name) != 'NA':
                    attr_value = getattr(command, attr_name)
                    if attr_name == 'gif' and attr_value is not None:
                        attr_value = await antipetros_repo_rel_path(attr_value)
                params.append(attr_value)
            # await self.insert_image(name, await command.get_source_code_image())
            params.append(name)
            commands_data.append(await asyncio.sleep(0, tuple(params)))

        await self.db.aio_write('insert_command', commands_data)

    async def insert_command(self, command: Union[commands.Command, AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand]):
        name = command.name
        cog_name = str(command.cog)
        is_group = 1 if isinstance(command, AntiPetrosBaseGroup) else 0
        params = [name, name, cog_name, is_group]
        for attr_name in self.command_attr_names:
            attr_value = None
            if hasattr(command, attr_name) and getattr(command, attr_name) != 'NA':
                attr_value = getattr(command, attr_name)
                if attr_name == 'gif' and attr_value is not None:
                    attr_value = await antipetros_repo_rel_path(attr_value)
            params.append(attr_value)
        # await self.insert_image(name, await command.get_source_code_image())
        params.append(name)
        params = tuple(params)
        await self.db.aio_write('insert_command', params)

    async def insert_channel_use(self, text_channel: discord.TextChannel):
        channel_id = text_channel.id
        await self.db.aio_write('insert_channel_use', (channel_id,))

    async def insert_text_channels(self, text_channels: List[discord.TextChannel]):
        text_channels_data = []
        for text_channel in text_channels:
            _id = text_channel.id
            name = text_channel.name
            position = text_channel.position
            created_at = text_channel.created_at
            category_id = text_channel.category.id
            topic = text_channel.topic
            text_channels_data.append(await asyncio.sleep(0, (_id, name, position, created_at, category_id, topic, False)))
            await asyncio.sleep(0)
        await self.db.aio_write("insert_text_channel", text_channels_data)

    async def insert_category_channels(self, category_channels: List[discord.CategoryChannel]):
        category_channels_data = []
        for category_channel in category_channels:
            _id = category_channel.id
            name = category_channel.name
            position = category_channel.position
            created_at = category_channel.created_at
            category_channels_data.append(await asyncio.sleep(0, (_id, name, position, created_at, False)))

        await self.db.aio_write("insert_category_channel", category_channels_data)

    async def update_text_channel_deleted(self, text_channel_id: int):
        await self.db.aio_write("update_text_channel_deleted", (text_channel_id, True))

    async def update_category_channel_deleted(self, category_channel_id: int):
        await self.db.aio_write("updated_category_channels_deleted", (category_channel_id, True))

    async def get_category_channel_ids(self):
        result = await self.db.aio_query("get_all_category_channel_ids", row_factory=True)
        return [row['id'] for row in result]

    async def get_text_channel_ids(self):
        result = await self.db.aio_query("get_all_text_channel_ids", row_factory=True)
        return [row['id'] for row in result]

    async def get_cpu_data_last_24_hours(self):
        now = datetime.now(tz=timezone.utc)
        one_day_ago = now - timedelta(hours=24)

        result = await self.db.aio_query('get_cpu_performance', (one_day_ago, now), row_factory=True)
        all_items = []
        for row in result:

            all_items.append(CpuPerformanceItem(**row))
        return all_items

    async def get_latency_data_last_24_hours(self):
        now = datetime.now(tz=timezone.utc)
        one_day_ago = now - timedelta(hours=24)

        result = await self.db.aio_query('get_latency_performance', (one_day_ago, now), row_factory=True)
        all_items = []
        for row in result:

            all_items.append(LatencyPerformanceItem(**row))
        return all_items

    async def get_memory_data_last_24_hours(self):
        now = datetime.now(tz=timezone.utc)
        one_day_ago = now - timedelta(hours=24)

        result = await self.db.aio_query('get_memory_performance', (one_day_ago, now), row_factory=True)
        all_items = []
        for row in result:

            all_items.append(MemoryPerformanceItem(**row))
        return all_items

    async def get_channel_usage(self, from_datetime: datetime = None, to_datetime: datetime = None) -> ChannelUsageResult:
        script_name = "get_channel_usage"
        if from_datetime is None and to_datetime is None:
            script_name = "get_channel_usage_all"
        elif from_datetime is None:
            script_name = "get_channel_usage_only_from"
        elif to_datetime is None:
            script_name = "get_channel_usage_only_to"

        arguments = tuple(arg for arg in [from_datetime, to_datetime] if arg is not None)
        result = await self.db.aio_query(script_name, arguments, row_factory=True)
        result_item = ChannelUsageResult()

        result_item.result_data = [row['channel_id'] for row in result]
        return result_item

    async def get_command_usage(self, from_datetime: datetime = None, to_datetime: datetime = None, as_counter: bool = True):
        script_name = "get_command_usage"
        if from_datetime is None and to_datetime is None:
            script_name = "get_command_usage_all"
        elif from_datetime is None:
            script_name = "get_command_usage_only_from"
        elif to_datetime is None:
            script_name = "get_command_usage_only_to"

        arguments = tuple(arg for arg in [from_datetime, to_datetime] if arg is not None)
        result = await self.db.aio_query(script_name, arguments, row_factory=True)
        if as_counter is True:
            return Counter(row['name'] for row in result)
        else:
            return [row['name'] for row in result]

    async def insert_cpu_performance(self, timestamp: datetime, usage_percent: int, load_avg_1: int, load_avg_5: int, load_avg_15: int):
        await self.db.aio_write("insert_cpu_performance", (timestamp, usage_percent, load_avg_1, load_avg_5, load_avg_15))

    async def insert_latency_perfomance(self, timestamp: datetime, latency: int):
        await self.db.aio_write('insert_latency_performance', (timestamp, latency))

    async def insert_memory_perfomance(self, timestamp: datetime, memory_in_use: int):
        await self.db.aio_write('insert_memory_performance', (timestamp, memory_in_use))

    def __str__(self):
        return self.__class__.__name__


class AioSuggestionDataStorageSQLite:
    def __init__(self):
        self.db = AioGidSqliteDatabase(db_location=DB_LOC_SUGGESTIONS, script_location=SCRIPT_LOC_SUGGESTIONS, log_execution=LOG_EXECUTION)
        self.was_created = self.db.startup_db()
        self.db.vacuum()
        glog.class_init_notification(log, self)

    async def get_save_emojis(self):
        _out = {}
        for item in await self.db.aio_query('get_all_save_emojis', row_factory=True):
            _out[item["name"]] = item['save_emoji']
        return _out

    async def category_emojis(self):
        _out = {}
        for item in await self.db.aio_query('SELECT "emoji", "name" FROM "category_tbl"', row_factory=True):
            _out[item['emoji']] = item['name']
        return _out

    async def get_all_non_discussed_message_ids(self, as_set: bool = True):
        result = await self.db.aio_query('get_all_messages_not_discussed', row_factory=True)
        _out = [item['message_discord_id'] for item in result]
        if as_set is True:
            return set(_out)
        return _out

    async def update_votes(self, vote_type, amount, message_id):
        phrase = 'update_upvotes' if vote_type == 'thumbs_up' else 'update_downvotes'
        await self.db.aio_write(phrase, (amount, message_id))

    async def update_category(self, category, message_id):
        await self.db.aio_write('update_category', (category, message_id))

    async def get_all_message_ids(self, as_set: bool = True):
        result = await self.db.aio_query('get_all_message_ids', row_factory=True)

        _out = [item['message_discord_id'] for item in result]
        if as_set is True:
            return set(_out)
        return _out

    async def get_suggestions_per_author(self, author_name):
        result = await self.db.aio_query('get_suggestions_by_author', (author_name,), row_factory=True)
        return list(result)

    async def get_suggestion_by_id(self, suggestion_id):
        result = await self.db.aio_query('get_suggestion_by_id', (suggestion_id,), row_factory=True)
        return result[0]

    async def remove_suggestion_by_id(self, suggestion_id):
        data_id = await self.db.aio_query('get_data_id_by_message_id', (suggestion_id,), row_factory=True)
        data_id = data_id[0]['extra_data_id']
        await self.db.aio_write('remove_suggestion_by_id', (suggestion_id,))
        if data_id is not None:
            await self.db.aio_write('remove_extra_data_by_id', (data_id,))

    async def add_suggestion(self, suggestion_item):

        for author in [suggestion_item.message_author, suggestion_item.reaction_author]:
            await self.db.aio_write('insert_author', (author.name,
                                                      author.display_name,
                                                      author.id,
                                                      any(role.name == 'Member' for role in author.roles)))

        if suggestion_item.extra_data is None:
            content = suggestion_item.message.content if suggestion_item.name is None else suggestion_item.message.content.replace('# ' + suggestion_item.name, '')
            sql_phrase = 'insert_suggestion'
            arguments = (suggestion_item.name,
                         suggestion_item.message.id,
                         suggestion_item.message_author.id,
                         suggestion_item.reaction_author.id,
                         suggestion_item.message.created_at,
                         suggestion_item.time,
                         suggestion_item.message.content,
                         suggestion_item.message.jump_url,
                         suggestion_item.team)

        else:
            extra_data_name, extra_data_path = suggestion_item.extra_data

            await self.db.aio_write('insert_extra_data', (extra_data_name, extra_data_path))
            sql_phrase = 'insert_suggestion_with_data'
            arguments = (suggestion_item.name,
                         suggestion_item.message.id,
                         suggestion_item.message_author.id,
                         suggestion_item.reaction_author.id,
                         suggestion_item.message.created_at,
                         suggestion_item.time,
                         suggestion_item.message.content,
                         suggestion_item.message.jump_url,
                         suggestion_item.team,
                         extra_data_name)
        await self.db.aio_write(sql_phrase, arguments)
        await self.db.aio_vacuum()

    async def get_all_suggestion_not_discussed(self):
        log.debug('querying all suggestions by time')
        result = await self.db.aio_query('get_suggestions_not_discussed', row_factory=True)
        none_id = 1
        _out = []

        for row in result:

            item = {'sql_id': row['id'],
                    'name': row['name'],
                    'utc_posted_time': row['utc_posted_time'],
                    'utc_saved_time': row['utc_saved_time'],
                    'upvotes': row['upvotes'],
                    'downvotes': row['downvotes'],
                    'link_to_message': row['link_to_message'],
                    'category_name': row['category_name'],
                    'author_name': row['author_name'],
                    'setter_name': row['setter_name'],
                    'content': row['content'],
                    'data_name': row['data_name'],
                    'data_location': row['data_location']}
            if item['name'] is None:
                item['name'] = 'NoName Suggestion ' + str(none_id)
                none_id += 1
            item['utc_posted_time'] = item['utc_posted_time'].split('.')[0]
            item['utc_saved_time'] = item['utc_saved_time'].split('.')[0]
            _out.append(item)
        return _out

    async def mark_discussed(self, sql_id):
        await self.db.aio_write('mark_discussed', (sql_id,))

    async def clear(self):
        BASE_CONFIG.read()
        use_backup = BASE_CONFIG.getboolean('databases', 'backup_db')
        amount_backups = BASE_CONFIG.getint('databases', 'amount_backups_to_keep')
        location = self.db.path
        if use_backup:
            new_name = os.path.basename(timenamemaker(location))
            new_location = pathmaker(ARCHIVE_LOCATION, new_name)
            shutil.move(location, new_location)
            basename = os.path.basename(location).split('.')[0]
            limit_amount_files_absolute(basename, ARCHIVE_LOCATION, amount_backups)
        else:
            os.remove(location)
        try:
            await self.db.startup_db()
        except Exception as error:
            self.db.startup_db()


general_db = AioGeneralStorageSQLite()
