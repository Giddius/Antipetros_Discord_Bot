

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import re
import shutil
import asyncio
import sqlite3 as sqlite
from datetime import datetime
from tempfile import TemporaryDirectory
from textwrap import dedent
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from discord.ext import commands
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases, get_doc_data
from antipetros_discordbot.utility.misc import make_config_name
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_channel_and_allowed_role, owner_or_admin, allowed_requester
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.named_tuples import SUGGESTION_DATA_ITEM
from antipetros_discordbot.utility.embed_helpers import EMBED_SYMBOLS, DEFAULT_FOOTER, make_basic_embed
from antipetros_discordbot.utility.sqldata_storager import AioSuggestionDataStorageSQLite
from antipetros_discordbot.utility.gidtools_functions import writeit, loadjson, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.id_generation import make_full_cog_id
from antipetros_discordbot.engine.replacements import auto_meta_info_command
# endregion[Imports]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
COG_NAME = "SaveSuggestionCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion [Constants]

# region [TODO]


# TODO: create report generator in different formats, at least json and Html, probably also as embeds and Markdown

# TODO: Document and Docstrings

# endregion[TODO]

class SaveSuggestionCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Provides functionality for each Antistasi Team to save suggestions by reacting with emojis.
    """

    # region [ClassAttributes]
    cog_id = 13
    full_cog_id = make_full_cog_id(THIS_FILE_DIR, cog_id)
    suggestion_name_regex = re.compile(r"(?P<name>(?<=#).*)")

    config_name = CONFIG_NAME

    jinja_env = Environment(loader=FileSystemLoader(APPDATA["report_templates"]))

    css_files = {"basic_report_style.css": (APPDATA["basic_report_style.css"], "basic_report_style.css"),
                 'style.css': (APPDATA["style.css"], "style.css"),
                 'experiment_css_1.css': (APPDATA['experiment_css_1.css'], 'experiment_css_1.css'),
                 'experiment_3.css': (APPDATA['experiment_3.css'], 'experiment_3.css')}

    auto_accept_user_file = pathmaker(APPDATA["json_data"], "auto_accept_suggestion_users.json")

    docattrs = {'show_in_readme': True,
                'is_ready': CogMetaStatus.WORKING | CogMetaStatus.OPEN_TODOS | CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.NEEDS_REFRACTORING | CogMetaStatus.DOCUMENTATION_MISSING,
                'extra_description': dedent("""
                                            """).strip(),
                'caveat': None}

    required_config_data = dedent("""
                                        suggestion_reaction_listener_enabled = yes
                                        suggestion_reaction_listener_allowed_channels = suggestions, bot-testing
                                        suggestion_reaction_listener_allowed_roles = Dev Helper, Admin
                                        downvote_emoji = 👎
                                        upvote_emoji = 👍
                                        add_success_embed_verbose = yes""")

# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.data_storage_handler = AioSuggestionDataStorageSQLite()
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        self.command_emojis = None
        self.categories_emojis = None
        self.vote_emojis = None
        self.ready = False

        glog.class_init_notification(log, self)


# endregion [Init]
# region [Setup]

    async def on_ready_setup(self):
        self.command_emojis = await self.get_command_emojis()
        self.categories_emojis = await self.get_categories_emojis()
        self.vote_emojis = await self.get_upvote_downvote_emojis()
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion[Setup]
# region [Properties]


    async def get_command_emojis(self):
        _out = await self.data_storage_handler.get_save_emojis()

        return _out

    async def get_upvote_downvote_emojis(self):
        return {'upvote': normalize_emoji(COGS_CONFIG.get(self.config_name, 'upvote_emoji')),
                'downvote': normalize_emoji(COGS_CONFIG.get(self.config_name, 'downvote_emoji'))}

    async def get_categories_emojis(self):

        categories_emojis = await self.data_storage_handler.category_emojis()

        return {normalize_emoji(key): value for key, value in categories_emojis.items()}

    async def get_category_name(self, emoji_name):
        data = await self.data_storage_handler.category_emojis()
        if emoji_name in data:
            return data.get(emoji_name)

    @ property
    def notify_contact_member(self):
        return COGS_CONFIG.get(self.config_name, 'notify_contact_member')

    async def messages_to_watch(self):
        return await self.data_storage_handler.get_all_non_discussed_message_ids()

    async def saved_messages(self):
        saved_messages = await self.data_storage_handler.get_all_message_ids()
        return saved_messages

    @ property
    def std_datetime_format(self):
        return self.bot.std_date_time_format

    @ property
    def auto_accept_user_dict(self):
        if os.path.isfile(self.auto_accept_user_file) is False:
            writejson({}, self.auto_accept_user_file)
        return loadjson(self.auto_accept_user_file)

    async def get_team_from_emoji(self, emoji_name):
        for key, value in self.command_emojis.items():
            if value == emoji_name:
                return key
        raise KeyError(f'emoji "{emoji_name}" is not associated with any team')

# endregion [Properties]

# region [Listener]

    async def _suggestion_listen_checks(self, payload):
        command_name = "suggestion_reaction_listener"
        if get_command_enabled(command_name) is False:
            return False

        channel = self.bot.get_channel(payload.channel_id)
        emoji = payload.emoji

        message = await channel.fetch_message(payload.message_id)

        if message.author.bot is True:
            return False

        reaction_member = payload.member
        if reaction_member.bot is True:
            return False

        if channel.type is not discord.ChannelType.text:
            return False

        if channel.name.casefold() not in self.allowed_channels(command_name):
            return False

        if all(role.name.casefold() not in self.allowed_roles(command_name) for role in reaction_member.roles):
            return False

        emoji_name = normalize_emoji(emoji.name)
        if emoji_name not in {value for key, value in self.command_emojis.items()} and emoji_name not in self.categories_emojis and emoji_name not in {value for key, value in self.vote_emojis.items()}:

            return False

        if self.bot.is_blacklisted(reaction_member) is True:
            return False

        return True

    @ commands.Cog.listener(name="on_raw_reaction_add")
    async def suggestion_reaction_listener(self, payload):
        if self.ready is False:
            return
        try:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            emoji_name = normalize_emoji(payload.emoji.name)
            if emoji_name in [self.vote_emojis['upvote'], self.vote_emojis['downvote']] and message.id in await self.saved_messages():
                await self._change_votes(message, emoji_name)

                if await self._suggestion_listen_checks(payload) is False:
                    return

            reaction_user = await self.bot.fetch_user(payload.user_id)

            if emoji_name in [value for key, value in self.command_emojis.items()]:
                team = await self.get_team_from_emoji(emoji_name)
                is_new = await self._new_suggestion(channel, message, reaction_user, team)
                if str(message.author.id) not in self.auto_accept_user_dict and is_new is True:
                    _embed_data = await self.bot.make_generic_embed(title="Your suggestion has been saved by the dev team",
                                                                    description="The devs have saved your in their Database to locate it more easily",
                                                                    thumbnail="save",
                                                                    fields=[self.bot.field_item(name="If You Do Not Want This", value=f"DM me: `@{self.bot.display_name} unsave_suggestion {message.id}`", inline=False),
                                                                            self.bot.field_item(name="If You Want To See All Data Saved From You", value=f"DM me: `@{self.bot.display_name} request_my_data`", inline=False),
                                                                            self.bot.field_item(name="If You Want To Have All Data Saved From You Deleted", value=f"DM me: `@{self.bot.display_name} remove_all_userdata`", inline=False),
                                                                            self.bot.field_item(name="If you dont want to receive this message anymore íf your suggestion is saved", value=f"DM me: `@{self.bot.display_name} auto_accept_suggestions`")])
                    await message.author.send(**_embed_data)

            elif emoji_name in self.categories_emojis and message.id in await self.saved_messages():
                log.debug('category change triggered')
                await self._change_category(channel, message, emoji_name)

        except discord.errors.NotFound:
            return

# endregion [Listener]

# region [Commands]

    @auto_meta_info_command()
    @ allowed_channel_and_allowed_role(in_dm_allowed=True)
    async def mark_discussed(self, ctx, *suggestion_ids: int):
        embed_dict = {}
        for suggestion_id in suggestion_ids:
            await self.data_storage_handler.mark_discussed(suggestion_id)
            embed_dict['message_with_id_' + str(suggestion_id)] = 'was marked as discussed'
        await ctx.send(embed=await make_basic_embed(title='Marked Suggestions as discussed', text='The following items were marked as discussed: ', symbol='update', ** embed_dict))

    @ auto_meta_info_command()
    async def clear_all_suggestions(self, ctx, sure: bool = False):
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
                await ctx.send(embed=await make_basic_embed(title='No answer received', text='canceling request to delete Database, nothing was deleted', symbol='cancelled'))
                await question_msg.delete()
        else:
            await self._clear_suggestions(ctx, 'yes')

    @ auto_meta_info_command()
    @ commands.dm_only()
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

    @ auto_meta_info_command()
    @ commands.dm_only()
    async def unsave_suggestion(self, ctx, suggestion_id: int):
        if suggestion_id not in await self.saved_messages():

            await ctx.send(embed=await make_basic_embed(title=f'ID {suggestion_id} not found',
                                                        text='We have no message saved with this ID',
                                                        symbol='not_possible',
                                                        if_you_feel_like_this_is_an_error_please_contact=self.notify_contact_member))
            return
        suggestion = await self.data_storage_handler.get_suggestion_by_id(suggestion_id)
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
                await self.data_storage_handler.remove_suggestion_by_id(suggestion_id)
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

    @ auto_meta_info_command()
    @ allowed_channel_and_allowed_role(in_dm_allowed=True)
    async def get_all_suggestions(self, ctx, report_template: str = "basic_report.html.jinja"):

        query = await self.data_storage_handler.get_all_suggestion_not_discussed()
        var_dict = {'all_suggestions': query, 'style_sheet': "basic_report_style.css"}
        log.debug('getting template')
        template = self.jinja_env.get_template(report_template)
        log.debug('creating Tempdir')
        with TemporaryDirectory() as tempfold:
            html_path = pathmaker(tempfold, "suggestion_report.html")
            pdf_path = pathmaker(tempfold, 'suggestion_report.pdf')
            log.debug('rendering template and writing to file')
            writeit(html_path, await self.bot.execute_in_thread(template.render, var_dict))
            log.debug('copying stylesheet')
            shutil.copyfile(self.css_files.get('basic_report_style.css')[0], pathmaker(tempfold, self.css_files.get('basic_report_style.css')[1]))
            log.debug('transforming html to pdf')

            weasy_html = HTML(filename=html_path)
            weasy_html.write_pdf(pdf_path)

            file = discord.File(pdf_path, filename='suggestion_report.pdf')
            log.debug('sending file')
            await ctx.send(file=file)

    @ auto_meta_info_command()
    @ commands.dm_only()
    async def remove_all_userdata(self, ctx):
        user = ctx.author
        all_user_data = await self.data_storage_handler.get_suggestions_per_author(user.name)
        if len(all_user_data) == 0:
            # TODO: make as embed
            await ctx.send("We have no data stored from you | if you feel like this is an error please contact: " + self.notify_contact_member)
            return
            # TODO: make as embed
        await ctx.send("Do you really all your suggestion stored by the dev team deleted from the Database?\n\nPossible Answers: YES, NO\nTime to answer: 30sec")

        def check(m):
            return m.author.name == ctx.author.name and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            if 'yes' in msg.content.casefold():
                for row in all_user_data:
                    await self.data_storage_handler.remove_suggestion_by_id(row['message_discord_id'])
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

    @ auto_meta_info_command()
    @ commands.dm_only()
    async def request_my_data(self, ctx):
        user = ctx.author
        all_user_data = await self.data_storage_handler.get_suggestions_per_author(user.name)
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

    async def _add_suggestion(self, suggestion_item: SUGGESTION_DATA_ITEM, extra_data=None):
        if extra_data is not None:
            _path = pathmaker(APPDATA['suggestion_extra_data'], extra_data[0])
            with open(_path, 'wb') as extra_data_file:
                extra_data_file.write(extra_data[1])
            suggestion_item = suggestion_item._replace(extra_data=(extra_data[0], _path))
        try:
            await self.data_storage_handler.add_suggestion(suggestion_item)
            return True, suggestion_item
        except sqlite.Error as error:
            log.error(error)
            return False, suggestion_item

    async def _set_category(self, category, message_id):
        try:
            await self.data_storage_handler.update_category(category, message_id)
            return True
        except sqlite.Error as error:
            log.error(error)
            return False

    async def _clear_suggestions(self, ctx, answer):
        if answer.casefold() == 'yes':
            # TODO: make as embed
            await ctx.send('deleting Database')
            await self.data_storage_handler.clear()
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
        _filtered_content = f"```fix\n{_filtered_content.strip()}\n```"

        if len(_filtered_content) >= 900:
            _filtered_content = _filtered_content[:900] + '...```'
        embed = discord.Embed(title="**Suggestion was Saved!**", description=f"Your suggestion was saved for the {suggestion_item.team.replace('_',' ').title()}.\n\n", color=0xf2ea48)
        embed.set_thumbnail(url=EMBED_SYMBOLS.get('save', None))
        embed.add_field(name="Title:", value=f"__{suggestion_item.name}__", inline=False)
        if COGS_CONFIG.getboolean(self.config_name, 'add_success_embed_verbose') is True:
            embed.add_field(name="Author:", value=f"*{suggestion_item.message_author.name}*", inline=True)
            embed.add_field(name="Content:", value=_filtered_content, inline=True)
            embed.add_field(name='Saved Timestamp:', value=suggestion_item.time.isoformat(timespec='seconds'), inline=False)

        extra_data_value = ['No attachments detected'] if suggestion_item.extra_data is None else suggestion_item.extra_data[0]
        embed.add_field(name='Attachments', value=f"`{extra_data_value}`")
        embed.set_footer(text=DEFAULT_FOOTER)
        return embed

    async def make_changed_category_embed(self, message, category):
        embed = discord.Embed(title="**Updated Suggestion Category**", description="I updated the category an Suggestion\n\n", color=0xf2a44a)
        embed.set_thumbnail(url=EMBED_SYMBOLS.get('update', None))
        embed.add_field(name="New Category:", value=category, inline=False)
        embed.add_field(name="Suggestion:", value=message.jump_url, inline=False)
        embed.set_footer(text=DEFAULT_FOOTER)

        return embed

    async def make_already_saved_embed(self):
        embed = discord.Embed(title="**This Suggestion was already saved!**", description="I did not save the Suggestion as I have it already saved", color=0xe04d7e)
        embed.set_thumbnail(url=EMBED_SYMBOLS.get('not_possible', None))
        embed.set_footer(text=DEFAULT_FOOTER)

        return embed


# endregion [Embeds]

# region [HelperMethods]


    async def _collect_title(self, content):
        name_result = self.suggestion_name_regex.search(content)
        if name_result:
            name = name_result.group('name')
            name = None if len(name) > 100 else name.strip().title()
        else:
            name = None
        return name

    async def specifc_reaction_from_message(self, message, target_reaction):
        for reaction in message.reactions:
            if normalize_emoji(reaction.emoji) == target_reaction:
                return reaction

    async def _new_suggestion(self, channel, message, reaction_user, team):
        if message.id in await self.saved_messages():
            await channel.send(embed=await self.make_already_saved_embed())
            return False

        message_member = await self.bot.retrieve_antistasi_member(message.author.id)
        reaction_member = await self.bot.retrieve_antistasi_member(reaction_user.id)
        now_time = datetime.utcnow()
        name = await self._collect_title(message.content)
        extra_data = (message.attachments[0].filename, await message.attachments[0].read()) if len(message.attachments) != 0 else None

        suggestion_item = SUGGESTION_DATA_ITEM(name=name, message_author=message_member, reaction_author=reaction_member, message=message, time=now_time, team=team)

        was_saved, suggestion_item = await self._add_suggestion(suggestion_item, extra_data)
        log.info("saved new suggestion, suggestion name: '%s', suggestion author: '%s', saved by: '%s', suggestion has extra data: '%s'",
                 name,
                 message_member.name,
                 reaction_member.name,
                 'yes' if extra_data is not None else 'no')

        if was_saved is True:
            await channel.send(embed=await self.make_add_success_embed(suggestion_item), delete_after=120)
        return True

    async def _remove_previous_categories(self, target_message, new_emoji_name):
        for reaction_emoji in self.categories_emojis:
            if reaction_emoji is not None and reaction_emoji != new_emoji_name:
                other_reaction = await self.specifc_reaction_from_message(target_message, reaction_emoji)
                if other_reaction is not None:
                    await other_reaction.clear()

    async def _change_category(self, channel, message, emoji_name):
        category = await self.get_category_name(emoji_name)
        if category:
            success = await self._set_category(category, message.id)
            if success:
                await channel.send(embed=await self.make_changed_category_embed(message, category), delete_after=30)
                log.info("updated category for suggestion (id: %s) to category '%s'", message.id, category)
                await self._remove_previous_categories(message, emoji_name)

    async def _change_votes(self, message, emoji_name):
        reaction = await self.specifc_reaction_from_message(message, emoji_name)
        _count = reaction.count
        await self.data_storage_handler.update_votes(emoji_name, _count, message.id)
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
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))
# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(SaveSuggestionCog(bot)))
