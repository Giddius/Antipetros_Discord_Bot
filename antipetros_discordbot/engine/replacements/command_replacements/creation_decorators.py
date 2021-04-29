"""
[summary]

[extended_summary]
"""

# region [Imports]

import gc
import os
import unicodedata
import discord
from discord.ext import commands, tasks
import gidlogger as glog
from antipetros_discordbot.utility.general_decorator import universal_log_profiler
from .base_group import AntiPetrosBaseGroup
from .base_command import AntiPetrosBaseCommand

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


def auto_meta_info_command(name=None, cls=None, **attrs):
    """
    EXTENDED_BY_GIDDI
    -----------------
    Automatically gets the following attributes, if not provided or additional to provided:
    - creates default aliases and retrieves custom aliases.

    Base Docstring
    ---------------
    A decorator that transforms a function into a :class:`.Command`
    or if called with :func:`.group`, :class:`.Group`.

    By default the ``help`` attribute is received automatically from the
    docstring of the function and is cleaned up with the use of
    ``inspect.cleandoc``. If the docstring is ``bytes``, then it is decoded
    into :class:`str` using utf-8 encoding.

    All checks added using the :func:`.check` & co. decorators are added into
    the function. There is no way to supply your own checks through this
    decorator.

    Parameters
    -----------
    name: :class:`str`
        The name to create the command with. By default this uses the
        function name unchanged.
    cls
        The class to construct with. By default this is :class:`.Command`.
        You usually do not change this.
    attrs
        Keyword arguments to pass into the construction of the class denoted
        by ``cls``.

    Raises
    -------
    TypeError
        If the function is not a coroutine or is already a command.
    """
    if cls is None:
        cls = AntiPetrosBaseCommand

    def decorator(func):

        return cls(universal_log_profiler(func), name=name, **attrs)

    return decorator


def auto_meta_info_group(name=None, **attrs):
    """EXTENDED_BY_GIDDI
    -----------------
    A decorator that transforms a function into a :class:`.Group`.

    This is similar to the :func:`.command` decorator but the ``cls``
    parameter is set to :class:`Group` by default.

    .. versionchanged:: 1.1
        The ``cls`` parameter can now be passed.
    """

    attrs.setdefault('cls', AntiPetrosBaseGroup)
    return auto_meta_info_command(name=name, **attrs)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
