"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os

# * Third Party Imports --------------------------------------------------------------------------------->
import discord

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->

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


class BlacklistedUserItem:

    def __init__(self, warden, user_id: int, user_name: str, notified: bool = False, command_called: int = 0):
        self.warden = warden
        self.id = user_id
        self.name = user_name
        self._command_called = command_called
        self.notified = notified

    @property
    def command_called(self):
        return self._command_called

    def tried_calling(self):
        self._command_called += 1

    async def unblacklist(self):
        await self.warden.unblacklist_user(self)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, int):
            return other == self.id
        elif isinstance(other, str):
            return other == self.name
        elif isinstance(other, BlacklistedUserItem):
            return other is self
        elif isinstance(other, discord.Member):
            return other.id == self.id
        elif isinstance(other, discord.User):
            return other.id == self.id

    def __hash__(self) -> int:
        return hash(self.notified) + hash(self._command_called) + hash(self.id) + hash(self.name)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'command_called': self._command_called, 'notified':self.notified}

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]