import re
import textwrap

TIME_REGEX = re.compile(r"(?P<hour>[012\s]?\d).(?P<minute>[0123456]\d).(?P<second>[0123456]\d)")
DATE_REGEX = re.compile(r"(?P<year>\d\d\d\d).(?P<month>\d+?).(?P<day>\d+)")
LOG_NAME_DATE_TIME_REGEX = re.compile(r"(?P<year>\d\d\d\d).(?P<month>\d+?).(?P<day>\d+).(?P<hour>[012\s]?\d).(?P<minute>[0123456]\d).(?P<second>[0123456]\d)")


DATETIME_REGEX = re.compile(textwrap.dedent(r'''
                                            (?P<year>\d\d\d\d)
                                            .*?
                                            (?P<month>[01]\d)
                                            .*?
                                            (?P<day>[0123]\d)
                                            .*?
                                            (?P<hour>[012]\d)
                                            .*?
                                            (?P<minute>[0-6]\d)
                                            .*?
                                            (?P<second>[0-6]\d)
                                            ''').strip(), re.VERBOSE)

LOG_SPLIT_REGEX = re.compile(r"\n(?=\d\d\d\d.*?[01]\d.*?[0123]\d.*?[012]\d.*?[0-6]\d.*?[0-6]\d)")

ANTISTASI_MARKER_REGEX = re.compile(r".*?\[Antistasi\]\s?\|")

LOG_LEVEL_REGEX = re.compile(r"\|\s?(?P<log_level>DEBUG|INFO|VERBOSE|ERROR)\s?\|")

LOGGED_FUNCTION_REGEX = re.compile(r"\|\s?(?:DEBUG|INFO|VERBOSE|ERROR)\s?\|\s(?P<logged_function>.*?) \|")

MESSAGE_REGEX = re.compile(r"\|\s?(?P<message>[^\|]*?)$", re.DOTALL)

MOD_TABLE_START_REGEX = re.compile(r"^[\d\s]\d.[0123456]\d.[0123456]\d\s*?name\s?\|\s*?modDir\s?\|.*?\n[\d\s]\d.[0123456]\d.[0123456]\d.*?\-+", re.MULTILINE | re.IGNORECASE)

MOD_TABLE_END_REGEX = re.compile(r"^[\d\s]\d.[0123456]\d.[0123456]\d\s*?\=+\n", re.MULTILINE)

MOD_TABLE_LINE_REGEX = re.compile(r"""^[\d\s]\d.[0123456]\d.[0123456]\d\s*?
                                  (?P<mod_name>.*?)\s\|
                                  \s*?
                                  (?P<mod_dir>.*?)\s\|
                                  \s*?
                                  (?P<default>.*?)\s\|
                                  \s*?
                                  (?P<official>.*?)\s\|
                                  \s*?
                                  (?P<origin>.*?)\s\|
                                  \s*?
                                  (?P<hash>.*?)\s\|
                                  \s*?
                                  (?P<hashshort>.*?)\s\|
                                  \s*?
                                  (?P<fullpath>.*)""", re.VERBOSE)


COMMAND_TEXT_FILE_REGEX = re.compile(r"\n?(?P<key_words>[\w\s]+).*?\=.*?(?P<value_words>.*?(?=(?:\n[^\n]*?\=)|$))", re.DOTALL)