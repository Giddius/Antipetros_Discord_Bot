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
from gidappdata import AppDataAccessor
# endregion [Imports]
from quart import Quart, render_template, request, url_for, send_from_directory
from discord.ext import ipc
from base64 import b64encode
load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\antipetros_discordbot\token.env")

app = Quart(__name__)
ipc_client = ipc.Client(
    secret_key=os.getenv("IPC_SECRET_KEY")
)  # secret_key must be the same as your server
APPDATA = None


async def get_appdata():
    global APPDATA
    if APPDATA is None:

        appdata_accessor_kwargs = await ipc_client.request("get_appdata_accessor_kwargs", data="")
        APPDATA = AppDataAccessor(**appdata_accessor_kwargs)
    return APPDATA

ImageItem = namedtuple("ImageItem", ["name", "path", "alt_text", "title_text"])


@app.route('/uploads/<path:filename>')
async def gif_files(filename):
    appdata = await get_appdata()
    return await send_from_directory(APPDATA['gifs'], filename, as_attachment=False)


@ app.route("/")
async def index():

    antipetros_image = ImageItem("AntiPetros.png", url_for("static", filename="images/AntiPetros.png"), "AntiPetros", "AntiPetrosBot Avatar")
    return await render_template('home.html', antipetros_image=antipetros_image)


@ app.route("/command_list")
async def command_list():
    await asyncio.wait_for(get_appdata(), timeout=None)
    command_data = await ipc_client.request('get_command_list', data="")

    tables = {cog_name: tabulate(value, tablefmt='html') for cog_name, value in command_data.items()}
    gif_dict = await ipc_client.request('get_gifs', data="")

    gifs = [ImageItem(image_name, pathmaker(image_path), image_name, image_name.split('.')[0].title()) for image_name, image_path in gif_dict.items()]

    return await render_template('command_list.html', tables=tables, gifs=gifs)


if __name__ == "__main__":

    app.run(debug=True)
