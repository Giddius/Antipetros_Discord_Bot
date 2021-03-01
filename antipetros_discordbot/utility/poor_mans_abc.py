from antipetros_discordbot.utility.data import COG_NEEDED_ATTRIBUTES
from antipetros_discordbot.utility.exceptions import MissingNeededAttributeError
import gidlogger as glog

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]


def attribute_checker(cog):
    for attr in COG_NEEDED_ATTRIBUTES:
        if hasattr(cog, attr) is False:
            raise MissingNeededAttributeError(attr, cog)
    log.debug('attribute check for Cog "%s" SUCCEDED', cog.qualified_name)
    return cog
