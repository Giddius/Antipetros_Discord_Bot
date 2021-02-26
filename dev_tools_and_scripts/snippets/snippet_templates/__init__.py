# * Standard Library Imports -->
# * Standard Library Imports ---------------------------------------------------------------------------->
import os

SNIPPETS_TEMPLATES_DIR = os.path.abspath(os.path.dirname(__file__))
if os.path.islink(SNIPPETS_TEMPLATES_DIR) is True:

    SNIPPETS_TEMPLATES_DIR = os.readlink(SNIPPETS_TEMPLATES_DIR).replace('\\\\?\\', '')
