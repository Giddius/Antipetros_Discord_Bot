import os

TEMPLATES_DIR = os.path.abspath(os.path.dirname(__file__))
if os.path.islink(TEMPLATES_DIR) is True:

    TEMPLATES_DIR = os.readlink(TEMPLATES_DIR).replace('\\\\?\\', '')
