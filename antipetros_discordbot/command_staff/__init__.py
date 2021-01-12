import os


COMMAND_STAFF_DIR = os.path.abspath(os.path.dirname(__file__))
if os.path.islink(COMMAND_STAFF_DIR) is True:

    COMMAND_STAFF_DIR = os.readlink(COMMAND_STAFF_DIR).replace('\\\\?\\', '')


from .command_staff import *
from .staff_error_handler import *
from .staff_invoke_statistician import *
from .staff_time_keeper import *
from .staff_chan_statistician import *
from .staff_regex_keeper import *
from .staff_color_keeper import *
