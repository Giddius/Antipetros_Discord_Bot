"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.bot_support.sub_support import SUB_SUPPORT_CLASSES


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


class BotSupporter:

    def __init__(self, bot):
        self.bot = bot
        self.subsupports = []
        self.available_subsupport_classes = SUB_SUPPORT_CLASSES

    def find_available_subsupport_classes(self):
        pass

    def recruit_subsupports(self):

        for subsupport_class in self.available_subsupport_classes:
            self.subsupports.append(subsupport_class(self.bot, self))
        log.debug("recruited subsupporters: %s", ', '.join([str(subsupporter) for subsupporter in self.subsupports]))

    def __getattr__(self, attribute_name):
        _out = None
        for subsupport in self.subsupports:
            if hasattr(subsupport, attribute_name):
                _out = getattr(subsupport, attribute_name)
                return _out
        raise AttributeError

    # def really_has_attribute(self, attribute_name):
    #     return hasattr(self, attribute_name) and all(hasattr(subsupport, attribute_name) is False for subsupport in self.subsupports)

    # async def to_all_subsupports(self, attribute_name, *args, **kwargs):
    #     # TODO: Refactor so it is callable like cogs
    #     if self.really_has_attribute(attribute_name):
    #         if iscoroutine(getattr(self, attribute_name)):
    #             await getattr(self, attribute_name)(*args, **kwargs)
    #         else:
    #             getattr(self, attribute_name)(*args, **kwargs)
    #     for subsupport in self.subsupports:
    #         if hasattr(subsupport, attribute_name):
    #             if iscoroutinefunction(getattr(subsupport, attribute_name)):
    #                 await getattr(subsupport, attribute_name)(*args, **kwargs)
    #             else:
    #                 getattr(subsupport, attribute_name)(*args, **kwargs)

    def retire_subsupport(self):
        for subsupport in self.subsupports:
            subsupport.retire()

    @ staticmethod
    def log_attribute_not_found(*args, **kwargs):
        return log.critical("'%s' was not found in any subsupport, args used: '%s', kwargs used: '%s'", str(args[0]), str(args), str(kwargs))

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{str(self)}({', '.join([str(subsupport) for subsupport in self.subsupports])})"

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
