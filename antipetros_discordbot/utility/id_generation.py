
# region [Imports]

import os
import sys
import shutil
import re
import random
from antipetros_discordbot.cogs import category_ids
# endregion[Imports]


def make_full_cog_id(in_dir_path, in_cog_id: int):
    category_data = category_ids()
    cog_folder = os.path.basename(in_dir_path)
    cog_cat_id = {key.split('.')[-1].casefold(): value for key, value in category_data.items()}.get(cog_folder.casefold())
    full_id_string = str(cog_cat_id) + str(in_cog_id)
    return int(full_id_string)
