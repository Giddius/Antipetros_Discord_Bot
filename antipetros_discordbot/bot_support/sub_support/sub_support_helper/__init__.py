# * Standard Library Imports ---------------------------------------------------------------------------->
import os

SUB_SUPPORT_HELPER_DIR = os.path.abspath(os.path.dirname(__file__))
if os.path.islink(SUB_SUPPORT_HELPER_DIR) is True:

    SUB_SUPPORT_HELPER_DIR = os.readlink(SUB_SUPPORT_HELPER_DIR).replace('\\\\?\\', '')


for file in [file for file in os.scandir(SUB_SUPPORT_HELPER_DIR) if file.is_file() and file.name != '__init__.py']:
    as_module_name = file.name.removesuffix('.py')
    import_stmt = f"from .{as_module_name} import *"
    exec(import_stmt)
