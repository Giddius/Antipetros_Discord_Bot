

# region [Imports]

# * Standard Library Imports -->
import os
import re
import sqlite3 as sqlite
import unicodedata
from datetime import datetime, timedelta
import asyncio
import shutil
from concurrent.futures import ThreadPoolExecutor
from tempfile import TemporaryDirectory, TemporaryFile
# * Third Party Imports -->
import discord
from discord.ext import commands
from async_property import async_property
from jinja2 import Environment, FileSystemLoader
import pdfkit
from weasyprint import HTML, CSS
# * Gid Imports -->
import gidlogger as glog
from pprint import pprint, pformat
# * Local Imports -->
from antipetros_discordbot.utility.named_tuples import SUGGESTION_DATA_ITEM
from antipetros_discordbot.utility.sqldata_storager import SuggestionDataStorageSQLite
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, writeit
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock
# endregion[Imports]

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


# TODO: create report generator in different formats, at least json and Html, probably also as embeds and Markdown

# TODO: Document and Docstrings

# endregion[TODO]

class SaveSuggestion(commands.Cog, command_attrs={'hidden': True}):

    # region [ClassAttributes]

    suggestion_name_regex = re.compile(r"(?P<name>(?<=#).*)")
    config_name = 'save_suggestions'
    jinja_env = Environment(loader=FileSystemLoader(APPDATA["reports"]))
    css_files = {"basic_report_style": (APPDATA["basic_report_style.css"], "basic_report_style.css"),
                 'exp_report_stylesheet': (APPDATA["style.css"], "style.css")}
    auto_accept_user_file = APPDATA["auto_accept_suggestion_users.json"]

# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.data_storage_handler = SuggestionDataStorageSQLite()
        if self.bot.is_debug:
            self.save_commands()
        glog.class_init_notification(log, self)

    def save_commands(self):
        command_json_file = r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\docs\commands.json"
        command_json = loadjson(command_json_file)
        command_json[str(self)] = {'file_path': pathmaker(os.path.abspath(__file__)),
                                   'description': __doc__,
                                   'commands': {(com.name + ' ' + com.signature).replace('<ctx>', '').replace('  ', ' ').strip(): com.help for com in self.get_commands()}}
        writejson(command_json, command_json_file, indent=4)
        log.debug("commands for %s saved to %s", self, command_json_file)

# endregion [Init]

# region [Properties]

    @property
    def command_emojis(self):
        if self.bot.is_debug:
            COGS_CONFIG.read()
        return {'save': COGS_CONFIG.get(self.config_name, 'save_emoji'),
                'upvote': COGS_CONFIG.get(self.config_name, 'upvote_emoji'),
                'downvote': COGS_CONFIG.get(self.config_name, 'downvote_emoji')}

    @property
    def categories(self):
        _out = self.data_storage_handler.category_emojis
        if self.bot.is_debug:
            log.debug(_out)
        return _out

    @property
    def allowed_channels(self):
        if self.bot.is_debug:
            COGS_CONFIG.read()
        return set(COGS_CONFIG.getlist(self.config_name, 'allowed_channels'))

    @property
    def notify_contact_member(self):
        if self.bot.is_debug:
            COGS_CONFIG.read()
        return COGS_CONFIG.get(self.config_name, 'notify_contact_member')

    @property
    def messages_to_watch(self):
        return self.data_storage_handler.get_all_non_discussed_message_ids()

    @property
    def saved_messages(self):
        return self.data_storage_handler.get_all_message_ids()

    @property
    def std_datetime_format(self):
        return BASE_CONFIG.get('datetime', 'std_format')

    @property
    def auto_accept_user_dict(self):
        return loadjson(self.auto_accept_user_file)

# endregion [Properties]

