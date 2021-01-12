

# region [Imports]

# * Standard Library Imports -->
import os
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
# * Third Party Imports -->
import aiohttp
import discord
from discord.ext import tasks, commands

# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.enums import RequestStatus
from antipetros_discordbot.utility.named_tuples import LINK_DATA_ITEM
from antipetros_discordbot.utility.sqldata_storager import LinkDataStorageSQLite
from antipetros_discordbot.utility.gidtools_functions import writeit, loadjson, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.embed_helpers import make_basic_embed, EMBED_SYMBOLS
from antipetros_discordbot.utility.misc import save_commands
from antipetros_discordbot.utility.checks import in_allowed_channels
from antipetros_discordbot.cogs import get_aliases
# endregion [Imports]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]
APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
COGS_CONFIG = SupportKeeper.get_config('cogs_config')
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))


# endregion [Constants]

# region [TODO]


# TODO: refractor 'get_forbidden_list' to not use temp directory but send as filestream or so

# TODO: need help figuring out how to best check bad link or how to format/normalize it


# endregion [TODO]


class SaveLinkCog(commands.Cog, command_attrs={"name": "SaveLinkCog"}):

    """
    An extension Cog to let users temporary save links.

    Saved links get posted to a certain channel and deleted after the specified time period from that channel (default in config).
    Deleted links are kept in the bots database and can always be retrieved by fuzzy matched name.

    Checks against a blacklist of urls and a blacklist of words, to not store malicious links.

    """
# region [ClassAttributes]

    # url to blacklist for forbidden_link_list
    blocklist_hostfile_url = "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews-gambling-porn/hosts"
    config_name = 'save_link'

# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.data_storage_handler = LinkDataStorageSQLite()  # composition to make data storage modular, currently set up for an sqlite Database
        self.forbidden_url_words_file = APPDATA['forbidden_url_words.json']
        if self.bot.is_debug:
            save_commands(self)
        self.fresh_blacklist_loop.start()
        self.check_link_best_by_loop.start()

        glog.class_init_notification(log, self)

# endregion [Init]

# region [Setup]

    async def _process_raw_blocklist_content(self, raw_content):
        """
        Process downloaded Blacklist to a list of raw urls.

        Returns:
            set: forbidden_link_list as set for quick contain checks
        """

        _out = []
        if self.bot.is_debug is True:
            raw_content += '\n\n0 www.stackoverflow.com'  # added for Testing
        for line in raw_content.splitlines():
            if line.startswith('0') and line not in ['', '0.0.0.0 0.0.0.0']:
                line = line.split('#')[0].strip()
                _, forbidden_url = line.split(' ')
                _out.append(forbidden_url.strip())
        return set(_out)

    async def _create_forbidden_link_list(self):
        """
        Downloads Blacklist and saves it to json, after processing (-->_process_raw_blocklist_content)
        """
        if self.bot.aio_request_session is None:
            await asyncio.sleep(2)

        async with self.bot.aio_request_session.get(self.blocklist_hostfile_url) as _response:
            if RequestStatus(_response.status) is RequestStatus.Ok:
                _content = await _response.read()
                _content = _content.decode('utf-8', errors='ignore')
                forbidden_links = await self._process_raw_blocklist_content(_content)

                _path = APPDATA["forbidden_link_list.json"]
                writejson(list(map(lambda x: urlparse('https://' + x).netloc.replace('www.', ''), forbidden_links)), _path)  # converting to list as set is not json serializable

    def cog_unload(self):
        self.fresh_blacklist_loop.stop()
        self.fresh_blacklist_loop.stop()
        super().unload()
        log.info("Cog '%s' has been unloaded", str(self))

    @tasks.loop(hours=24.0, reconnect=True)
    async def fresh_blacklist_loop(self):
        """
        Background Loop to pull a new Blacklist every 24 hours and create a new blacklist json.
        """
        await self._create_forbidden_link_list()
        log.debug("Link Blacklist was refreshed")

    @fresh_blacklist_loop.before_loop
    async def before_fresh_blacklist_loop(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=1.0, reconnect=True)
    async def check_link_best_by_loop(self):
        """
        Background loop to check if the delete time of an link message has passed, deletes the link message and updated the db to show it was deleted.
        """
        for message_id in self.data_storage_handler.link_messages_to_remove:
            msg = await self.link_channel.fetch_message(message_id)
            await msg.delete()
            self.data_storage_handler.update_removed_status(message_id)

    @check_link_best_by_loop.before_loop
    async def before_check_link_best_by_loop(self):
        await self.bot.wait_until_ready()


