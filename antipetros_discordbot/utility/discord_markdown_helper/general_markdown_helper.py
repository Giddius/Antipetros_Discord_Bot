# * Standard Library Imports -->
# * Standard Library Imports ---------------------------------------------------------------------------->
from collections import UserString
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, ListMarker


class AntiPetrosMarkdownBase(UserString):
    def __init__(self, data):
        self.data = f"{self.md_symbol_start}{data}{self.md_symbol_end}"

    @property
    def md_symbol_start(self):
        return self.md_symbol

    @property
    def md_symbol_end(self):
        return self.md_symbol


class Bold(AntiPetrosMarkdownBase):
    def __init__(self, data):
        if isinstance(data, AntiPetrosMarkdownBase) and '*' in data.data:
            self.md_symbol = '***'
            data = data.data.replace('*', '')
        else:
            self.md_symbol = '**'

        super().__init__(data)


class UnderScore(AntiPetrosMarkdownBase):
    def __init__(self, data):
        self.md_symbol = '__'
        super().__init__(data)


class Cursive(AntiPetrosMarkdownBase):
    def __init__(self, data):
        if isinstance(data, AntiPetrosMarkdownBase) and '**' in data.data:
            self.md_symbol = '***'
            data = data.data.replace('**', '')
        else:
            self.md_symbol = '*'
        super().__init__(data)


class LineCode(AntiPetrosMarkdownBase):
    @property
    def md_symbol(self):
        return '`'


class CodeBlock(AntiPetrosMarkdownBase):
    def __init__(self, data, language=None):
        self.language = '' if language is None else language
        self.md_symbol = "```"
        super().__init__(data)

    @property
    def md_symbol_start(self):
        return f"{self.md_symbol}{self.language}\n"

    @property
    def md_symbol_end(self):
        return f"\n{self.md_symbol}"


class BlockQuote(AntiPetrosMarkdownBase):
    def __init__(self, data):
        self.raw_data = data.splitlines()
        self.data = ""
        if len(self.raw_data) == 1:
            self.data = f'{self.md_symbol_start} {self.raw_data[0]}'
        else:
            for line in self.raw_data:
                self.data += f'{self.md_symbol_start} {line}{self.md_symbol_end}'

    @property
    def md_symbol_start(self):
        return ">"

    @property
    def md_symbol_end(self):
        return "\n"


def make_message_list(in_list_data: list, list_marker: str = 'bullet', special_mod=None, empty_lines: int = 0):
    empty_lines = empty_lines + 1
    special_mod = special_mod + ' ' if special_mod is not None else ''
    marker = getattr(ListMarker, list_marker) if hasattr(ListMarker, list_marker) else list_marker
    mod_list_data = [f"{special_mod}{marker} {list_item}" for list_item in in_list_data]
    newlines = '\n' * (empty_lines)
    return newlines.join(mod_list_data)


if __name__ == '__main__':
    pass