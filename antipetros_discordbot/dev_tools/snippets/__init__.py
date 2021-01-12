import os

SNIPPETS_DIR = os.path.abspath(os.path.dirname(__file__))
if os.path.islink(SNIPPETS_DIR) is True:

    SNIPPETS_DIR = os.readlink(SNIPPETS_DIR).replace('\\\\?\\', '')
