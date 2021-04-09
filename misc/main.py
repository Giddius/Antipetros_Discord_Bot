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
from flask import Flask, request, render_template, redirect, url_for
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from tabulate import tabulate
# endregion [Imports]
load_dotenv('flask_keys.env')
load_dotenv('../antipetros_discordbot/token.env')
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY').encode('utf-8')
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"


app.config["DISCORD_CLIENT_ID"] = 752943453624729640    # Discord client ID.
app.config["DISCORD_CLIENT_SECRET"] = os.getenv('CLIENT_SECRETS')                # Discord client secret.
app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback"                 # URL to your callback endpoint.
app.config["DISCORD_BOT_TOKEN"] = os.getenv('DISCORD_TOKEN')                    # Required to access BOT resources.

discord = DiscordOAuth2Session(app)


HYPERLINK = '<a href="{}">{}</a>'


@app.route("/")
def index():
    if not discord.authorized:
        return f"""
        {HYPERLINK.format(url_for(".login"), "Login")} <br />
        {HYPERLINK.format(url_for(".login_with_data"), "Login with custom data")} <br />
        {HYPERLINK.format(url_for(".invite_bot"), "Invite Bot with permissions 8")} <br />
        {HYPERLINK.format(url_for(".invite_oauth"), "Authorize with oauth and bot invite")}
        """

    return f"""
    {HYPERLINK.format(url_for(".me"), "@ME")}<br />
    {HYPERLINK.format(url_for(".logout"), "Logout")}<br />
    {HYPERLINK.format(url_for(".user_guilds"), "My Servers")}<br />
    {HYPERLINK.format(url_for(".add_to_guild", guild_id=475549041741135881), "Add me to 475549041741135881.")}
    """


@app.route("/login/")
def login():
    return discord.create_session()


@app.route("/login-data/")
def login_with_data():
    return discord.create_session(data=dict(redirect="/me/", coupon="15off", number=15, zero=0, status=False))


@app.route("/invite-bot/")
def invite_bot():
    return discord.create_session(scope=["bot"], permissions=8, guild_id=464488012328468480, disable_guild_select=True)


@app.route("/invite-oauth/")
def invite_oauth():
    return discord.create_session(scope=["bot", "identify"], permissions=8)


@app.route("/callback/")
def callback():
    data = discord.callback()
    redirect_to = data.get("redirect", "/")
    return redirect(redirect_to)


@app.route("/me/")
def me():
    user = discord.fetch_user()
    return f"""
<html>
<head>
<title>{user.name}</title>
</head>
<body><img src='{user.avatar_url or user.default_avatar_url}' />
<p>Is avatar animated: {str(user.is_avatar_animated)}</p>
<p>Is avatar animated: {str(user.id)}</p>
<a href={url_for("my_connections")}>Connections</a>
<br />
</body>
</html>
"""


@app.route("/me/guilds/")
def user_guilds():
    guilds = discord.fetch_guilds()
    return "<br />".join([f"[ADMIN] {g.name}" if g.permissions.administrator else g.name for g in guilds])


@app.route("/add_to/<int:guild_id>/")
def add_to_guild(guild_id):
    user = discord.fetch_user()
    return user.add_to_guild(guild_id)


@app.route("/me/connections/")
def my_connections():
    user = discord.fetch_user()
    connections = discord.fetch_connections()
    return f"""
<html>
<head>
<title>{user.name}</title>
</head>
<body>
{str([f"{connection.name} - {connection.type}" for connection in connections])}
</body>
</html>
"""


@app.route("/logout/")
def logout():
    discord.revoke()
    return redirect(url_for(".index"))


@app.route("/secret/")
@requires_authorization
def secret():
    return os.urandom(16)


if __name__ == "__main__":
    app.run(debug=True)
