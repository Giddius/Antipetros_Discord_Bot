
# region [Imports]


import textwrap
import re
import asyncio

# endregion[Imports]


SPACE_CLEANING_REGEX = re.compile(r" +")
NEWLINE_CLEANING_REGEX = re.compile(r"\n+")


def clean_whitespace(in_text: str, replace_newline: bool = False) -> str:
    cleaned_text = SPACE_CLEANING_REGEX.sub(' ', in_text)
    if replace_newline is True:
        cleaned_text = NEWLINE_CLEANING_REGEX.sub(' ', cleaned_text)
    return cleaned_text


def shorten_string(in_text: str, max_length: int, shorten_side: str = "right", placeholder: str = '...', clean_before: bool = True, ensure_space_around_placeholder: bool = False, split_on: str = '\s|\n') -> str:
    if shorten_side.casefold() not in {"left", "right"}:
        raise ValueError(shorten_side)

    if ensure_space_around_placeholder is True:
        placeholder = f" {placeholder.strip()}" if shorten_side == "right" else f"{placeholder.strip()} "

    if clean_before is True:
        in_text = clean_whitespace(in_text, replace_newline=False)

    if len(in_text) <= max_length:
        return in_text

    max_length = max_length - len(placeholder)

    new_text = in_text[:max_length] if shorten_side == 'right' else in_text[-max_length:]
    find_regex = re.compile(split_on)
    last_space_position = list(find_regex.finditer(new_text))

    return new_text[:last_space_position[-1].span()[0]].strip() + placeholder if shorten_side == 'right' else placeholder + new_text[last_space_position[0].span()[0]:].strip()
