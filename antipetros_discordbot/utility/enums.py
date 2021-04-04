# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from enum import Enum, Flag, auto, unique
from functools import reduce, wraps, partial
from operator import or_

# endregion[Imports]


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


class CogState(Flag):
    """
    [summary]

    all states template:
        CogState.READY|CogState.WORKING|CogState.OPEN_TODOS|CogState.UNTESTED|CogState.FEATURE_MISSING|CogState.NEEDS_REFRACTORING|CogState.OUTDATED|CogState.CRASHING|CogState.EMPTY


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

    @classmethod
    def split(cls, combined_cog_state):
        if combined_cog_state is cls.EMPTY:
            return [combined_cog_state]
        _out = []
        for state in cls:
            if state is not cls.EMPTY and state in combined_cog_state:
                _out.append(state)
        return _out


@unique
class UpdateTypus(Flag):
    CONFIG = auto()
    ALIAS = auto()
    DATE = auto()
    TIME = auto()
    DATE_AND_TIME = DATE | TIME

    @classmethod
    @property
    def ALL(cls):
        all_flags = [member for member in cls.__members__.values()]
        return reduce(or_, all_flags)
