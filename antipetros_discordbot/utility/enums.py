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