# region [Listener]

    @ commands.Cog.listener()
    @ commands.has_any_role(*COGS_CONFIG.getlist('save_suggestions', 'allowed_roles'))
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        if channel.name not in self.allowed_channels:
            return
        reaction_user = await self.bot.fetch_user(payload.user_id)
        if reaction_user.bot is True or reaction_user.id in self.bot.blacklist_user:
            return
        message = await channel.fetch_message(payload.message_id)
        emoji_name = unicodedata.name(payload.emoji.name)

        if emoji_name == self.command_emojis['save']:
            await self._new_suggestion(channel, message, payload.guild_id, reaction_user)
            if str(message.author.id) not in self.auto_accept_user_dict:
                await message.author.send(embed=await self.bot.make_basic_embed(title='Your Suggestion was saved by the Devs!',
                                                                                text='The devs have saved your in their Database to locate it more easily',
                                                                                if_you_do_not_want_this=f'DM me: `@Antipetros unsave_suggestion {message.id}`',
                                                                                if_you_want_to_see_all_data_saved_from_you='DM me: `@Antipetros request_my_data`',
                                                                                if_you_want_to_have_all_data_saved_from_you_deleted='DM me: `@Antipetros remove_all_userdata`'),
                                          footer='If you dont want to receive this message anymore íf your suggestion is saved, DM me: `@AntiPetros auto_accept_suggestions')

        elif emoji_name in self.categories and message.id in self.saved_messages:
            await self._change_category(channel, message, emoji_name)

        elif emoji_name in [self.command_emojis['upvote'], self.command_emojis['downvote']] and message.id in self.saved_messages:
            await self._change_votes(message, emoji_name)


# endregion [Listener]

