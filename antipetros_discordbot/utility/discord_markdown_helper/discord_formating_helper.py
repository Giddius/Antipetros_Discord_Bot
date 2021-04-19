from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, SPECIAL_SPACE, Seperators


def discord_key_value_text(key: str, value: str, width: int = 25, specifier: str = '=', seperator: str = f"{ZERO_WIDTH} "):
    new_text = f"{key} {specifier}{'$%$'*(width-len(key))}{value}"
    return new_text.replace('$%$', seperator)


def embed_hyperlink(name, url):
    return f"[{name}]({url})🔗"


def make_box(in_text: str):
    lines = in_text.splitlines()
    max_length = max([len(line) + 10 for line in lines]) - 2
    pre_spacing = SPECIAL_SPACE * 8

    mod_lines = map(lambda x: f"{SPECIAL_SPACE*8}{x}", lines)
    boxed_text = "┌" + Seperators.make_line("line", max_length // 2) + '┐\n'
    boxed_text += '\n'.join(mod_lines) + '\n'
    boxed_text += "└" + Seperators.make_line("line", max_length // 2) + "┘"
    return boxed_text
