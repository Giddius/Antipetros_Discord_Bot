from antipetros_discordbot.utility.regexes import COMMAND_TEXT_FILE_REGEX
from typing import Union


async def parse_command_text_file(in_content: str, command_keywords: Union[list, set, tuple]):
    results = {key: None for key in command_keywords}
    for match_data in COMMAND_TEXT_FILE_REGEX.finditer(in_content):
        if match_data:
            key_word = match_data.group('key_words').strip().casefold()
            if key_word in command_keywords:
                results[key_word] = '\n'.join(line.strip() for line in match_data.group('value_words').splitlines() if not line.startswith('#'))
    return results