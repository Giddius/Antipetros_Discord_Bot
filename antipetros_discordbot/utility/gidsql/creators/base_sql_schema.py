"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from abc import abstractmethod

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class BaseSchema:

    @classmethod
    @abstractmethod
    def provide_sql(cls):
        ...

    @classmethod
    @abstractmethod
    def create_table_phrase(cls, exist_error=False):
        ...

    @classmethod
    @abstractmethod
    def full_query_phrase(cls):
        ...

    @classmethod
    @abstractmethod
    def insert_phrase(cls, values: dict):
        ...

    @classmethod
    @abstractmethod
    def drop_phrase(cls):
        ...

    @classmethod
    @abstractmethod
    def query(cls, columns: list):
        ...


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
