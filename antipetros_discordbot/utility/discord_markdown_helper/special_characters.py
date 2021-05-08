ZERO_WIDTH = '\u200b'
SPECIAL_SPACE = '\u00A0'
SPECIAL_SPACE_2 = '\u2003'


class ListMarker:
    hand = '☛'
    star = '⋆'
    circle_star = '⍟'
    circle_small = '∘'
    square_black = '∎'
    triangle = '⊳'
    triangle_black = '▶'
    hexagon = '⎔'
    hexagon_double = '⏣'
    logic = '⊸'
    arrow = '→'
    arrow_down = '↳'
    arrow_up = '↱'
    arrow_big = '⇒'
    arrow_curved = '↪'
    arrow_two = '⇉'
    arrow_three = '⇶'
    bullet = '•'
    vertical_bar = '▏'
    vertical_bar_long = '│'
    vertical_bar_thick = '┃'
    connector_round = '╰'

    @classmethod
    def make_list(cls, in_data, symbol=None, indent: int = 0, formatting: str = None) -> str:
        symbol = cls.bullet if symbol is None else symbol
        indent_unit = SPECIAL_SPACE * 8
        formatting = '' if formatting is None else formatting
        return '\n'.join(f"{formatting}{ZERO_WIDTH}{indent_unit*indent}{symbol} {item}{formatting}" for item in in_data)

    @classmethod
    def _column_symbol_generator(cls, amount_columns: int, seperator: str):
        while True:
            for i in range(amount_columns - 1):
                yield seperator
            yield "\n"

    @classmethod
    def make_column_list(cls, in_data, symbol=None, amount_columns: int = 2, seperator: str = ', '):
        col_gen = cls._column_symbol_generator(amount_columns, seperator)
        return ''.join(f"{symbol} {item}{next(col_gen)}" for item in in_data)


class Seperators:
    basic = '-'
    thick = '█'
    double = '═'
    line = '─'

    @classmethod
    def make_line(cls, character_name: str = 'line', amount: int = 15):
        character = getattr(cls, character_name)
        return character * amount
