# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from enum import Enum, Flag, auto, unique
from functools import reduce
from operator import or_
import inflect

# endregion[Imports]

inflect_engine = inflect.engine()


class RequestStatus(Enum):
    Ok = 200
    NotFound = 404
    NotAuthorized = 401


class WatermarkPosition(Flag):
    Top = auto()
    Bottom = auto()
    Left = auto()
    Right = auto()
    Center = auto()


WATERMARK_COMBINATIONS = {WatermarkPosition.Left | WatermarkPosition.Top,
                          WatermarkPosition.Left | WatermarkPosition.Bottom,
                          WatermarkPosition.Right | WatermarkPosition.Top,
                          WatermarkPosition.Right | WatermarkPosition.Bottom,
                          WatermarkPosition.Center | WatermarkPosition.Top,
                          WatermarkPosition.Center | WatermarkPosition.Bottom,
                          WatermarkPosition.Center | WatermarkPosition.Left,
                          WatermarkPosition.Center | WatermarkPosition.Right,
                          WatermarkPosition.Center | WatermarkPosition.Center}


class DataSize(Enum):
    Bytes = 1024**0
    KiloBytes = 1024**1
    MegaBytes = 1024**2
    GigaBytes = 1024**3
    TerraBytes = 1024**4

    @property
    def short_name(self):
        if self.name != "Bytes":
            return self.name[0].lower() + 'b'
        return 'b'

    def convert(self, in_bytes: int, round_digits=3, annotate=False):
        converted_bytes = round(in_bytes / self.value, ndigits=round_digits)
        if annotate is True:
            return str(converted_bytes) + ' ' + self.short_name
        return converted_bytes


class EmbedType(Enum):
    Rich = "rich"
    Image = "image"
    Video = "video"
    Gifv = "gifv"
    Article = "article"
    Link = "link"


class CogMetaStatus(Flag):
    """
    [summary]

    all states template:
        CogMetaStatus.READY|CogMetaStatus.WORKING|CogMetaStatus.OPEN_TODOS|CogMetaStatus.UNTESTED|CogMetaStatus.FEATURE_MISSING|CogMetaStatus.NEEDS_REFRACTORING|CogMetaStatus.OUTDATED|CogMetaStatus.CRASHING|CogMetaStatus.EMPTY


    Args:
        Flag ([type]): [description]

    Returns:
        [type]: [description]
    """

    READY = auto()
    WORKING = auto()
    OPEN_TODOS = auto()
    UNTESTED = auto()
    FEATURE_MISSING = auto()
    NEEDS_REFRACTORING = auto()
    OUTDATED = auto()
    CRASHING = auto()
    DOCUMENTATION_MISSING = auto()
    FOR_DEBUG = auto()
    EMPTY = auto()
    WIP = auto()

    @classmethod
    def split(cls, combined_cog_state):
        if combined_cog_state is cls.EMPTY:
            return [combined_cog_state]
        _out = []
        for state in cls:
            if state is not cls.EMPTY and state in combined_cog_state:
                _out.append(state)
        return _out

    @property
    def _flags(self):
        _out = []
        for member in self.__class__.__members__.values():
            if member in self:
                _out.append(member)
        return _out

    def serialize(self):
        return [flag.name for flag in self._flags]


@unique
class UpdateTypus(Flag):
    CYCLIC = auto()
    GUILD = auto()
    ROLES = auto()
    MEMBERS = auto()
    CONFIG = auto()
    COMMANDS = auto()
    COGS = auto()
    ALIAS = auto()
    DATE = auto()
    TIME = auto()
    RECONNECT = auto()
    DATE_AND_TIME = DATE | TIME

    @classmethod
    @property
    def ALL(cls):
        all_flags = [member for member in cls.__members__.values()]
        return reduce(or_, all_flags)


@unique
class ExtraHelpParameter(Enum):
    ALL = auto


@unique
class HelpCategory(Enum):
    COG = 'cog'
    COMMAND = 'command'
    CATEGORY = 'category'

    @classmethod
    def _missing_(cls, value):
        mod_value = inflect_engine.singular_noun(value).casefold()
        try:
            return cls(mod_value)
        except ValueError:
            raise ValueError("%r is not a valid %s" % (value, cls.__name__))


class ContextAskAnswer(Enum):
    ACCEPTED = auto()
    DECLINED = auto()
    CANCELED = auto()
    NOANSWER = auto()


class GithubLabelOperator(Enum):
    AND = auto()
    OR = auto()
    NOT = auto()
    NOT_ANY = auto()
