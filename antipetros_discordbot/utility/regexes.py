import re


TIME_REGEX = re.compile(r"(?P<hour>[012\s]?\d).(?P<minute>[0123456]\d).(?P<second>[0123456]\d)")
DATE_REGEX = re.compile(r"(?P<year>\d\d\d\d).(?P<month>\d+?).(?P<day>\d+)")
