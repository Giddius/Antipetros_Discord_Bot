

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from textwrap import dedent
import asyncio
from datetime import datetime
import random
from tempfile import TemporaryDirectory
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands
import discord
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import make_config_name
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, allowed_channel_and_allowed_role_2, owner_or_admin, log_invoker, has_attachments
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogState
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.gidtools_functions import writejson, loadjson, pathmaker, pickleit, get_pickled, writeit, readit
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file
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
COG_NAME = "SubscriptionCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)
# endregion[Constants]


class FakeRole:
    def __init__(self, name):
        self.name = name
        self.mention = f'@FAKE_{self.name}_FAKE'
        self.id = random.randint(100000, 999999)

    @property
    def created_at(self):
        return datetime.utcnow()


class TopicItem:
    def __init__(self, name, emoji: str, creator, subscription_channel, message=None, role=None, description=None):
        self.subscription_channel = subscription_channel
        self.name = name
        self.emoji = emoji
        self.creator = creator
        self.message = message
        self.role = role
        self.description = '' if description is None else description

    @property
    def role_name(self):
        if self.role is None:
            return f"{self.name}_subscriber"
        return self.role.name

    @property
    def embed_data(self):
        return {"title": self.name, 'description': self.description, "timestamp": self.creation_time, "author": {"name": self.creator.display_name, "icon_url": self.creator.avatar_url}}

    @property
    def creation_time(self):
        return self.role.created_at

    @classmethod
    async def from_data(cls, bot, subscription_channel, name: str, emoji: str, creator_id: int, message_id: int, role_id: int, description):
        creator = await bot.retrieve_antistasi_member(creator_id)
        message = await subscription_channel.fetch_message(message_id)
        role = await bot.retrieve_antistasi_role(role_id)
        return cls(name=name, emoji=emoji, creator=creator, message=message, subscription_channel=subscription_channel, role=role, description=description)

    async def serialize(self):
        return {"name": self.name, "emoji": self.emoji, "creator_id": self.creator.id, "message_id": self.message.id, "role_id": self.role.id, "description": self.description}


class SubscriptionCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Soon
    """
    config_name = CONFIG_NAME
    topics_data_file = pathmaker(APPDATA['json_data'], 'subscription_topics_data.json')
    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.FEATURE_MISSING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 05:19:50")}

    required_config_data = dedent("""
                                  """)

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        self.topics = []
        self.subscription_channel = None

        glog.class_init_notification(log, self)
# region [Setup]

    async def on_ready_setup(self):
        self.subscription_channel = await self._get_subscription_channel()
        await self._load_topic_items()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Properties]


    @property
    def topic_data(self):
        if os.path.isfile(self.topics_data_file) is False:
            writejson([], self.topics_data_file)
        return loadjson(self.topics_data_file)

# endregion[Properties]

# region [Helper]

    @commands.Cog.listener(name='on_raw_reaction_add')
    async def subscription_reaction(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message not in [topic.message for topic in self.topics]:
            return
        topic = {topic.message: topic for topic in self.topics}.get(message)
        emoji_name = normalize_emoji(payload.emoji.name)
        if emoji_name != normalize_emoji(topic.emoji):
            for reaction in message.reactions:
                if normalize_emoji(str(reaction.emoji)) != normalize_emoji(topic.emoji):
                    await message.clear_reaction(reaction.emoji)
            return
        reaction_user = await self.bot.retrieve_antistasi_member(payload.user_id)
        if reaction_user.bot is True:
            return
        if topic.role in reaction_user.roles:
            return
        await self.sucess_subscribed_embed(reaction_user, topic)

    @commands.Cog.listener(name='on_raw_reaction_remove')
    async def unsubscription_reaction(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message not in [topic.message for topic in self.topics]:
            return
        topic = {topic.message: topic for topic in self.topics}.get(message)
        emoji_name = normalize_emoji(payload.emoji.name)
        if emoji_name != normalize_emoji(topic.emoji):
            for reaction in message.reactions:
                if normalize_emoji(str(reaction.emoji)) != normalize_emoji(topic.emoji):
                    await message.clear_reaction(reaction.emoji)
            return
        reaction_user = await self.bot.retrieve_antistasi_member(payload.user_id)
        if reaction_user.bot is True:
            return
        # if topic.role not in reaction_user.roles:
        #     return
        await self.sucess_unsubscribed_embed(reaction_user, topic)

    async def _add_topic_data(self, topic_item):
        current_data = self.topic_data
        current_data.append(await topic_item.serialize())
        writejson(current_data, self.topics_data_file)

    async def _remove_topic_data(self, topic_item):
        current_data = self.topic_data

    async def _clear_other_emojis(self, topic_item):
        pass

    async def _post_new_topic(self, topic_item, color=None, image=None):
        embed_data = await self.bot.make_generic_embed(**topic_item.embed_data, fields=[self.bot.field_item(name="Subscribe!", value=f"press {topic_item.emoji}"), self.bot.field_item(name='Subscriber Role', value=topic_item.role.mention), self.bot.field_item(name="Created by", value=topic_item.creator.mention)], color=color, image=image)
        msg = await self.subscription_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        await msg.add_reaction(topic_item.emoji)
        topic_item.message = msg

    async def _give_topic_role(self, member: discord.Member, topic_item):
        # FAKE: FOR DEMONSTRATION
        await asyncio.sleep(1)
        log.info(f"Fake assigned role {topic_item.role.name}")

    async def _load_topic_items(self):
        data = self.topic_data
        for item in data:
            topic_item = await TopicItem.from_data(self.bot, self.subscription_channel, **item)
            self.topics.append(topic_item)

    async def _create_topic_subscription_channel(self, name, category: discord.CategoryChannel):
        # FAKE: FOR DEMONSTRATION
        await asyncio.sleep(5)
        log.info(f'Fake created_channel {name} in {category.name}')
        self.subscription_channel = await self.bot.channel_from_name('bot-commands')
        COGS_CONFIG.set(self.config_name, 'subscription_channel', self.subscription_channel.name)
        COGS_CONFIG.save()

    async def _create_topic_role(self, topic_item):
        # FAKE: FOR DEMONSTRATION
        new_role = FakeRole(topic_item.role_name)
        topic_item.role = new_role
        return new_role

    async def _create_topic_subscription_header(self, ctx: commands.Context):
        # FAKE: FOR DEMONSTRATION
        new_clothes_command = self.bot.get_command('the_bots_new_clothes')
        await new_clothes_command(ctx)
        embed_data = await self.bot.make_generic_embed(title="Topic Subscription", description="You can Subscribe to certain Topics here, the following messages are the available topics",
                                                       footer={'text': "!!FAKE!! also text is just quickly written and can easily exchanged"},
                                                       fields=[self.bot.field_item(name='How to subscribe', value="Just press the emoji under the message for the topic you want to subscribe"),
                                                               self.bot.field_item(name='How to unsubscribe', value="Just press the emoji again to remove the emoji, you will be automatically unsubscribed"),
                                                               self.bot.field_item(name='How does it work', value="After subscribing you will get a role assigned, if there is an announcment for that topic, it will ping the role and therefore you")])
        await self.subscription_channel.send(**embed_data)

    async def _get_subscription_channel(self):
        name = COGS_CONFIG.retrieve(self.config_name, 'subscription_channel', typus=str, direct_fallback=None)
        if name is None:
            return None
        return await self.bot.channel_from_name(name)

# endregion[Helper]

# region [Commands]
    @auto_meta_info_command(enabled=get_command_enabled('create_subscription_channel'))
    @owner_or_admin()
    async def create_subscription_channel(self, ctx: commands.Context, category: discord.CategoryChannel, name: str):
        if self.subscription_channel is not None:
            await ctx.send('already exists')
            return
        # await ctx.send(f'Fake created_channel {name} in {category.name}')
        await self._create_topic_subscription_channel(name, category)
        # await ctx.send("creating subscription header")
        await self._create_topic_subscription_header(ctx)
        # await ctx.send('done')
        await ctx.message.delete()

    @auto_meta_info_command(enabled=get_command_enabled('add_topic'))
    @has_attachments(1)
    async def new_topic(self, ctx: commands.Context):
        if ctx.channel is not self.subscription_channel:
            return
        file = ctx.message.attachments[0]
        with TemporaryDirectory() as tempdir:
            path = pathmaker(tempdir, file.filename)
            await file.save(path)
            content = readit(path)
            command_data = await parse_command_text_file(content, {'name', 'emoji', 'color', 'description', 'image'})
        item = TopicItem(command_data.get('name'), command_data.get('emoji'), ctx.author, self.subscription_channel, description=command_data.get("description"))
        # await ctx.send("creating role")
        await self._create_topic_role(item)
        # await ctx.send(f"role {item.role_name} created, mentionable as {item.role.mention}", allowed_mentions=discord.AllowedMentions.none())
        # await ctx.send("creating new embed")
        await self._post_new_topic(item, command_data.get("color"), command_data.get("image"))
        # await ctx.send("serializing topic data")
        await self._add_topic_data(item)
        self.topics.append(item)
        await ctx.message.delete()
        # await ctx.send('done')

    async def sucess_subscribed_embed(self, member: discord.Member, topic: TopicItem):
        embed_data = await self.bot.make_generic_embed(title="Successfully Subscribed", description=f"You are now subscribed to {topic.name} and will get pinged if they have an Announcement.",
                                                       thumbnail="subscribed",
                                                       fields=[self.bot.field_item(name="Subscription Role", value=f"For this purpose you have been assigne the Role {topic.role.mention}", inline=False),
                                                               self.bot.field_item(name="Unsubscribe", value=f"To Unsubscribe just remove your emoji from the subscription post [link to post]({topic.message.jump_url})", inline=False),
                                                               self.bot.field_item(name="Unsubscribe Command", value=f"You can also use the command `@AntiPetros unsubscribe [{topic.name}]`]", inline=False)])
        await member.send(**embed_data)

    async def sucess_unsubscribed_embed(self, member: discord.Member, topic: TopicItem):
        embed_data = await self.bot.make_generic_embed(title="Successfully Unsubscribed", description=f"You are now no longer subscribed to {topic.name} and will NOT get pinged anymore if they have an Announcement.",
                                                       thumbnail="update",
                                                       fields=[self.bot.field_item(name="Subscription Role", value=f"The Role {topic.role.mention} has been removed", inline=False)])
        await member.send(**embed_data)

# endregion[Commands]

    def __repr__(self):
        return f"{self.name}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))

# region[Main_Exec]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(SubscriptionCog(bot)))

# endregion[Main_Exec]