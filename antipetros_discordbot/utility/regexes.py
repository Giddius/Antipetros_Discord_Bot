# * Standard Library Imports -->
# * Standard Library Imports ---------------------------------------------------------------------------->
import re

TIME_REGEX = re.compile(r"(?P<hour>[012\s]?\d).(?P<minute>[0123456]\d).(?P<second>[0123456]\d)")
DATE_REGEX = re.compile(r"(?P<year>\d\d\d\d).(?P<month>\d+?).(?P<day>\d+)")
LOG_NAME_DATE_TIME_REGEX = re.compile(r"(?P<year>\d\d\d\d).(?P<month>\d+?).(?P<day>\d+).(?P<hour>[012\s]?\d).(?P<minute>[0123456]\d).(?P<second>[0123456]\d)")
