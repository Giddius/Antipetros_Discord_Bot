
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from typing import List, Union, Tuple
import os
from discord.ext import commands, tasks, flags, ipc
import inspect
import re
from antipetros_discordbot.utility.exceptions import CommandIdNotSetError

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')


class AliasProvider:
    alias_data_file = pathmaker(APPDATA['documentation'], 'command_aliases.json')
    base_config = ParaStorageKeeper.get_config('base_config')

    def __init__(self, command_name: str, extra_aliases: Union[List, Tuple] = None):
        self.command_name = command_name
        self.extra_aliases = [] if extra_aliases is None else extra_aliases

    @property
    def default_alias_chars(self):
        return self.base_config.retrieve('command_meta', 'base_alias_replacements', typus=List[str], direct_fallback='-')

    @property
    def custom_alias_data(self):
        if os.path.isfile(self.alias_data_file) is False:
            return {}
        return loadjson(self.alias_data_file)

    @property
    def default_aliases(self):
        default_aliases = []
        for char in self.default_alias_chars:
            mod_name = self.command_name.replace('_', char)
            if mod_name not in default_aliases and mod_name != self.command_name:
                default_aliases.append(mod_name)
        return default_aliases

    @property
    def custom_aliases(self):
        return self.custom_alias_data.get(self.command_name, [])

    @property
    def aliases(self):
        aliases = self.default_aliases + self.custom_aliases + self.extra_aliases
        return list(set(map(lambda x: x.casefold(), aliases)))


class AntiPetrosCommand(commands.Command):
    meta_data_file = pathmaker(APPDATA['documentation'], 'command_help_data.json')
    bot_mention_regex = re.compile(r"\@AntiPetros|\@AntiDEVtros", re.IGNORECASE)
    gif_folder = APPDATA['gifs']

    def __init__(self, func, **kwargs):
        self.name = func.__name__ if kwargs.get("name") is None else kwargs.get("name")
        self.alias_provider = AliasProvider(self.name, kwargs.get("aliases"))
        super().__init__(func, **kwargs)

    @property
    def full_id(self):
        return self._get_full_id()

    @property
    def aliases(self):
        return self.alias_provider.aliases

    @aliases.setter
    def aliases(self, value):
        pass

    @property
    def meta_data(self):
        if os.path.isfile(self.meta_data_file) is False:
            return {}
        return loadjson(self.meta_data_file).get(self.name, {})

    @property
    def help(self):
        return inspect.cleandoc(self.meta_data.get('help', inspect.getdoc(self.callback)))

    @help.setter
    def help(self, value):
        pass

    @property
    def brief(self):
        return self.meta_data.get('brief', None)

    @brief.setter
    def brief(self, value):
        pass

    @property
    def description(self):
        return inspect.cleandoc(self.meta_data.get('description', ''))

    @description.setter
    def description(self, value):
        pass

    @property
    def short_doc(self):
        short_doc = self.meta_data.get('short_doc', None)
        if short_doc is not None:
            return short_doc
        if self.brief is not None:
            return self.brief
        if self.help is not None:
            return self.help
        return ''

    @short_doc.setter
    def short_doc(self, value):
        pass

    @property
    def usage(self):
        return self.meta_data.get('usage', None)

    @usage.setter
    def usage(self, value):
        pass

    @property
    def example(self):
        example = self.meta_data.get('example', None)
        return example

    @example.setter
    def example(self, value):
        meta_data = self.get_full_metadata()
        meta_data[self.name]['example'] = value

    @property
    def gif(self):
        for gif_file in os.scandir(self.gif_folder):
            if gif_file.is_file() and gif_file.name.casefold() == f"{self.name}_command.gif".casefold():
                return pathmaker(gif_file.path)
        return None

    def get_full_metadata(self):
        if os.path.exists(self.meta_data_file) is False:
            return {self.name: {}}
        return loadjson(self.meta_data_file)

    def save_full_metadata(self, data):
        writejson(data, self.meta_data_file)


class AntiPetrosFlagCommand(flags.FlagCommand, AntiPetrosCommand):
    pass


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
        cls = AntiPetrosCommand

    def decorator(func):
        return cls(func, name=name, **attrs)

    return decorator
