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


class Seperators:
    basic = '-'
    thick = '█'
    double = '═'
    line = '─'

    @classmethod
    def make_line(cls, character_name: str = 'line', amount: int = 15):
        character = getattr(cls, character_name)
        return character * amount
