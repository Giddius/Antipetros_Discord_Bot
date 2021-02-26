# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import logging
from enum import Enum, auto
from typing import Union
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidsql.phrasers import GidSqliteInserter
from antipetros_discordbot.utility.gidsql.db_reader import Fetch, GidSqliteReader, AioGidSqliteReader
from antipetros_discordbot.utility.gidsql.db_writer import GidSQLiteWriter, AioGidSQLiteWriter
from antipetros_discordbot.utility.gidsql.script_handling import GidSqliteScriptProvider
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

    def __init__(self, db_location, script_location, config=None, log_execution: bool = True):
        self.path = db_location
        self.script_location = script_location
        self.config = config
        self.pragmas = None
        if self.config is not None:
            self.pragmas = self.config.getlist('general_settings', 'pragmas')
        self.writer = GidSQLiteWriter(self.path, self.pragmas, log_execution=log_execution)
        self.reader = GidSqliteReader(self.path, self.pragmas, log_execution=log_execution)
        self.scripter = GidSqliteScriptProvider(self.script_location)

    def startup_db(self, overwrite=False):
        if os.path.exists(self.path) is True and overwrite is False:
            return False
        if os.path.exists(self.path) is True:
            os.remove(self.path)
        for script in self.scripter.setup_scripts:
            self.writer.write(script)

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
        if os.path.exists(self.path) is True and overwrite is False:
            return False
        if os.path.exists(self.path) is True:
            os.remove(self.path)
        for script in self.scripter.setup_scripts:
            await self.aio_write(script)

        return True

    async def aio_write(self, phrase, variables=None):

        if isinstance(phrase, str):
            sql_phrase = self.scripter.get(phrase, None)
            if sql_phrase is None:
                sql_phrase = phrase
            await self.aio_writer.write(sql_phrase, variables)

    async def aio_query(self, phrase, variables=None, fetch: Fetch = Fetch.All, row_factory: Union[bool, any] = False):

        if row_factory:
            _factory = None if isinstance(row_factory, bool) is True else row_factory
            await self.aio_reader.enable_row_factory(in_factory=_factory)
        sql_phrase = self.scripter.get(phrase, None)
        if sql_phrase is None:
            sql_phrase = phrase
        _out = await self.aio_reader.query(sql_phrase, variables=variables, fetch=fetch)
        await self.aio_reader.disable_row_factory()
        return _out

    async def aio_vacuum(self):

        await self.aio_write('VACUUM')
