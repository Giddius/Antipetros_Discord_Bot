# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from enum import Enum, Flag, auto, unique, EnumMeta
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
    CONFIG = auto()
    COMMANDS = auto()
    COGS = auto()
    ALIAS = auto()
    DATE = auto()
    TIME = auto()
    DATE_AND_TIME = DATE | TIME

    @classmethod
    @property
    def ALL(cls):
        all_flags = [member for member in cls.__members__.values()]
        return reduce(or_, all_flags)


@unique
class CommandCategory(Flag):
    GENERAL = auto()
    ADMINTOOLS = auto()
    DEVTOOLS = auto()
    TEAMTOOLS = auto()
    META = auto()
    NOTIMPLEMENTED = auto()

    @classmethod
    def _by_name(cls, in_value: str):
        for name, value in cls.__members__.items():
            if name.casefold() == in_value.casefold():
                return cls(value)
        raise ValueError(f"'{in_value}' is not a permitted value for '{cls.__name__}'")

    @classmethod
    def deserialize(cls, value):
        _out = None
        if isinstance(value, list):
            for subvalue in value:
                if _out is None:
                    _out = cls._by_name(subvalue)
                else:
                    _out |= cls._by_name(subvalue)
        elif isinstance(value, str):
            if '|' in value:
                return cls.deserialize(value.split('|'))
            _out = cls._by_name(value)
        return _out

    @property
    def description(self):
        description_map = {CommandCategory.GENERAL: "Default Category for Commands.",
                           CommandCategory.ADMINTOOLS: "Commands that are intended to help admins with their daily tasks.",
                           CommandCategory.DEVTOOLS: "Commands inteded as helpers for the Dev Team",
                           CommandCategory.TEAMTOOLS: "A variety of commands, each of which should be helpful to at least one of the Teams",
                           CommandCategory.META: "Commands that deal with the configuration or maintanance of the Bot itself",
                           CommandCategory.NOTIMPLEMENTED: "NOT YET IMPLEMENTED!"}
        return description_map.get(self, 'NA')

    @property
    def flags(self):
        _out = []
        for member in self.__class__.__members__.values():
            if member in self:
                _out.append(member)
        return _out

    def serialize(self):
        return [flag.name for flag in self.flags]

    def visibility_check(self, in_roles):
        if self is CommandCategory.NOTIMPLEMENTED:
            return False
        visibility_map = {CommandCategory.GENERAL: ['all'],
                          CommandCategory.ADMINTOOLS: ['admin', 'admin lead'],
                          CommandCategory.DEVTOOLS: ['admin', 'admin lead', 'dev helper', 'template helper', 'dev team', 'dev team lead'],
                          CommandCategory.TEAMTOOLS: ['admin', 'admin lead'],
                          CommandCategory.META: ['admin', 'admin lead']}

        return any(role in visibility_map.get(self) for role in in_roles)
