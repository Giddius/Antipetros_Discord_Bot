
# region [Imports]


import os
import shutil
from inspect import getmembers, getfile, getsourcefile, getsource, getsourcelines, getdoc
from datetime import datetime
import gidlogger as glog
from icecream import ic
from textwrap import dedent
from antipetros_discordbot.utility.gidsql.facade import AioGidSqliteDatabase
from antipetros_discordbot.utility.gidtools_functions import pathmaker, timenamemaker, limit_amount_files_absolute
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.misc import antipetros_repo_rel_path
# endregion[Imports]

# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')


DB_LOC_LINKS = pathmaker(APPDATA['database'], 'save_link_db.db')
SCRIPT_LOC_LINKS = APPDATA['save_link_sql']

DB_LOC_SUGGESTIONS = pathmaker(APPDATA['database'], "save_suggestion.db")
SCRIPT_LOC_SUGGESTIONS = APPDATA['save_suggestion_sql']

DB_LOC_META_DATA = pathmaker(APPDATA['database'], "meta_data.db")
SCRIPT_LOC_META_DATA = APPDATA['meta_data_sql']

ARCHIVE_LOCATION = APPDATA['archive']
LOG_EXECUTION = False

# endregion [Constants]

# region [Logging]


log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)


# endregion[Logging]


class AioMetaDataStorageSQLite:
    def __init__(self):
        self.db = AioGidSqliteDatabase(db_location=DB_LOC_META_DATA, script_location=SCRIPT_LOC_META_DATA, log_execution=LOG_EXECUTION)
        self.was_created = self.db.startup_db()
        self.db.vacuum()
        glog.class_init_notification(log, self)

    async def insert_cpu_performance(self, timestamp: datetime, usage_percent: int, load_avg_1: int, load_avg_5: int, load_avg_15: int):
        await self.db.aio_write("insert_cpu_performance.sql", (timestamp, usage_percent, load_avg_1, load_avg_5, load_avg_15))

    async def insert_latency_perfomance(self, timestamp: datetime, latency: int):
        await self.db.aio_write('insert_latency_performance', (timestamp, latency))

    async def insert_memory_perfomance(self, timestamp: datetime, memory_in_use: int):
        await self.db.aio_write('insert_memory_performance', (timestamp, memory_in_use))

    async def insert_cogs(self, bot):
        for cog_name, cog_object in bot.cogs.items():
            abs_path = getsourcefile(cog_object.__class__)
            ic(abs_path)
            rel_path = await antipetros_repo_rel_path(abs_path)
            ic(rel_path)
            category = os.path.basename(os.path.dirname(rel_path))
            ic(category)
            description = dedent(str(getdoc(cog_object.__class__)))
            await self.db.aio_write('insert_cog_category', (category,))
            await self.db.aio_write('insert_cog', (cog_name, cog_object.config_name, description, category, rel_path, 1))


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
