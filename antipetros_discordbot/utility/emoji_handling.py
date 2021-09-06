from emoji.unicode_codes.en import EMOJI_ALIAS_UNICODE_ENGLISH
from emoji import demojize, emoji_count
from contextlib import contextmanager
import random
from string import ascii_lowercase

CHECK_MARK_BUTTON_EMOJI = "✅"

CROSS_MARK_BUTTON_EMOJI = "❎"

CANCEL_EMOJI = "🛑"
FINISHED_EMOJI = "🆗"
NUMERIC_EMOJIS = ["1️⃣",
                  "2️⃣",
                  "3️⃣",
                  "4️⃣",
                  "5️⃣",
                  "6️⃣",
                  "7️⃣",
                  "8️⃣",
                  "9️⃣",
                  "🔟",
                  ]

ALPHABET_EMOJIS = ["🇦",
                   "🇧",
                   "🇨",
                   "🇩",
                   "🇪",
                   "🇫",
                   "🇬",
                   "🇭",
                   "🇮",
                   "🇯",
                   "🇰",
                   "🇱",
                   "🇲",
                   "🇳",
                   "🇴",
                   "🇵",
                   "🇶",
                   "🇷",
                   "🇸",
                   "🇹",
                   "🇺",
                   "🇻",
                   "🇼",
                   "🇽",
                   "🇾",
                   "🇿"]


EMOJI_ALPHABET_MAP = {x[0]: x[1] for x in zip(ascii_lowercase, ALPHABET_EMOJIS)}


def letter_to_emoji(letter: str):
    return EMOJI_ALPHABET_MAP[letter.casefold()]


def is_unicode_emoji(data: str):
    return emoji_count(data) > 0


@contextmanager
def str_random(string: str):
    random.seed(string)
    yield
    random.seed(None)


def create_emoji_id(in_emoji):
    with str_random(in_emoji):
        return random.randint(10000000, 99999999)


def create_emoji_custom_name(in_emoji):
    d_emoji = demojize(in_emoji)
    return f"<{d_emoji}{create_emoji_id(d_emoji)}>"


def normalize_emoji(in_emoji):
    return demojize(in_emoji).strip(':')


def get_emoji_unicode(in_emoji_name):
    for alias, unicode_data in EMOJI_ALIAS_UNICODE_ENGLISH.items():
        if normalize_emoji(alias) == in_emoji_name:
            return unicode_data
