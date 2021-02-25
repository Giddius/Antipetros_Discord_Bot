from discord.ext.commands import Command
from antipetros_discordbot.utility.gidtools_functions import loadjson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from typing import List
import os


APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')


def _get_custom_aliases(command_name: str) -> List[str]:
    """
    Looks up the custom aliases from the json file and retrieves them.

    Args:
    ------
        command_name :class:`str`: Name of the command.

    Returns:
        :class:`List[str]`: Custom Aliases.
    """
    file = APPDATA['command_aliases.json']
    if os.path.isfile(file) is False:
        return []
    data = loadjson(file)
    return data.get(command_name, [])


def _default_alias_maker(command_name: str) -> List[str]:
    """
    Modifies command name, to create default aliases by replacing '_' with chars specified in the BASE_CONFIG.

    Args:
    -----
        command_name :class:`str`: Name of the command.

    Returns:
    ---------
        :class:`list[str]`: modified aliases.
    """
    default_alias_chars = BASE_CONFIG.retrieve('command_meta', 'base_alias_replacements', typus=List[str], direct_fallback='-')
    default_aliases = []
    for char in default_alias_chars:
        mod_name = command_name.replace('_', char)
        if mod_name not in default_aliases and mod_name != command_name:
            default_aliases.append(mod_name)
    return default_aliases


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
        cls = Command

    def decorator(func):
        command_name = func.__name__ if name is None else name

        aliases = _default_alias_maker(command_name) + _get_custom_aliases(command_name=command_name) + attrs.get('aliases', [])
        aliases = list(set(map(lambda x: x.casefold(), aliases)))

        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, aliases=aliases, **{key: value for key, value in attrs.items() if key != 'aliases'})

    return decorator
