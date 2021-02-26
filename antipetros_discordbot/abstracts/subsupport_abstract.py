"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from abc import ABC, abstractmethod

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class SubSupportBase(ABC):
    @abstractmethod
    async def if_ready(self):
        ...

    @abstractmethod
    def retire(self):
        ...

    @abstractmethod
    async def update(self, typus):
        ...

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self):
        return str(self)


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
