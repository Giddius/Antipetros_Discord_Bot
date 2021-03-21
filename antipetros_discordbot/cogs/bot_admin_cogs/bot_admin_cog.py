

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from datetime import datetime, timedelta
from textwrap import dedent
import random
import asyncio
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import commands, tasks
import gc
from icecream import ic
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import make_config_name, seconds_to_pretty
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, log_invoker, owner_or_admin
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogState
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.gidtools_functions import pathmaker, writejson, loadjson
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import make_message_list
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)


# endregion[Logging]

# region [Constants]
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
COG_NAME = "BotAdminCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)
# endregion[Constants]


class BotAdminCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Commands and methods that are needed to Administrate the Bot itself.
    """
    config_name = CONFIG_NAME
    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.FEATURE_MISSING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 05:19:50",
                             "b0fabfbd25ed7b45a009737879c2ef61262acce2c3e9043d7b2b27e51f6cd8de27fea94d52e1f97739765b4629d534de76bf28b241c5f27bd96917f3eb8c7e6e")}

    required_config_data = dedent("""
                                  """)
    alive_phrases_file = pathmaker(APPDATA['fixed_data'], 'alive_phrases.json')
    who_is_trigger_phrases_file = pathmaker(APPDATA['fixed_data'], 'who_is_trigger_phrases.json')

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        self.latest_who_is_triggered_time = datetime.utcnow()

        glog.class_init_notification(log, self)
# region [Setup]

    async def on_ready_setup(self):
        self.garbage_clean_loop.start()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]


# region [Loops]

    @tasks.loop(hours=1)
    async def garbage_clean_loop(self):
        log.info('running garbage clean')
        x = gc.collect()
        log.info('Garbage Clean collected "%s"', x)

# endregion[Loops]

    @property
    def alive_phrases(self):
        if os.path.isfile(self.alive_phrases_file) is False:
            writejson(['I am alive!'], self.alive_phrases_file)
        return loadjson(self.alive_phrases_file)

    @property
    def who_is_trigger_phrases(self):
        std_phrases = ['who is %BOT_NAME%',
                       'what is %BOT_NAME%',
                       'who the fuck is %BOT_NAME%']
        if os.path.isfile(self.who_is_trigger_phrases_file) is False:
            writejson(std_phrases, self.who_is_trigger_phrases_file)
        return loadjson(self.who_is_trigger_phrases_file)

    @commands.Cog.listener(name='on_message')
    async def who_is_this_bot_listener(self, msg: discord.Message):
        command_name = "who_is_this_bot_listener"
        if get_command_enabled(command_name) is False:
            return
        channel = msg.channel
        if channel.type is not discord.ChannelType.text:
            return False

        if channel.name.casefold() not in self.allowed_channels(command_name):
            return False
        if any(trigger_phrase.replace('%BOT_NAME%', self.bot.display_name).casefold() in msg.content.casefold() for trigger_phrase in self.who_is_trigger_phrases):
            log.debug('who_is_this_bot_listener triggered')
            if datetime.utcnow() > self.latest_who_is_triggered_time + timedelta(minutes=1):
                image = self.bot.portrait_url
                embed_data = await self.bot.make_generic_embed(title=f'WHO IS {self.bot.display_name.upper()}', description='I am an custom made Bot for this community!',
                                                               fields=[self.bot.field_item(name='What I can do', value=f'Get a description of my features by using `@{self.bot.display_name} help`', inline=False),
                                                                       self.bot.field_item(name='Who created me', value=f'I was created by {self.bot.creator.member_object.mention}, for the Antistasi Community')],
                                                               image=image,
                                                               thumbnail=None)
                await msg.reply(**embed_data, delete_after=60)
                log.info("'%s' was triggered by '%s' in '%s'", command_name, msg.author.name, msg.channel.name)
                self.latest_who_is_triggered_time = datetime.utcnow()

            await msg.delete()

    @auto_meta_info_command(enabled=True)
    @owner_or_admin()
    async def tell_version(self, ctx: commands.Context):
        embed_data = await self.bot.make_generic_embed(title=self.bot.display_name.title(), description='**Version**  ' + str(os.getenv('ANTIPETROS_VERSION')),
                                                       thumbnail=self.bot.portrait_url)
        await ctx.send(**embed_data)

    @auto_meta_info_command(enabled=True)
    @owner_or_admin()
    @log_invoker(log, "warning")
    async def add_who_is_phrase(self, ctx, *, phrase: str):
        current_phrases = self.who_is_trigger_phrases

        if phrase.casefold() in map(lambda x: x.casefold(), current_phrases):
            await ctx.send(f'phrase `{phrase}` already in `who_is_trigger_phrases`')
            return
        current_phrases.append(phrase)
        writejson(current_phrases, self.who_is_trigger_phrases_file)
        await ctx.send(f"Added phrase `{phrase}` to `who_is_trigger_phrases`")

    @ auto_meta_info_command(enabled=True, aliases=['you_dead?', 'are-you-there', 'poke-with-stick'])
    async def life_check(self, ctx: commands.Context):
        if random.randint(0, len(self.alive_phrases)) == 0:
            file = discord.File(APPDATA['bertha.png'])
            await ctx.reply('My assistent will record your command for me, please speak into her Banhammer', file=file)
            return
        await ctx.reply(random.choice(self.alive_phrases))

    @ auto_meta_info_command(enabled=True)
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def add_to_blacklist(self, ctx, user: discord.Member):

        if user.bot is True:
            # TODO: make as embed
            await ctx.send("the user you are trying to add is a **__BOT__**!\n\nThis can't be done!")
            return
        blacklisted_user = await self.bot.blacklist_user(user)
        if blacklisted_user is not None:
            await ctx.send(f"User '{user.name}' with the id '{user.id}' was added to my blacklist, he wont be able to invoke my commands!")
        else:
            await ctx.send("Something went wrong while blacklisting the User")

    @ auto_meta_info_command(enabled=True)
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def remove_from_blacklist(self, ctx, user: discord.Member):

        await self.bot.unblacklist_user(user)
        await ctx.send(f"I have unblacklisted user {user.name}")

    @ auto_meta_info_command(enabled=True)
    async def tell_uptime(self, ctx):

        now_time = datetime.utcnow()
        delta_time = now_time - self.bot.start_time
        seconds = round(delta_time.total_seconds())
        # TODO: make as embed
        await ctx.send(f"__Uptime__ -->\n| {str(seconds_to_pretty(seconds))}")

    @auto_meta_info_command(enabled=True)
    @commands.is_owner()
    async def self_announcement(self, ctx: commands.Context, channel: discord.TextChannel, test: bool = False):

        if COGS_CONFIG.retrieve(self.config_name, 'self_announcement_made', typus=bool, direct_fallback=True) is True:
            return

        creator_mention = self.bot.creator.member_object.mention
        seperator = '━' * 25
        pre_embed = await self.bot.make_generic_embed(title='ANNOUNCEMENT\nfrom\n~~ the Party Leadership ~~\nthe Antistasi Leadership',
                                                      description="\n***Please direct your eyes to the mandatory Telescreens and await the announcement***",
                                                      image="https://raw.githubusercontent.com/official-antistasi-community/Antipetros_Discord_Bot/development/art/finished/images/bot_announcement.png",
                                                      footer=None)

        embed_data = await self.bot.make_generic_embed(title=f"LET THIS DATE LIVE IN INFAMY\n{ZERO_WIDTH}",
                                                       description="**There is a new Bot in Town".center(75, '$').replace('$', f" {ZERO_WIDTH} ") +
                                                       "\n" + "made from all the Petroses you ever killed".center(75, '$').replace('$', f" {ZERO_WIDTH} ") +
                                                       "\n" + "accidentaly, on purpose or otherwise".center(75, '$').replace('$', f" {ZERO_WIDTH} ") + "\n\n" +
                                                       "He and his Assistent Bertha are here to clean this place up**".center(75, '$').replace('$', f" {ZERO_WIDTH} "),
                                                       image=self.bot.portrait_url,
                                                       thumbnail=None,
                                                       fields=[self.bot.field_item(name=ZERO_WIDTH, value=ZERO_WIDTH, inline=False),
                                                               self.bot.field_item(name=f'**USER HAS JOINED YOUR CHANNEL**\n{ZERO_WIDTH}', value=f'Just call me {self.bot.user.mention}\n{ZERO_WIDTH}', inline=False),
                                                               self.bot.field_item(
                                                                   name=f'**NEW RULES**\n{ZERO_WIDTH}', value=f"**⍟** No more pro or contra Furry fighting, or Bertha puts on her BanBear Fursuite\n{seperator}\n**⍟** If you spam my commands you get Blacklisted!\n{seperator}\n**⍟** Try to break me, but if you succede, let {creator_mention} know\n{seperator}\n**⍟** Not everything in this announcement is serious, but you don't know what is and what is not\n{seperator}\n{ZERO_WIDTH}", inline=False),
                                                               self.bot.field_item(name=f'**WHO CREATED THIS CRIME AGAINST HUMANITY?**\n{ZERO_WIDTH}',
                                                                                   value=f"Direct the angry Mob to {creator_mention}" + f"\n{ZERO_WIDTH}", inline=False),
                                                               self.bot.field_item(name=f"**YOU HAVE SOMETHING TO SAY ABOUT ME?**\n{ZERO_WIDTH}",
                                                                                   value=f"Send {creator_mention} a DM or ping him\n*(he is completely ok with getting pinged)*\ndon't hesitate, you are helping!\n{ZERO_WIDTH}", inline=False),
                                                               self.bot.field_item(name=f'**HOW CAN WE INTERACT WITH YOU?**\n{ZERO_WIDTH}',
                                                                                   value=f'Just use\n\n```fix\n@{self.bot.display_name} [COMMAND]\n```\n\nand\n\n```fix\n@{self.bot.display_name} help\n```\nfor info.\n{ZERO_WIDTH}'),
                                                               self.bot.field_item(name=f"**CAN I SEE THE CODE?**\n{ZERO_WIDTH}", value=f"{embed_hyperlink('Link to Github Repo',self.bot.github_url)}\n{ZERO_WIDTH}", inline=False),
                                                               self.bot.field_item(name=f"**I WANT TO ALSO WORK ON THIS BOT**\n{ZERO_WIDTH}", value=f"Again, {creator_mention}\n{ZERO_WIDTH}", inline=False),
                                                               self.bot.field_item(name=ZERO_WIDTH, value=ZERO_WIDTH, inline=False)],
                                                       footer=None,
                                                       timestamp=datetime.strptime("6666.06.06 06:06", "%Y.%m.%d %H:%M"))
        file = discord.File(APPDATA['announcement.mp3'])
        await channel.send(**pre_embed)
        async with ctx.typing():
            await asyncio.sleep(60)
        await channel.send(file=file)
        async with ctx.typing():
            await asyncio.sleep(20)
        await channel.send(**embed_data)
        if not test:
            COGS_CONFIG.set(self.config_name, 'self_announcement_made', 'yes')
            COGS_CONFIG.save()
        await ctx.message.delete()

    @auto_meta_info_command(enabled=True)
    @commands.is_owner()
    async def send_log_file(self, ctx: commands.Context, which_logs: str = 'newest'):
        """
        Gets the log files of the bot and post it as a file to discord.

        You can choose to only get the newest or all logs.

        Args:
            which_logs (str, optional): [description]. Defaults to 'newest'. other options = 'all'

        Example:
            @AntiPetros send_log_file all
        """
        log_folder = APPDATA.log_folder
        if which_logs == 'newest':

            for file in os.scandir(log_folder):
                if file.is_file() and file.name.endswith('.log'):
                    discord_file = discord.File(file.path)
                    await ctx.send(file=discord_file)

        elif which_logs == 'all':
            for file in os.scandir(log_folder):
                if file.is_file() and file.name.endswith('.log'):
                    discord_file = discord.File(file.path)
                    await ctx.send(file=discord_file)

            for old_file in os.scandir(pathmaker(log_folder, 'old_logs')):
                if old_file.is_file() and old_file.name.endswith('.log'):
                    discord_file = discord.File(old_file.path)
                    await ctx.send(file=discord_file)
        log.warning("%s log file%s was requested by '%s'", which_logs, 's' if which_logs == 'all' else '', ctx.author.name)

    @auto_meta_info_command(enabled=True)
    @commands.is_owner()
    async def invocation_prefixes(self, ctx: commands.Context):
        prefixes = self.bot.command_prefix(self.bot, ctx.message)
        prefixes = sorted(prefixes, key=lambda x: '@' in x, reverse=True)
        mod_prefixes = []
        for prefix in prefixes:
            if not prefix.startswith('<@'):
                prefix = f'{prefix}'
            if '@' in prefix and prefix.replace('!', '') in [prfx.replace('!', '') for prfx in mod_prefixes]:
                pass
            else:
                mod_prefixes.append(prefix)
        embed_data = await self.bot.make_generic_embed(title=f'Invocation Prefixes', description=make_message_list(mod_prefixes),
                                                       thumbnail=None,
                                                       timestamp=None,
                                                       author='bot_author')
        cmsg = await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        await asyncio.sleep(60)
        await cmsg.delete()
        await ctx.message.delete()

    @auto_meta_info_command(enabled=True)
    @commands.is_owner()
    async def all_aliases(self, ctx: commands.Context):
        all_aliases = []
        for command in self.bot.walk_commands():
            if command.aliases:
                all_aliases.append(f"`{command.name}`\n```python\n" + '\n'.join(command.aliases) + "\n```")

        await self.bot.split_to_messages(ctx, '\n\n'.join(all_aliases), split_on='\n\n')

    def cog_check(self, ctx):
        return True

    async def cog_command_error(self, ctx, error):
        pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    def __repr__(self):
        return f"{self.qualified_name}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):
        self.garbage_clean_loop.stop()
        log.debug("Cog '%s' UNLOADED!", str(self))

# region[Main_Exec]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(BotAdminCog(bot)))

# endregion[Main_Exec]