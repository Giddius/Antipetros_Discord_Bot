import discord.ext.test as dpytest
from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
import pytest
from dotenv import load_dotenv
import os
import asyncio

load_dotenv(os.path.join(os.getenv('BASE_FOLDER'), 'nextcloud.env'))
load_dotenv(os.path.join(os.getenv('BASE_FOLDER'), 'token.env'))


@pytest.mark.asyncio
async def test_flip_coin():
    bot = AntiPetrosBot(token=os.getenv('ANTIDEVTROS_TOKEN'))
    dpytest.configure(bot)
    await asyncio.sleep(45)
    await dpytest.message("@AntiDEVtros help")
