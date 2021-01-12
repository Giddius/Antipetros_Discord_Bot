# region [Imports]

# * Standard Library Imports -->
from enum import Enum, Flag, auto
from datetime import datetime
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
