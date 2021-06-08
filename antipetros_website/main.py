# region[Imports]

import os
import subprocess
import shutil
import sys
import asyncio
from inspect import getmembers, isclass, isfunction
from pprint import pprint, pformat
from typing import Union, Dict, Set, List, Tuple
from datetime import tzinfo, datetime, timezone, timedelta
import re
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import random
from functools import wraps, lru_cache, singledispatch, total_ordering, partial
from contextlib import contextmanager
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from enum import Enum, unique, Flag, auto
from rich import print as rprint, inspect as rinspect
from time import time, sleep
from timeit import Timer, timeit
from textwrap import dedent
from antipetros_discordbot.utility.gidtools_functions import writejson, writeit, readit, pathmaker, loadjson, clearit, pickleit, get_pickled


from gidappdata import AppDataAccessor
from quart import Quart, render_template, request, url_for, send_from_directory
from base64 import b64encode
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
# endregion [Imports]

app = Quart(__name__)
APPDATA = ParaStorageKeeper.get_appdata()


ImageItem = namedtuple("ImageItem", ["name", "path", "alt_text", "title_text"])


@app.route('/uploads/<path:filename>')
async def gif_files(filename):
    return await send_from_directory(APPDATA['website_images'], filename, as_attachment=False)


@ app.route("/")
async def index():

    antipetros_image = ImageItem("AntiPetros.png", url_for("static", filename="images/AntiPetros.png"), "AntiPetros", "AntiPetrosBot Avatar")
    return await render_template('home.html', antipetros_image=antipetros_image)


if __name__ == "__main__":

    app.run(debug=True)
