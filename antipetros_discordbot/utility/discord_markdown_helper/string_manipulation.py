
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


def better_shorten(in_text: str, max_length: int, shorten_side: str = "right", placeholder: str = '...', clean_before: bool = True, ensure_space_around_placeholder: bool = False) -> str:
    if shorten_side.casefold() not in {"left", "right"}:
        raise ValueError(shorten_side)

    if ensure_space_around_placeholder is True:
        placeholder = f" {placeholder.strip()}" if shorten_side == "right" else f"{placeholder.strip()} "

    max_length = max_length - len(placeholder)

    if clean_before is True:
        in_text = clean_whitespace(in_text, replace_newline=False)
    new_text_lines = []

    lines = in_text.splitlines() if shorten_side == 'right' else list(reversed(in_text.splitlines()))

    while lines and (sum([len(new_text_line) for new_text_line in new_text_lines])) + len(lines[0]) <= max_length:
        new_text_lines.append(lines.pop(0))

    if not lines:
        return '\n'.join(new_text_lines).strip() if shorten_side == 'right' else '\n'.join(reversed(new_text_lines)).strip()

    last_new_line = []
    words = lines[0].split(' ') if shorten_side == 'right' else list(reversed(lines[0].split(' ')))
    while sum([len(new_text_line) for new_text_line in new_text_lines]) + sum(len(new_word) for new_word in last_new_line) + len(words[0]) <= max_length:
        last_new_line.append(words.pop(0))
    last_new_line = ' '.join(last_new_line).strip() if shorten_side == 'right' else ' '.join(reversed(last_new_line)).strip()
    new_text_lines.append(last_new_line)
    return '\n'.join(new_text_lines).strip() + placeholder if shorten_side == 'right' else placeholder + '\n'.join(reversed(new_text_lines)).strip()


async def async_better_shorten(in_text: str, max_length: int, shorten_side: str = "right", placeholder: str = '...', clean_before: bool = True, ensure_space_around_placeholder: bool = False) -> str:
    if shorten_side.casefold() not in {"left", "right"}:
        raise ValueError(shorten_side)

    if ensure_space_around_placeholder is True:
        placeholder = f" {placeholder.strip()}" if shorten_side == "right" else f"{placeholder.strip()} "

    max_length = max_length - len(placeholder)

    if clean_before is True:
        in_text = await asyncio.to_thread(clean_whitespace, in_text, replace_newline=False)
    new_text_lines = []

    lines = in_text.splitlines() if shorten_side == 'right' else list(reversed(in_text.splitlines()))

    while lines and (sum([len(new_text_line) for new_text_line in new_text_lines])) + len(lines[0]) <= max_length:
        new_text_lines.append(await asyncio.sleep(0, lines.pop(0)))

    if not lines:
        return '\n'.join(new_text_lines).strip() if shorten_side == 'right' else '\n'.join(reversed(new_text_lines)).strip()

    last_new_line = []
    words = lines[0].split(' ') if shorten_side == 'right' else list(reversed(lines[0].split(' ')))
    while sum([len(new_text_line) for new_text_line in new_text_lines]) + sum(len(new_word) for new_word in last_new_line) + len(words[0]) <= max_length:
        last_new_line.append(await asyncio.sleep(0, words.pop(0)))
    last_new_line = ' '.join(last_new_line).strip() if shorten_side == 'right' else ' '.join(reversed(last_new_line)).strip()
    new_text_lines.append(await asyncio.sleep(0, last_new_line))
    return '\n'.join(new_text_lines).strip() + placeholder if shorten_side == 'right' else placeholder + '\n'.join(reversed(new_text_lines)).strip()


def alternative_better_shorten(in_text: str, max_length: int, shorten_side: str = "right", placeholder: str = '...', clean_before: bool = True, ensure_space_around_placeholder: bool = False, split_on: str = '\s|\n') -> str:
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
