
# * Standard Library Imports -->
from datetime import datetime
import base64
import lzma
import shutil
import os

# * Third Party Imports -->
from fuzzywuzzy import process as fuzzprocess

# * Gid Imports -->
from gidtools.gidsql.facade import GidSqliteDatabase, Fetch
import gidlogger as glog
# * Local Imports -->
from antipetros_discordbot.utility.named_tuples import LINK_DATA_ITEM
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.gidtools_functions import timenamemaker, limit_amount_files_absolute, pathmaker
from antipetros_discordbot.utility.misc import sync_to_async


APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')


DB_LOC_LINKS = pathmaker(APPDATA['database'], 'save_link_db.db')
SCRIPT_LOC_LINKS = APPDATA['save_link_sql']

DB_LOC_SUGGESTIONS = pathmaker(APPDATA['database'], "save_suggestion.db")
SCRIPT_LOC_SUGGESTIONS = APPDATA['save_suggestion_sql']

ARCHIVE_LOCATION = APPDATA['archive']


# TODO: create regions for this file
# TODO: update save link Storage to newer syntax (composite access)
# TODO: Document and Docstrings
# TODO: refractor to subfolder


log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)


class LinkDataStorageSQLite:
    def __init__(self):
        self.db = GidSqliteDatabase(DB_LOC_LINKS, SCRIPT_LOC_LINKS)
        self.db.startup_db()
        self.db.vacuum()
        glog.class_init_notification(log, self)

    def add_data(self, item, message_id):
        if isinstance(item, LINK_DATA_ITEM):
            self.db.writer.write(self.db.scripter['insert_link_author'], (item.author.name, item.author.display_name, item.author.id, any(str(_role) == 'Member' for _role in item.author.roles)))
            self.db.writer.write(self.db.scripter['insert_saved_link'], (item.link_name, item.link, item.date_time, item.delete_date_time, item.author.id, message_id))

    @property
    def std_datetime_format(self):
        return BASE_CONFIG.get('datetime', 'std_format')

    @property
    def link_messages_to_remove(self):
        for item in self.db.query('SELECT "message_discord_id" FROM "saved_links_tbl" WHERE "is_removed"=0 AND "delete_time"<?', (datetime.utcnow(),)):
            yield item[0]

    @ property
    def all_link_names(self):
        _out_list = []
        for item in self.db.reader.query(self.db.scripter['list_of_name_save_link']):
            _out_list.append(item[0])
        return set(_out_list)

    def update_removed_status(self, message_id):
        self.db.write('update_removed', (message_id,))

    def clear(self):
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

        self.db.startup_db()

    def delete_link(self, name):
        self.db.write('delete_link', (name,))
        self.db.vacuum()

    def get_all_posted_links(self):
        for item in self.db.query('get_all_link_delete_info'):
            yield item[0]

    def get_link_for_delete(self, name):
        _name = fuzzprocess.extractOne(name, self.all_link_names, score_cutoff=80)
        if _name is None:
            return None, None, None
        _name = _name[0]
        result = self.db.query(self.db.scripter['get_link_delete_info'], (_name,), fetch=Fetch.One)
        print(result[0], result[1], result[2])
        return result[0], result[1], result[2]

    def get_link(self, name):
        _name = fuzzprocess.extractOne(name, self.all_link_names)
        if _name is None:
            return None, None
        _name = _name[0]
        _out = self.db.reader.query(self.db.scripter['get_link'], (_name,))[0]

        return _out[0], _out[1]

    def get_all_links(self, in_format='plain'):
        if in_format == 'json':
            _out = {}
            for item in self.db.reader.query(self.db.scripter['get_all_links']):
                if item[2] not in _out:
                    _out[item[2]] = []
                _out[item[2]].append((item[0], item[1]))
        elif in_format == 'plain':
            _out = []
            for item in self.db.reader.query(self.db.scripter['get_all_links']):
                _out.append(item[0] + ' --> ' + item[1])
        return _out


class SuggestionDataStorageSQLite:
    def __init__(self):
        self.db = GidSqliteDatabase(DB_LOC_SUGGESTIONS, SCRIPT_LOC_SUGGESTIONS)
        self.db.startup_db()
        self.db.vacuum()
        glog.class_init_notification(log, self)

    @property
    def category_emojis(self):
        _out = {}
        for item in self.db.query('SELECT "emoji", "name" FROM "category_tbl"', row_factory=True):
            _out[item['emoji']] = item['name']
        return _out

    def get_all_non_discussed_message_ids(self, as_set: bool = True):
        result = self.db.query('get_all_messages_not_discussed', row_factory=True)
        _out = [item['message_discord_id'] for item in result]
        if as_set is True:
            _out = set(_out)
        return _out

    def update_votes(self, vote_type, amount, message_id):
        phrase = 'update_upvotes' if vote_type == 'THUMBS UP SIGN' else 'update_downvotes'
        self.db.write(phrase, (amount, message_id))

    def update_category(self, category, message_id):
        self.db.write('update_category', (category, message_id))

    def get_all_message_ids(self, as_set: bool = True):
        result = self.db.query('get_all_message_ids', row_factory=True)

        _out = [item['message_discord_id'] for item in result]
        if as_set is True:
            _out = set(_out)
        return _out

    def get_suggestions_per_author(self, author_name):
        result = self.db.query('get_suggestions_by_author', (author_name,), row_factory=True)
        return list(result)

    def get_suggestion_by_id(self, suggestion_id):
        result = self.db.query('get_suggestion_by_id', (suggestion_id,), row_factory=True)
        return result[0]

    def remove_suggestion_by_id(self, suggestion_id):
        data_id = self.db.query('get_data_id_by_message_id', (suggestion_id,), row_factory=True)[0]['extra_data_id']
        self.db.write('remove_suggestion_by_id', (suggestion_id,))
        if data_id is not None:
            self.db.write('remove_extra_data_by_id', (data_id,))

    def add_suggestion(self, suggestion_item):

        for author in [suggestion_item.message_author, suggestion_item.reaction_author]:
            self.db.write('insert_author', (author.name,
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
                         suggestion_item.message.jump_url)

        else:
            extra_data_name, extra_data_path = suggestion_item.extra_data

            self.db.write('insert_extra_data', (extra_data_name, extra_data_path))
            sql_phrase = 'insert_suggestion_with_data'
            arguments = (suggestion_item.name,
                         suggestion_item.message.id,
                         suggestion_item.message_author.id,
                         suggestion_item.reaction_author.id,
                         suggestion_item.message.created_at,
                         suggestion_item.time,
                         suggestion_item.message.content,
                         suggestion_item.message.jump_url,
                         extra_data_name)
        self.db.write(sql_phrase, arguments)
        self.db.vacuum()

    def get_all_suggestion_not_discussed(self):
        log.debug('querying all suggestions by time')
        result = self.db.query('get_suggestions_not_discussed', row_factory=True)
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

    def mark_discussed(self, sql_id):
        self.db.write('mark_discussed', (sql_id,))

    def clear(self):
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

        self.db.startup_db()
