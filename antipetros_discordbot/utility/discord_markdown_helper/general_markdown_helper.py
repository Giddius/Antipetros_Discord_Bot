from collections import UserString


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


if __name__ == '__main__':
    pass