# endregion [Setup]

# region [Properties]

    @property
    def forbidden_url_words(self):
        """
        Lazy loads the forbidden url word json when needed.

        Returns:
            set: forbidden url word list
        """
        return set(map(lambda x: str(x).casefold(), loadjson(self.forbidden_url_words_file)))

    @property
    def link_channel(self):
        """
        lazy loads the channel to save the links in

        Returns:
            discord.channel: channel object
        """
        return self.bot.get_channel(COGS_CONFIG.getint(self.config_name, 'link_channel'))

    @property
    def allowed_channels(self):
        """
        Lazy loads the list of channel names where the commands in this cog are allowed

        Returns:
            set: channel name list
        """
        return set(COGS_CONFIG.getlist(self.config_name, 'allowed_channels'))

    @property
    def bad_link_image(self):
        """
        Lazy loads the image that should be posted when someone tries to save an fobidden link.

        Returns:
            tuple: name of the image, path to the image
        """

        name = COGS_CONFIG.get(self.config_name, 'bad_link_image_name')
        return name, APPDATA[name]

    @property
    def forbidden_links(self):
        """
        Lazy loads the forbidden links json when needed.

        Returns:
            set: forbidden link list

        """
        return set(loadjson(APPDATA["forbidden_link_list.json"]))

# endregion [Properties]

# region [Listener]


# endregion [Listener]