# region [Commands]


    @ commands.command()
    @ commands.has_any_role(*COGS_CONFIG.getlist('save_suggestions', 'allowed_admin_roles'))
    async def mark_discussed(self, ctx, *suggestion_ids: int):
        if ctx.channel.name not in self.allowed_channels:
            return
        embed_dict = {}
        for suggestion_id in suggestion_ids:
            self.data_storage_handler.mark_discussed(suggestion_id)
            embed_dict['message_with_id_' + str(suggestion_id)] = 'was marked as discussed'
        await ctx.send(embed=await self.bot.make_basic_embed(title='Marked Suggestions as discussed', text='The following items were marked as discussed: ', symbol='update', ** embed_dict))

    @ commands.command()
    @ commands.has_any_role(*COGS_CONFIG.getlist('save_suggestions', 'allowed_roles'))
    async def clear_all_suggestions(self, ctx, sure=False):
        if ctx.channel.name not in self.allowed_channels:
            return
        if sure is False:
            question_msg = await ctx.send("Do you really want to delete all saved suggestions?\n\nANSWER **YES** in the next __30 SECONDS__")
            user = ctx.author
            channel = ctx.channel

            def check(m):
                return m.author.name == user.name and m.channel.name == channel.name
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30.0)
                await self._clear_suggestions(ctx, msg.content)
            except asyncio.TimeoutError:
                await ctx.send(embed=await self.bot.make_basic_embed(title='No answer received', text='canceling request to delete Database, nothing was deleted', symbol='cancelled'))
                await question_msg.delete()
        else:
            await self._clear_suggestions(ctx, 'yes')

    @ commands.command()
    @commands.dm_only()
    async def auto_accept_suggestions(self, ctx):
        if str(ctx.author.id) in self.auto_accept_user_dict:
            # Todo: make as embed
            await ctx.send("you are already in the auto accept suggestion list")
            return
        auto_accept_dict = loadjson(self.auto_accept_user_file)
        auto_accept_dict[ctx.author.id] = ctx.author.name
        writejson(auto_accept_dict, self.auto_accept_user_file)
        # Todo: make as embed
        await ctx.send("I added you to the auto accept suggestion list")

    @commands.command(name='unsave_suggestion')
    @commands.dm_only()
    async def user_delete_suggestion(self, ctx, suggestion_id: int):
        if suggestion_id not in self.saved_messages:

            await ctx.send(embed=await self.bot.make_basic_embed(title=f'ID {suggestion_id} not found',
                                                                 text='We have no message saved with this ID',
                                                                 symbol='not_possible',
                                                                 if_you_feel_like_this_is_an_error_please_contact=self.notify_contact_member))
            return
        suggestion = self.data_storage_handler.get_suggestion_by_id(suggestion_id)
        if ctx.author.name != suggestion['author_name']:
            # TODO: make as embed
            await ctx.send("You are not the Author of that suggestion, so you cannot remove it | if you feel like this is an error please contact: " + self.notify_contact_member)
            return
        await ctx.send(f"Do you really don't want the following suggestion saved by the dev team?\n{CodeBlock(suggestion['content'])}\n\nPossible Answers: YES, NO\nTime to answer: 30sec")

        def check(m):
            return m.author.name == ctx.author.name and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            if 'yes' in msg.content.casefold():
                self.data_storage_handler.remove_suggestion_by_id(suggestion_id)
                # TODO: make as embed
                await ctx.send("Suggestion was remove from stored data, it will still be on discord!")
                return
            elif 'no' in msg.content.casefold():
                # TODO: make as embed
                await ctx.send("NO was answered, keeping message saved.")
                return
            else:
                # TODO: make as embed
                await ctx.send("Did not register an valid answer, cancelling.")
                return

        except asyncio.TimeoutError:
            # TODO: make as embed
            await ctx.send('No answer received, aborting request, you can always try again')
            return

    @ commands.command()
    @ commands.has_any_role(*COGS_CONFIG.getlist('save_suggestions', 'allowed_roles'))
    async def get_all_suggestions(self, ctx, report_template: str = "basic_report.html.jinja"):
        log.debug('command was triggered')
        if ctx.channel.name not in self.allowed_channels:
            return
        log.debug('correct channel')
        log.debug('querying data')
        query = self.data_storage_handler.get_all_suggestion_not_discussed()
        var_dict = {'all_suggestions': query}
        log.debug('getting template')
        template = self.jinja_env.get_template(report_template)
        log.debug('creating Tempdir')
        with TemporaryDirectory() as tempfold:
            html_path = pathmaker(tempfold, "suggestion_report.html")
            pdf_path = pathmaker(tempfold, 'suggestion_report.pdf')
            log.debug('rendering template and writing to file')
            writeit(html_path, await self.bot.execute_in_thread(template.render, var_dict))

            log.debug('copying stylesheet')
            shutil.copyfile(self.css_files.get('exp_report_stylesheet')[0], pathmaker(tempfold, self.css_files.get('exp_report_stylesheet')[1]))
            log.debug('transforming html to pdf')

            weasy_html = HTML(filename=html_path)
            weasy_html.write_pdf(pdf_path)

            file = discord.File(pdf_path, filename='suggestion_report.pdf')
            log.debug('sending file')
            await ctx.send(file=file)

    @ commands.command(name="remove_all_my_data")
    @commands.dm_only()
    async def remove_all_userdata(self, ctx):
        user = ctx.author
        all_user_data = self.data_storage_handler.get_suggestions_per_author(user.name)
        if len(all_user_data) == 0:
            # TODO: make as embed
            await ctx.send("We have no data stored from you | if you feel like this is an error please contact: " + self.notify_contact_member)
            return
            # TODO: make as embed
        await ctx.send(f"Do you really all your suggestion stored by the dev team deleted from the Database?\n\nPossible Answers: YES, NO\nTime to answer: 30sec")

        def check(m):
            return m.author.name == ctx.author.name and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            if 'yes' in msg.content.casefold():
                for row in all_user_data:
                    self.data_storage_handler.remove_suggestion_by_id(row['message_discord_id'])
                    # TODO: make as embed
                await ctx.send("All your data was removed from the database")
                return
            elif 'no' in msg.content.casefold():
                # TODO: make as embed
                await ctx.send("NO was answered, keeping messages saved.")
                return
            else:
                # TODO: make as embed
                await ctx.send("Did not register an valid answer, cancelling.")
                return

        except asyncio.TimeoutError:
            # TODO: make as embed
            await ctx.send('No answer received, aborting request, you can always try again')
            return

    @ commands.command()
    @commands.dm_only()
    async def request_my_data(self, ctx):
        user = ctx.author
        all_user_data = self.data_storage_handler.get_suggestions_per_author(user.name)
        if len(all_user_data) == 0:
            # TODO: make as embed
            await ctx.send("We have no data stored from you | if you feel like this is an error please contact: " + self.notify_contact_member)
            return
        with TemporaryDirectory() as tmpdir:
            writejson(await self._row_to_json_user_data(all_user_data), pathmaker(tmpdir, 'output.json'))
            file = discord.File(pathmaker(tmpdir, 'output.json'), filename=ctx.author.name + '_data.txt')
            await ctx.send(file=file)

