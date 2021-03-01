# * Standard Library Imports -->
# * Standard Library Imports ---------------------------------------------------------------------------->
import os

SUPPORT_DIR = os.path.abspath(os.path.dirname(__file__))
if os.path.islink(SUPPORT_DIR) is True:

    SUPPORT_DIR = os.readlink(SUPPORT_DIR).replace('\\\\?\\', '')


from .bot_supporter import BotSupporter
