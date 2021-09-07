# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import asyncio
import logging
from enum import Enum, auto
import re
from typing import List, Union
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from datetime import datetime, timedelta, timezone
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidsql.phrasers import GidSqliteInserter
from antipetros_discordbot.utility.gidsql.db_reader import Fetch, GidSqliteReader, AioGidSqliteReader
from antipetros_discordbot.utility.gidsql.db_writer import GidSQLiteWriter, AioGidSQLiteWriter
from antipetros_discordbot.utility.gidsql.script_handling import GidSqliteScriptProvider
from antipetros_discordbot.utility.gidtools_functions import pathmaker
from sortedcontainers import SortedList
# endregion[Imports]

__updated__ = '2020-11-28 03:29:05'

# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = logging.getLogger('gidsql')

glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
# endregion[Constants]


class BackUpDbFile:
    backup_date_regex = re.compile(r"""
        \[
        (?P<year>\d+)
        [^\d]
        (?P<month>\d+)
        [^\d]
        (?P<day>\d+)
        [^\d]
        (?P<hour>\d+)
        [^\d]
        (?P<minute>\d+)
        [^\d]
        (?P<second>\d+)
        \_UTC
        \]
        \_
        .*
        """, re.VERBOSE | re.IGNORECASE)

    def __init__(self, path: Union[str, os.PathLike]) -> None:
        self.path = pathmaker(path)
        self.name = os.path.basename(self.path)
        self.backup_date = self._parse_backup_date()

    def _parse_backup_date(self) -> datetime:
        cleaned_name = self.name.split('.')[0].casefold()
        date_and_time_match = self.backup_date_regex.match(cleaned_name)
        back_up_date = datetime(**date_and_time_match.groupdict(), microsecond=0, tzinfo=timezone.utc)
        return back_up_date

    def delete(self):
        os.remove(self.path)
        log.info("removed backup DB file '%s'", self.name)


class PhraseType(Enum):
    Insert = auto()
    Query = auto()
    Create = auto()
    Drop = auto()


class GidSqliteDatabase:
    Insert = PhraseType.Insert
    Query = PhraseType.Query
    Create = PhraseType.Create
    Drop = PhraseType.Drop

    All = Fetch.All
    One = Fetch.One

    phrase_objects = {Insert: GidSqliteInserter, Query: None, Create: None, Drop: None}
    backup_datetime_format = "%Y-%m-%d_%H-%M-%S"
    backup_name_template = "[{date_and_time}_UTC]_{original_name}_backup.{original_file_extension}"

    def __init__(self, db_location, script_location, config=None, log_execution: bool = True):
        self.path = db_location
        self.name = os.path.basename(db_location)
        self.script_location = script_location
        self.config = config
        self.pragmas = None
        if self.config is not None:
            self.pragmas = self.config.retrieve('general_settings', 'pragmas', typus=List[str], default_fallback=[])
        self.amount_backups_to_keep = self.config.retrieve('general_settings', 'amount_backups_to_keep', typus=int, default_fallback=10) if self.config is not None else 10

        self.writer = GidSQLiteWriter(self.path, self.pragmas, log_execution=log_execution)
        self.reader = GidSqliteReader(self.path, self.pragmas, log_execution=log_execution)
        self.scripter = GidSqliteScriptProvider(self.script_location)

    @property
    def back_up_folder(self) -> str:
        orig_folder_name = os.path.dirname(self.path)
        backup_folder_name = os.path.basename(self.path).split('.')[0] + '_backups'
        backup_folder = os.path.realpath(os.path.join(orig_folder_name, backup_folder_name))
        backup_folder = pathmaker(backup_folder)
        if os.path.isdir(backup_folder) is False:
            os.makedirs(backup_folder)
        return backup_folder

    @property
    def stored_backups(self) -> list[BackUpDbFile]:
        stored_backups = []
        orig_file_extension = os.path.basename(self.path).split('.')[0]
        for file in os.scandir(self.back_up_folder):
            if file.is_file() and file.name.endswith(f".{orig_file_extension}"):
                stored_backups.append(BackUpDbFile(file.path))
        return sorted(stored_backups, key=lambda x: x.backup_date, reverse=True)

    @property
    def backup_name(self) -> str:
        orig_name, orig_file_extension = self.name.split('.')
        format_data = {"date_and_time": datetime.now(tz=timezone.utc).strftime(self.backup_datetime_format),
                       "original_name": orig_name,
                       "original_file_extension": orig_file_extension}

        return self.backup_name_template.format(**format_data)

    @property
    def backup_path(self) -> str:
        return pathmaker(self.back_up_folder, self.backup_name)

    def startup_db(self, overwrite=False):
        if os.path.exists(self.path) is True and overwrite is True:
            os.remove(self.path)

        for script in self.scripter.setup_scripts:
            for sql_phrase in script.split(';'):
                if sql_phrase:

                    self.writer.write(sql_phrase=sql_phrase)
        return True

    def new_phrase(self, typus: PhraseType):
        return self.phrase_objects.get(typus)()

    def write(self, phrase, variables=None):

        if isinstance(phrase, str):
            sql_phrase = self.scripter.get(phrase, None)
            if sql_phrase is None:
                sql_phrase = phrase
            self.writer.write(sql_phrase, variables)

    def query(self, phrase, variables=None, fetch: Fetch = Fetch.All, row_factory: Union[bool, any] = False):

        if row_factory:
            _factory = None if isinstance(row_factory, bool) is True else row_factory
            self.reader.enable_row_factory(in_factory=_factory)
        sql_phrase = self.scripter.get(phrase, None)
        if sql_phrase is None:
            sql_phrase = phrase
        _out = self.reader.query(sql_phrase, variables=variables, fetch=fetch)
        self.reader.disable_row_factory()
        return _out

    def vacuum(self):
        self.write('VACUUM')

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path}, {self.script_location}, {self.config})"

    def __str__(self) -> str:
        return self.__class__.__name__


class AioGidSqliteDatabase(GidSqliteDatabase):

    def __init__(self, db_location, script_location, config=None, log_execution: bool = True):
        super().__init__(db_location, script_location, config=config, log_execution=log_execution)
        self.aio_writer = AioGidSQLiteWriter(self.path, self.pragmas, log_execution=log_execution)
        self.aio_reader = AioGidSqliteReader(self.path, self.pragmas, log_execution=log_execution)

    async def aio_startup_db(self, overwrite=False):

        if os.path.exists(self.path) is True and overwrite is True:
            os.remove(self.path)

        for script in self.scripter.setup_scripts:
            for sql_phrase in script.split(';'):
                if sql_phrase:
                    await self.aio_write(sql_phrase)

        return True

    async def aio_write(self, phrase, variables=None):

        if isinstance(phrase, str):
            sql_phrase = self.scripter.get(phrase, None)
            if sql_phrase is None:
                sql_phrase = phrase
            await self.aio_writer.write(sql_phrase, variables)

    async def aio_query(self, phrase, variables=None, fetch: Fetch = Fetch.All, row_factory: Union[bool, any] = False):

        sql_phrase = self.scripter.get(phrase, None)
        if sql_phrase is None:
            sql_phrase = phrase

        async with self.aio_reader.active_row_factory(in_factory=row_factory):
            _out = await self.aio_reader.query(sql_phrase, variables=variables, fetch=fetch)
            await self.aio_reader.disable_row_factory()
            return _out

    async def aio_vacuum(self):

        await self.aio_write('VACUUM')