# region [Commands]


    @commands.command(aliases=get_aliases("add_forbidden_word"))
    @commands.has_any_role(*COGS_CONFIG.getlist('save_link', 'allowed_admin_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist('save_link', 'allowed_channels')))
    async def add_forbidden_word(self, ctx, word: str):
        """
        adds a word to the forbidden url word list, case is unimportant

        Args:
            word (str): the word to save
        """
        if word.casefold() in self.forbidden_url_words:
            await ctx.send(embed=await make_basic_embed(title='Word already in list', text=f'The word "{word}" is allready in the forbidden url words list', symbol='not_possible'))
            return
        _forbidden_list = loadjson(self.forbidden_url_words_file)
        _forbidden_list.append(word)
        writejson(_forbidden_list, self.forbidden_url_words_file)
        await ctx.send(embed=await make_basic_embed(title='Added Word', text=f'The Word "{word}" was added to the forbidden url word list', symbol='update'))

    @commands.command(aliases=get_aliases("remove_forbidden_word"))
    @commands.has_any_role(*COGS_CONFIG.getlist('save_link', 'allowed_admin_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist('save_link', 'allowed_channels')))
    async def remove_forbidden_word(self, ctx, word: str):
        """
        removes a word from the forbidden url word list, caseinsensitive.

        Args:
            word (str): the word to remove
        """
        if word.casefold() not in self.forbidden_url_words:
            await ctx.send(embed=await make_basic_embed(title='Word not in list', text=f'The word "{word}" is not found in the forbidden url words list', symbol='not_possible'))
            return
        _forbidden_list = loadjson(self.forbidden_url_words_file)
        _new_list = [url_words for url_words in _forbidden_list if url_words.casefold() != word.casefold()]

        writejson(_new_list, self.forbidden_url_words_file)
        await ctx.send(embed=await make_basic_embed(title='Removed Word', text=f'The Word "{word}" was removed from the forbidden url word list', symbol='update'))

    @commands.command(aliases=get_aliases("clear_all_links"))
    @commands.has_any_role(*COGS_CONFIG.getlist('save_link', 'delete_all_allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist('save_link', 'allowed_channels')))
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def clear_all_links(self, ctx, sure: bool = False):
        """
        Clears the datastorage (database) and sets it up empty again.

        Args:
            sure (bool, optional): skip the confirmation dialog. Defaults to False.
        """
        log.critical("'%s' requested to delete all links", ctx.author.name)
        if sure is False:
            await ctx.send(embed=await make_basic_embed(title="Are you sure?", text="Do you really want to delete all saved links?", symbol='warning', **{"ANSWER **YES** to delete all saved links": "You have __30 SECONDS__ to answer"}))
            user = ctx.author
            channel = ctx.channel

            def check(m):
                return m.author.name == user.name and m.channel.name == channel.name
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30.0)
                await self._clear_links(ctx, msg.content)
            except asyncio.TimeoutError:
                await ctx.send(embed=await make_basic_embed(title='No answer received', text='canceling request to delete all links, nothing was deleted', symbol='cancelled'))
        else:
            await self._clear_links(ctx, 'yes')

    @commands.command(hidden=False, aliases=get_aliases("get_link"))
    @commands.has_any_role(*COGS_CONFIG.getlist('save_link', 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist('save_link', 'allowed_channels')))
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    async def get_link(self, ctx, name: str):
        """
        Get a previously saved link by link_name.

        Args:
            name (str): link name, will be fuzzy matched.
        """

        _name, _link = self.data_storage_handler.get_link(name)
        if _name is None:
            await ctx.send(embed=await make_basic_embed(title="Not Found!", text=f"I could not find a Link with the Name of '{name}', or any similar Name!", symbol='not_possible'), delete_after=60)
            log.warning("not able to find link with name '%s'", name)
            return
        await ctx.send(embed=await make_basic_embed(title='Retrieved link!', text='Link was successfully retrieved from storage', symbol='link', **{'available for the next': '1 Hour', _name: _link}), delete_after=60 * 60)

    @ commands.command(hidden=False, aliases=get_aliases("get_all_links"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('save_link', 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist('save_link', 'allowed_channels')))
    @ commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    async def get_all_links(self, ctx, in_format: str = 'txt'):
        """
        Get a list of all previously saved links, as a file.

        Args:
            in_format (str, optional): output format, currently possible: 'json', 'txt'. Defaults to 'txt'.
        """

        with TemporaryDirectory() as tempdir:
            if in_format == 'json':
                _link_dict = self.data_storage_handler.get_all_links('json')
                _name = 'all_links.json'
                _path = pathmaker(tempdir, _name)
                if len(_link_dict) == 0:
                    await ctx.send(embed=await make_basic_embed(title='No saved links', text='I have no links saved in my datastorage', symbol='not_possible'))
                    return

                writejson(_link_dict, _path)

            elif in_format == 'txt':
                _link_list = self.data_storage_handler.get_all_links('plain')
                _name = 'all_links.txt'
                _path = pathmaker(tempdir, _name)
                if len(_link_list) == 0:
                    await ctx.send(embed=await make_basic_embed(title='No saved links', text='I have no links saved in my datastorage', symbol='not_possible'))
                    return

                writeit(_path, '\n'.join(_link_list))
            else:
                await ctx.send(embed=await make_basic_embed(title='Unknown Format requested', text=f'unable to provide link list in format "{in_format}"'), symbol='not_possible')
                return
            _file = discord.File(_path, _name)
            await ctx.send(file=_file)

    @ commands.command(hidden=False, aliases=get_aliases("save_link"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('save_link', 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist('save_link', 'allowed_channels')))
    @ commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def save_link(self, ctx, link: str, link_name: str = None, days_to_hold: int = None):
        """
        Save a link to the DataStorage and posts it for a certain time to an storage channel.

        Args:
            link (str): link to save
            link_name (str, optional): name to save the link as, if not given will be generated from url. Defaults to None.
            days_to_hold (int, optional): time befor the link will be deleted from storage channel in days, if not give will be retrieved from config. Defaults to None.
        """
        # TODO: refractor that monster of an function

        to_check_link = await self._make_check_link(link)
        parsed_link = urlparse(link, scheme='https').geturl().replace('///', '//')
        date_and_time = datetime.utcnow()
        if all(to_check_link != forbidden_link for forbidden_link in self.forbidden_links) and all(forbidden_word not in to_check_link for forbidden_word in self.forbidden_url_words):

            if link_name is None:
                link_name = await self._make_link_name(link)
            link_name = link_name.upper()

            # check if link name is already occupied
            if await self._check_link_name_existing(link_name) is True:

                await ctx.send(embed=await make_basic_embed(title='Link name already in use', text=f"The link_name '{link_name}', is already taken, please choose a different Name.", symbol='not_possible'))
                return None

            # calculate or retrieve all other needed values
            days = COGS_CONFIG.getint(self.config_name, 'default_storage_days') if days_to_hold is None else days_to_hold
            delete_date_and_time = date_and_time + timedelta(days=days)
            author = ctx.author

            # create the link item
            link_item = LINK_DATA_ITEM(author, link_name, date_and_time, delete_date_and_time, parsed_link)

            # post the link as embed to the specified save link channel
            link_store_message = await self.link_channel.send(embed=await self._answer_embed(link_item))

            # save to datastorage
            log.info("new link --> author: '%s', link_name: '%s', delete_date_time: '%s', days_until_delete: '%s', parsed_link: '%s'",
                     author.name,
                     link_name,
                     delete_date_and_time.isoformat(timespec='seconds'),
                     str(days),
                     parsed_link)
            await self.save(link_item, link_store_message.id)

            # post an success message to the channel from where the command was invoked. Delete after 60 seconds.
            await ctx.send(embed=await make_basic_embed(title='success', text='✅ Link was successfully saved', symbol='save'))

        else:

            await self._handle_forbidden_link(ctx, date_and_time, parsed_link, to_check_link)

    async def _handle_forbidden_link(self, ctx, date_time, parsed_link, to_check_link):
        log.warning("link '%s' matched against a forbidden link or contained a forbidden word", parsed_link)

        await ctx.send(embed=await self._bad_link_embed(), file=await self._get_bad_link_image())
        if ctx.channel.permissions_for(ctx.me).manage_messages:
            await ctx.message.delete(delay=None)
            log.debug("was able to delete the offending link")
            was_deleted = True

        else:
            log.error("was NOT able to delete the offending link")
            was_deleted = False

        notify_embed = await self._notify_dm_embed(was_deleted=was_deleted,
                                                   author=ctx.author,
                                                   date_time=date_time,
                                                   channel=ctx.channel.name,
                                                   link=parsed_link,
                                                   matches_link=await self.get_matched_forbidden_link(to_check_link),
                                                   matches_word=await self.get_matched_forbidden_word(to_check_link))

        for user_id in COGS_CONFIG.getlist(self.config_name, 'member_to_notifiy_bad_link'):
            user = self.bot.get_user(int(user_id))
            await user.send(embed=notify_embed)
            log.debug("notified '%s' about the offending link", user.name)

    @ commands.command(hidden=False, aliases=get_aliases("get_forbidden_list"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('save_link', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('save_link', 'allowed_channels')))
    @ commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    async def get_forbidden_list(self, ctx, file_format: str = 'json'):
        """
        Get the forbidden link list as an file.

        Args:
            file_format (str, optional): format the list file should have(currently possible: 'json'). Defaults to 'json'.
        """

        if file_format == 'json':
            with TemporaryDirectory() as tempdir:
                _name = 'forbidden_links.json'
                _path = pathmaker(tempdir, _name)
                writejson(list(self.forbidden_links), _path, indent=2)
                _file = discord.File(_path, filename=_name)
                await ctx.send(file=_file, delete_after=60)

    @ commands.command(aliases=get_aliases("delete_link"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('save_link', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('save_link', 'allowed_channels')))
    @ commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    async def delete_link(self, ctx, name: str, scope: str = 'channel'):
        """
        Deletes an link by name (name will be fuzzy matched).

        Args:
            name (str): name of the link to delete
            scope (str, optional): if 'channel' it will only delete the link in the channel but keeps it in the Database, if 'full' tries to delete both in channel and in database. Defaults to 'channel'.
        """

        log.critical("Link with Link name '%s' was requested to be deleted by '%s'", name, ctx.author.name)
        link_name, link_message_id, link_status = self.data_storage_handler.get_link_for_delete(name)
        if link_message_id is None:
            await ctx.send(embed=await make_basic_embed(title="Link not found", text="I cannot find a link with that name", symbol="cancelled", link_name=name))
            log.warning("No saved link found with name: '%s'", name)
            return
        if scope == 'channel' and link_status in [1, True]:
            await ctx.send(embed=await make_basic_embed(title='Link was already deleted!', text='The link was already deleted from the channel some time ago', symbol="not_possible"))
            return
        answer = {}
        if scope == 'full':
            self.data_storage_handler.delete_link(link_name)
            answer["deleted_from_database"] = "✅"
        if link_status != 1:
            message = await self.link_channel.fetch_message(link_message_id)
            if scope != 'full':
                self.data_storage_handler.update_removed_status(link_message_id)
                await message.delete()
                answer["deleted_from_channel"] = "✅"
        await ctx.send(embed=await make_basic_embed(title="Deleted Link", text='Link was deleted from: ', symbol='trash', **answer))


# endregion [Commands]

# region [DataStorage]


    async def link_name_list(self):
        """
        Retrieves all saved link names from the DataStorage.

        async wrapper for access to the modular data storage (currently sqlite Db)

        Returns:
            set: set of all link names
        """

        return self.data_storage_handler.all_link_names

    async def save(self, link_item: LINK_DATA_ITEM, message_id: int):
        """
        Adds new link to the DataStorage

        async wrapper for access to the modular data storage (currently sqlite Db)

        Args:
            link_item (LINK_DATA_ITEM): namedtuple to contain link data see 'antipetros_discordbot.utility.named_tuples --> LINK_DATA_ITEM'
        """

        self.data_storage_handler.add_data(link_item, message_id)


# endregion [DataStorage]

# region [Embeds]

    async def _answer_embed(self, link_item):
        """
        creates the stored link embed for an saved link.

        Is extra function to make it more readable. No customization currently.

        Returns:
            discord.Embed: link storage embed.
        """

        _rel_time = link_item.delete_date_time - link_item.date_time
        _embed = discord.Embed(title="Saved Link", description="Temporary Stored Link", color=0x4fe70e)
        _embed.set_thumbnail(url=EMBED_SYMBOLS.get('link', None))
        _embed.add_field(name="from:", value=link_item.author.name, inline=True)
        _embed.add_field(name=link_item.link_name + ':', value=link_item.link, inline=False)
        _embed.add_field(name="available until:", value=link_item.delete_date_time.strftime("%Y/%m/%d, %H:%M:%S") + f" ({str(_rel_time).split(',')[0].strip()})", inline=False)
        _embed.add_field(name="retrieve command:", value=f"`get_link {link_item.link_name}`", inline=True)
        _embed.add_field(name="retrieve all command", value="`get_all_links`", inline=True)
        _embed.set_footer(text='This link will be deleted after the date specified in "available until", afterwards it can still be retrieved by the retrieve commands')
        return _embed

    async def _bad_link_embed(self):
        """
        creates the answer embed for an answer to an forbidden link.

        Is extra function to make it more readable. No customization currently.

        Returns:
            discord.Embed: Bad link answer embed
        """

        embed = discord.Embed(title="FORBIDDEN LINK", description="You tried to save a link that is either in my forbidden_link-list or contains a forbidden word.", color=0x7c0303)
        embed.set_thumbnail(url=EMBED_SYMBOLS.get('forbidden', None))
        embed.add_field(name="🚫 The link has NOT been saved! 🚫", value="-", inline=False)
        embed.add_field(name="⚠️ DO NOT TRY THIS AGAIN ⚠️", value="-", inline=False)
        embed.set_footer(text="! This has been Logged !")
        return embed

    async def _notify_dm_embed(self, was_deleted: bool, author, date_time: datetime, channel: str, link: str, matches_link: list, matches_word: list):
        """
        creates the notify embed for DM notifications when an forbidden link was tried to be saved forbidden link.

        Is extra function to make it more readable. No customization currently.

        Returns:
            discord.Embed: notify dm embed
        """

        _description = ('The message has been successfully deleted and warning was posted!' if was_deleted else "I was not able to delete the message, but posted the warning")

        embed = discord.Embed(title='ATTEMPT AT SAVING FORBIDDEN LINK', description=_description, color=0xdf0005)
        embed.set_thumbnail(url=EMBED_SYMBOLS.get('warning', None))
        embed.add_field(name="User", value=f"__**{author.name}**__", inline=False)
        embed.add_field(name="User Display Name", value=f"*{author.display_name}*", inline=False)
        embed.add_field(name="User ID", value=f"**{author.id}**", inline=False)
        embed.add_field(name="Channel", value=f"**{channel}**", inline=False)
        embed.add_field(name="Date", value=date_time.date().isoformat(), inline=True)
        embed.add_field(name="Time", value=f"{date_time.time().isoformat(timespec='seconds')} UTC", inline=True)
        if COGS_CONFIG.getboolean(self.config_name, 'notify_with_link') is True:
            embed.add_field(name="Offending Link", value=f"***{link}***", inline=False)
            if matches_link != []:
                embed.add_field(name="forbidden link matches", value='\n'.join(matches_link), inline=False)
            if matches_word != []:
                embed.add_field(name="forbidden word matches", value='\n'.join(matches_word), inline=False)
        embed.set_footer(text="You have been notified, because your discord user id has been registered in my config, to be notified in such events.")
        return embed


# endregion [Embeds]


# region [HelperMethods]

    async def _get_bad_link_image(self):
        """
        Wraps the bad_link_image in and discord File object.
        has to be created each time, can't be stored in attribute as discord File object.

        Returns:
            discord.File: discord File containing the image
        """

        # image_path = COGS_CONFIG.get(self.config_name, 'bad_link_answer_image')
        # if image_path.casefold() == 'none':
        #     return None
        # image_name = os.path.basename(image_path)
        # return discord.File(image_path, image_name)
        name, path = self.bad_link_image
        if path == '' or path is None:
            return None
        if name == '' or name is None:
            name = os.path.basename(path)
        return discord.File(path, filename=name)

    async def _make_check_link(self, url):
        """
        Helper to normalize the link url, so it can easily be compared to the forbidden links (normalized link in each forbidden link)

        Args:
            url (str): link url

        Returns:
            str: normalized link url
        """

        temp_url = 'https://' + url if not url.startswith('http') else url
        check_link = urlparse(temp_url).netloc.replace('www.', '')
        return check_link.casefold()

    async def _make_link_name(self, url):
        """
        Helper to create an link name from the url if none was give by the command.

        Args:
            url (str): link url

        Returns:
            str: link name
        """
        temp_url = 'https://' + url if not url.startswith('http') else url
        link_name = urlparse(temp_url).netloc.replace('www.', '')
        link_name = link_name.split('.')
        return link_name[0]

    async def _check_link_name_existing(self, name):
        """
        Helper to check if link_name is already occupied.

        Args:
            name (str): link name

        Returns:
            [bool]: bool (True if already occupied)
        """

        _name_list = await self.link_name_list()
        return name in _name_list

    async def get_matched_forbidden_link(self, check_link):
        """
        get all unique matches between the input link and the forbidden link list, as list.

        Args:
            check_link (str): modified check url

        Returns:
            (list): all matches as list, if no matches, returns empty list
        """

        _out = [link for link in self.forbidden_links if check_link == link]
        return list(set(_out))

    async def get_matched_forbidden_word(self, url):
        """
        get all unique matches between the input link and the forbidden word list, as list.

        Args:
            check_link (str): modified check url

        Returns:
            (list): all matches as list, if no matches, returns empty list
        """

        _out = [word for word in self.forbidden_url_words if word in url]
        return list(set(_out))

    async def _clear_links(self, ctx, answer):
        """
        Helper to tell the datastorage to reset.
        """
        if answer.casefold() == 'yes':
            for link_id in self.data_storage_handler.get_all_posted_links():
                msg = await self.link_channel.fetch_message(link_id)
                await msg.delete()
            self.data_storage_handler.clear()
            await ctx.send(embed=await make_basic_embed(title="Link data deleted", text="The link data storage was deleted an initialized again, it is ready for new input", symbol='trash'))

        elif answer.casefold() == 'no':
            await ctx.send(embed=await make_basic_embed(title="Aborting deletion process", text='aborting deletion process, nothing was deleted', symbol='cancelled'))


# endregion [HelperMethods]

# region [SpecialMethods]


    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

# endregion [DunderMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(SaveLinkCog(bot))
