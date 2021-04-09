# region[Imports]

import os
import subprocess
import shutil
import sys
from inspect import getmembers, isclass, isfunction
from pprint import pprint, pformat
from typing import Union, Dict, Set, List, Tuple
from datetime import tzinfo, datetime, timezone, timedelta
from icecream import ic
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

from tabulate import tabulate

# endregion [Imports]
from quart import Quart, render_template
from discord.ext import ipc
load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\antipetros_discordbot\token.env")

app = Quart(__name__)
ipc_client = ipc.Client(
    secret_key=os.getenv("IPC_SECRET_KEY")
)  # secret_key must be the same as your server

ImageItem = namedtuple("ImageItem", ["name", "path", "alt_text", "title_text"])


@app.route("/")
async def index():
    image = ImageItem('AntiPetros.png', pathmaker('images', 'AntiPetros.png'), "AntiPetros-Bot Avatar", 'AntiPetros-Bot Avatar')
    base_bot_info = await ipc_client.request("get_base_bot_info")
    table = [["Creator", "Giddi"]]
    for key, value in base_bot_info.items():
        if key not in ['intents', 'role_names']:
            table.append([key, value])
    the_table = tabulate(table, tablefmt='unsafehtml')
    return await render_template('home.html', image=image)


if __name__ == "__main__":
    app.run(debug=True)
