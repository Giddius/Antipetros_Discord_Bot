"""
[summary]

[extended_summary]
"""

# region [Imports]

import gc
import os
import unicodedata
from typing import Callable, Callable
from functools import lru_cache, partial
import inspect
import discord
from discord.ext import commands, tasks
from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name, get_all_lexers, guess_lexer
from pygments.formatters import HtmlFormatter, ImageFormatter
from pygments.styles import get_style_by_name, get_all_styles
from pygments.filters import get_all_filters
import gidlogger as glog
from antipetros_discordbot.utility.gidtools_functions import pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.pygment_styles import DraculaStyle

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class SourceCodeProvider:
    repo_base_url = os.getenv('REPO_BASE_URL')
    wiki_base_url = os.getenv('WIKI_BASE_URL')
    base_folder_name = 'antipetros_discordbot'
    code_highlighter_style = DraculaStyle

    def get_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.get, command)

    def get(self, command: commands.Command, typus: str):
        typus = typus.casefold()
        if typus == "image":
            return self.source_code_image(command)
        if typus == "link":
            return self.github_line_link(command)
        if typus == "wiki_link":
            return self.github_wiki_link(command)

    @staticmethod
    def line_numbers(command: commands.Command) -> tuple:
        source_lines = inspect.getsourcelines(command.callback)
        start_line_number = source_lines[1]
        code_length = len(source_lines[0])
        code_line_numbers = tuple(range(start_line_number, start_line_number + code_length))
        return code_line_numbers

    def github_line_link(self, command: commands.Command) -> str:
        rel_path = self.antipetros_repo_rel_path(inspect.getsourcefile(command.cog.__class__))
        code_line_numbers = self.line_numbers(command)
        full_path = '/'.join([self.repo_base_url, rel_path, f'#L{min(code_line_numbers)}-L{max(code_line_numbers)}'])
        return full_path

    def github_wiki_link(self, command: commands.Command) -> str:
        return '/'.join([self.wiki_base_url, command.name])

    @lru_cache
    def antipetros_repo_rel_path(self, in_path: str) -> str:
        in_path = pathmaker(in_path)
        in_path_parts = in_path.split('/')
        while in_path_parts[0] != self.base_folder_name:
            _ = in_path_parts.pop(0)
        return pathmaker(*in_path_parts)

    def source_code_image(self, command: commands.Command) -> bytes:
        rel_path = self.antipetros_repo_rel_path(inspect.getsourcefile(command.cog.__class__))
        raw_source_code = f'\t# {rel_path}\n\n' + inspect.getsource(command.callback)

        image = highlight(raw_source_code, PythonLexer(), ImageFormatter(style=self.code_highlighter_style,
                                                                         font_name='Fira Code',
                                                                         line_number_start=min(self.line_numbers(command)),
                                                                         line_number_bg="#2f3136",
                                                                         line_number_fg="#ffffff",
                                                                         line_number_chars=3,
                                                                         line_pad=5,
                                                                         font_size=20,
                                                                         line_number_bold=True))
        return image


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
