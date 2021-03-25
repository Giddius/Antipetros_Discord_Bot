from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH


def discord_key_value_text(key: str, value: str, width: int = 25, specifier: str = '=', seperator: str = f"{ZERO_WIDTH} "):
    new_text = f"{key} {specifier}{'$%$'*(width-len(key))}{value}"
    return new_text.replace('$%$', seperator)


def embed_hyperlink(name, url):
    return f"[{name}]({url})🔗"