# endregion [Commands]

# region [DataStorage]

    async def add_suggestion(self, suggestion_item: SUGGESTION_DATA_ITEM, extra_data=None):
        if extra_data is not None:
            _path = pathmaker(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\antipetros_discordbot\data\data_storage\images\suggestion_extra_data", extra_data[0])
            with open(_path, 'wb') as extra_data_file:
                extra_data_file.write(extra_data[1])
            suggestion_item = suggestion_item._replace(extra_data=(extra_data[0], _path))
        try:
            self.data_storage_handler.add_suggestion(suggestion_item)
            return True, suggestion_item
        except sqlite.Error as error:
            log.error(error)
            return False, suggestion_item

    async def set_category(self, category, message_id):
        try:
            self.data_storage_handler.update_category(category, message_id)
            return True
        except sqlite.Error as error:
            log.error(error)
            return False

    async def _clear_suggestions(self, ctx, answer):
        if answer.casefold() == 'yes':
            # TODO: make as embed
            await ctx.send('deleting Database')
            self.data_storage_handler.clear()
            # TODO: make as embed
            await ctx.send('Database was cleared, ready for input again')

        elif answer.casefold() == 'no':
            # TODO: make as embed
            await ctx.send('canceling request to delete Database, nothing was deleted')


# endregion [DataStorage]

# region [Embeds]

    async def make_add_success_embed(self, suggestion_item: SUGGESTION_DATA_ITEM):
        _filtered_content = []
        if suggestion_item.name is not None:
            for line in suggestion_item.message.content.splitlines():
                if suggestion_item.name.casefold() not in line.casefold():
                    _filtered_content.append(line)
            _filtered_content = '\n'.join(_filtered_content)
        else:
            _filtered_content = suggestion_item.message.content
        _filtered_content = f"```\n{_filtered_content.strip()}\n```"

        embed = discord.Embed(title="**Suggestion was Saved!**", description="Your suggestion was saved for the Dev Team.\n\n", color=0xf2ea48)
        embed.set_thumbnail(url=self.bot.embed_symbols.get('save', None))
        embed.add_field(name="Title:", value=f"__{suggestion_item.name}__", inline=False)
        if COGS_CONFIG.getboolean(self.config_name, 'add_success_embed_verbose') is True:
            embed.add_field(name="Author:", value=f"*{suggestion_item.message_author.name}*", inline=True)
            embed.add_field(name="Content:", value=_filtered_content, inline=True)
            embed.add_field(name='Saved Timestamp:', value=suggestion_item.time.isoformat(timespec='seconds'), inline=False)

        extra_data_value = ['No attachments detected'] if suggestion_item.extra_data is None else suggestion_item.extra_data[0]
        embed.add_field(name='Attachments', value=f"`{extra_data_value}`")

        return embed

    async def make_changed_category_embed(self, message, category):
        embed = discord.Embed(title="**Updated Suggestion Category**", description="I updated the category an Suggestion\n\n", color=0xf2a44a)
        embed.set_thumbnail(url=self.bot.embed_symbols.get('update', None))
        embed.add_field(name="New Category:", value=category, inline=False)
        embed.add_field(name="Suggestion:", value=message.jump_url, inline=False)
        return embed

    async def make_already_saved_embed(self):
        embed = discord.Embed(title="**This Suggestion was already saved!**", description="I did not save the Suggestion as I have it already saved", color=0xe04d7e)
        embed.set_thumbnail(url=self.bot.embed_symbols.get('not_possible', None))
        return embed


# endregion [Embeds]

# region [HelperMethods]

    async def collect_title(self, content):
        name_result = self.suggestion_name_regex.search(content)
        if name_result:
            name = name_result.group('name')
            name = None if len(name) > 100 else name.strip().title()
        else:
            name = None
        return name

    async def specifc_reaction_from_message(self, message, target_reaction):
        for reaction in message.reactions:
            if unicodedata.name(reaction.emoji) == target_reaction:
                return reaction

    async def _new_suggestion(self, channel, message, guild_id, reaction_user):
        if message.id in self.saved_messages:
            await channel.send(embed=await self.make_already_saved_embed())
            return

        message_member = await self.bot.retrieve_member(guild_id, message.author.id)
        reaction_member = await self.bot.retrieve_member(guild_id, reaction_user.id)
        now_time = datetime.utcnow()
        name = await self.collect_title(message.content)
        extra_data = (message.attachments[0].filename, await message.attachments[0].read()) if len(message.attachments) != 0 else None

        suggestion_item = SUGGESTION_DATA_ITEM(name, message_member, reaction_member, message, now_time)

        was_saved, suggestion_item = await self.add_suggestion(suggestion_item, extra_data)
        log.info("saved new suggestion, suggestion name: '%s', suggestion author: '%s', saved by: '%s', suggestion has extra data: '%s'",
                 name,
                 message_member.name,
                 reaction_member.name,
                 'yes' if extra_data is not None else 'no')

        if was_saved is True:
            await channel.send(embed=await self.make_add_success_embed(suggestion_item))

    async def _remove_previous_categories(self, target_message, new_emoji_name):
        for reaction_emoji in self.categories:
            if reaction_emoji is not None and reaction_emoji != new_emoji_name:
                other_reaction = await self.specifc_reaction_from_message(target_message, reaction_emoji)
                if other_reaction is not None:
                    await other_reaction.clear()

    async def _change_category(self, channel, message, emoji_name):
        category = self.categories.get(emoji_name)
        if category:
            success = await self.set_category(category, message.id)
            if success:
                await channel.send(embed=await self.make_changed_category_embed(message, category))
                log.info("updated category for suggestion (id: %s) to category '%s'", message.id, category)
                await self._remove_previous_categories(message, emoji_name)

    async def _change_votes(self, message, emoji_name):
        reaction = await self.specifc_reaction_from_message(message, emoji_name)
        _count = reaction.count
        self.data_storage_handler.update_votes(emoji_name, _count, message.id)
        log.info("updated votecount for suggestion (id: %s) for type: '%s' to count: %s", message.id, emoji_name, _count)

    async def _row_to_json_user_data(self, data):
        _out = {}
        for row in data:
            _out[row['message_discord_id']] = {'name': row['name'],
                                               'utc_posted_time': row['utc_posted_time'],
                                               'utc_saved_time': row['utc_saved_time'],
                                               'upvotes': row['upvotes'],
                                               'downvotes': row['downvotes'],
                                               'category_name': row['category_name'],
                                               'author_name': row['author_name'],
                                               'content': row['content'],
                                               'data_name': row['data_name']}
        return _out

# endregion [HelperMethods]

# region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__

# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(SaveSuggestion(bot))
