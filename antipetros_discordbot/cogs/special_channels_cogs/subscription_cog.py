

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from textwrap import dedent
import asyncio
from datetime import datetime
import random
from tempfile import TemporaryDirectory
from copy import deepcopy
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands
import discord
from emoji import emoji_count
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import make_config_name, delete_message_if_text_channel
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, allowed_channel_and_allowed_role, owner_or_admin, log_invoker, has_attachments
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogState, UpdateTypus
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.gidtools_functions import writejson, loadjson, pathmaker, pickleit, get_pickled, writeit, readit
from antipetros_discordbot.engine.replacements import auto_meta_info_command
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file
from antipetros_discordbot.utility.named_tuples import EmbedFieldItem


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


class TopicItem:
    def __init__(self,
                 name,
                 emoji: str,
                 creator: discord.Member,
                 subscription_channel: discord.TextChannel,
                 message: discord.Message = None,
                 role: discord.Role = None,
                 description: str = None,
                 color: str = None,
                 image: str = None):

        self.subscription_channel = subscription_channel
        self.name = name
        self.emoji = emoji
        self.creator = creator
        self.message = message
        self.role = role
        self.description = '' if description is None else description
        self.color = 'random' if color is None else color
        self.image = image

    @property
    def embed_data(self):
        return {"title": self.name,
                'description': self.description,
                "timestamp": self.creation_time,
                "author": {"name": self.creator.display_name,
                           "icon_url": self.creator.avatar_url},
                "fields": [EmbedFieldItem(name="Subscribe!", value=f"press {self.emoji}"),
                           EmbedFieldItem(name='Subscriber Role', value=self.mention),
                           EmbedFieldItem(name="Created by", value=self.creator.mention)],
                "color": self.color,
                "image": self.image,
                "thumbnail": "subscription"}

    @property
    def creation_time(self):
        if self.role is None:
            return datetime.utcnow()
        return self.role.created_at

    @property
    def mention(self):
        if self.role is None:
            return f"`@{self.name}_Subscriber`"
        return self.role.mention

    @classmethod
    async def from_data(cls,
                        bot,
                        subscription_channel,
                        name: str,
                        emoji: str,
                        creator_id: int,
                        message_id: int,
                        role_id: int,
                        description,
                        color: str,
                        image: str = None):

        creator = await bot.retrieve_antistasi_member(creator_id)
        message = await subscription_channel.fetch_message(message_id)
        role = await bot.retrieve_antistasi_role(role_id)
        return cls(name=name,
                   emoji=emoji,
                   creator=creator,
                   message=message,
                   subscription_channel=subscription_channel,
                   role=role,
                   description=description,
                   color=color,
                   image=image)

    async def serialize(self):
        return {"name": self.name,
                "emoji": self.emoji,
                "creator_id": self.creator.id,
                "message_id": self.message.id,
                "role_id": self.role.id,
                "description": self.description,
                "color": self.color,
                "image": self.image}


class SubscriptionCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Organizes Topic so they can be subscribed and mentioned selectively.
    """
    # region [ClassAttributes]

    config_name = CONFIG_NAME
    topics_data_file = pathmaker(APPDATA['json_data'], 'subscription_topics_data.json')
    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.FEATURE_MISSING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 05:19:50")}

    required_config_data = dedent("""
                                  """)

    # endregion[ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        self.topics = []
        self.ready = False

        glog.class_init_notification(log, self)

# endregion[Init]

# region [Setup]

    async def on_ready_setup(self):
        await self._load_topic_items()
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Properties]


    @property
    def subscription_channel(self):
        name = COGS_CONFIG.retrieve(self.config_name, 'subscription_channel', typus=str, direct_fallback=None)
        if name is None:
            return None
        return self.bot.sync_channel_from_name(name)

    @property
    def topic_data(self):
        if os.path.isfile(self.topics_data_file) is False:
            writejson([], self.topics_data_file)
        return loadjson(self.topics_data_file)

# endregion[Properties]

# region [Listener]

    @commands.Cog.listener(name='on_raw_reaction_add')
    async def subscription_reaction(self, payload):
        if self.ready is False:
            return
        try:
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
                await reaction_user.send(f"You already have the role `{topic.role.name}`.\nThis should not have been possible, please contact Giddi!")
                return
            await self._give_topic_role(reaction_user, topic)
            await self.sucess_subscribed_embed(reaction_user, topic)

        except discord.errors.NotFound:
            return

    @commands.Cog.listener(name='on_raw_reaction_remove')
    async def unsubscription_reaction(self, payload):
        if self.ready is False:
            return
        try:
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
            if topic.role not in reaction_user.roles:
                return
            await self._remove_topic_role(reaction_user, topic)
            await self.sucess_unsubscribed_embed(reaction_user, topic)
        except discord.errors.NotFound:
            return

# endregion[Listener]

# region [Helper]

    async def _get_header_message(self):
        msg_id = COGS_CONFIG.retrieve(self.config_name, 'header_message_id', typus=int, direct_fallback=0)
        if msg_id == 0:
            return None
        return await self.subscription_channel.fetch_message(msg_id)

    async def _add_topic_data(self, topic_item):
        current_data = self.topic_data
        current_data.append(await topic_item.serialize())
        writejson(current_data, self.topics_data_file)

    async def _remove_topic_data(self, topic_item: TopicItem):
        current_data = self.topic_data
        current_data.remove(await topic_item.serialize())
        writejson(current_data, self.topics_data_file)

    async def _save_topic_data(self):
        writejson([await item.serialize() for item in self.topics], self.topics_data_file)
        await self._load_topic_items()

    async def _clear_other_emojis(self, topic_item):
        pass

    async def _post_new_topic(self, topic_item: TopicItem):
        embed_data = await self.bot.make_generic_embed(**topic_item.embed_data)
        msg = await self.subscription_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        await msg.add_reaction(topic_item.emoji)
        topic_item.message = msg

    async def _remove_topic_role(self, member: discord.Member, topic_item: TopicItem):
        await member.remove_roles(topic_item.role, reason=f'User unsibscribed from topic "{topic_item.name}"')
        log.info(f"removed role {topic_item.role.name} to {member.display_name}")

    async def _give_topic_role(self, member: discord.Member, topic_item):
        await member.add_roles(topic_item.role, reason=f"User subscribed to Topic '{topic_item.name}'")
        log.info(f"assigned role {topic_item.role.name} to {member.display_name}")

    async def _load_topic_items(self):
        self.topics = []
        data = self.topic_data
        for item in data:
            topic_item = await TopicItem.from_data(self.bot, self.subscription_channel, **item)
            self.topics.append(topic_item)

    async def convert_hex_color(self, color):
        h = color.lstrip('#')
        rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        return discord.Color.from_rgb(*rgb)

    async def _create_topic_role(self, topic_item: TopicItem):
        """
        Creates the new subscriber role.

        Role has not permissions, but is mentionable.

        Args:
            topic_item (`TopicItem`): The container holding the Topic information.

        """
        log.debug(f"Trying to create role '{topic_item.name}_Subscriber'")
        new_role = await self.bot.antistasi_guild.create_role(name=f"{topic_item.name}_Subscriber", permissions=discord.Permissions.none(), mentionable=False, color=discord.Color.lighter_gray(), reason=f"Subscribe-able Topic creation, topic: '{topic_item.name}'")
        # await new_role.edit(position=0, reason=f"Subscribe-able Topic creation, topic: '{topic_item.name}'")
        topic_item.role = new_role
        log.debug(f"finished creating role '{topic_item.name}_Subscriber'")

    async def _create_topic_subscription_header_embed(self):
        embed_data = await self.bot.make_generic_embed(title="Topic Subscription", description=COGS_CONFIG.retrieve(self.config_name, 'header_description', typus=str, direct_fallback=''),
                                                       fields=[self.bot.field_item(name='How to subscribe', value=">>> " + COGS_CONFIG.retrieve(self.config_name, 'header_how_to_subscribe_text', typus=str, direct_fallback='')),
                                                               self.bot.field_item(name='How to unsubscribe', value=">>> " + COGS_CONFIG.retrieve(self.config_name, 'header_how_to_unsubscribe_text', typus=str, direct_fallback='')),
                                                               self.bot.field_item(name='How does it work', value=">>> " + COGS_CONFIG.retrieve(self.config_name, 'header_how_does_it_work_text', typus=str, direct_fallback=''))],
                                                       color=COGS_CONFIG.retrieve(self.config_name, 'header_color', typus=str, direct_fallback='gray'),
                                                       thumbnail=COGS_CONFIG.retrieve(self.config_name, 'header_thumbnail', typus=str, direct_fallback='antistasi_logo'))

        return embed_data

    async def _get_subscription_channel(self):
        name = COGS_CONFIG.retrieve(self.config_name, 'subscription_channel', typus=str, direct_fallback=None)
        if name is None:
            return None
        return await self.bot.channel_from_name(name)

    async def _remove_subscription_reaction(self, member: discord.member, topic_item: TopicItem):
        message = topic_item.message
        await message.remove_reaction(topic_item.emoji, member)

    async def _send_topic_remove_notification(self, topic_item: TopicItem):
        role = topic_item.role
        for member in role.members:
            embed_data = await self.bot.make_generic_embed(title=f"Topic {topic_item.name} was removed!",
                                                           description=f"The Topic `{topic_item.name}` was removed as a topic, therefor the assigned role {topic_item.role.mention} has been removed from your account!")
            await member.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
            await asyncio.sleep(0.25)

    async def sucess_subscribed_embed(self, member: discord.Member, topic: TopicItem):
        embed_data = await self.bot.make_generic_embed(title="Successfully Subscribed", description=f"You are now subscribed to {topic.name} and will get pinged if they have an Announcement.",
                                                       thumbnail="subscribed",
                                                       fields=[self.bot.field_item(name="Subscription Role", value=f"For this purpose you have been assigne the Role `{topic.role.name}`", inline=False),
                                                               self.bot.field_item(name="Unsubscribe", value=f"To Unsubscribe just remove your emoji from the subscription post [link to post]({topic.message.jump_url})", inline=False),
                                                               self.bot.field_item(name="Unsubscribe Command", value=f"You can also use the command `@AntiPetros unsubscribe {topic.name}`", inline=False)])
        await member.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    async def sucess_unsubscribed_embed(self, member: discord.Member, topic: TopicItem):
        embed_data = await self.bot.make_generic_embed(title="Successfully Unsubscribed", description=f"You are now no longer subscribed to {topic.name} and will NOT get pinged anymore if they have an Announcement.",
                                                       thumbnail="update",
                                                       fields=[self.bot.field_item(name="Subscription Role", value=f"The Role {topic.role.name} has been removed", inline=False)])
        await member.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    async def _confirm_topic_creation_deletion(self, ctx: commands.Context, topic_item: TopicItem, typus: str):
        topic_embed_data = await self.bot.make_generic_embed(**topic_item.embed_data)
        description = f"Are you sure you want to create the Topic `{topic_item.name}`, with the following subscription message?" if typus == 'creation' else f"Are you sure you want to REMOVE the topic `{topic_item.name}`, with that subscription message above?"
        confirmation_embed_data = await self.bot.make_generic_embed(title='Confirmation Required',
                                                                    description=description,
                                                                    fields=[self.bot.field_item(name='Time to answer', value="5 minutes"),
                                                                            self.bot.field_item(name='To Confirm', value='React with ✅ to this message', inline=True),
                                                                            self.bot.field_item(name='To Cancel', value="React with ❎ to this message", inline=True)])
        topic_embed_message = await ctx.send(**topic_embed_data, allowed_mentions=discord.AllowedMentions.none())
        conformation_message = await ctx.send(**confirmation_embed_data)

        await conformation_message.add_reaction("✅")
        await conformation_message.add_reaction("❎")

        def check_confirm(payload: discord.RawReactionActionEvent):
            return payload.message_id == conformation_message.id and payload.user_id == ctx.author.id and str(payload.emoji) in ['✅', '❎']
        try:
            payload = await self.bot.wait_for('raw_reaction_add', timeout=300.0, check=check_confirm)
            if ctx.channel.type is discord.ChannelType.text:
                await conformation_message.delete()
                await topic_embed_message.delete()
        except asyncio.TimeoutError:
            description = "Cancelling Topic Creation because not answer was received" if typus == 'creation' else "Cancelling Topic Removal because no answer was received"
            embed_data = await self.bot.make_generic_embed(title="Timed Out!", description=description, thumbnail="timeout")
            await ctx.send(**embed_data)
            if ctx.channel.type is discord.ChannelType.text:
                await conformation_message.delete()
                await topic_embed_message.delete()

            return False
        if str(payload.emoji) == '❎':
            description = "Stopping Topic creation" if typus == 'creation' else "Stopping Topic removal"
            embed_data = await self.bot.make_generic_embed(title='USER CANCELATION', description=description, thumbnail="cancelled")
            await ctx.send(**embed_data)
            return False
        if str(payload.emoji) == '✅':
            description = 'Topic creation confirmed, creating topic...' if typus == 'creation' else "Topic REMOVAL Confirmed, removing topic..."
            embed_data = await self.bot.make_generic_embed(title="Confirmed", description=description, thumbnail="confirmed")
            await ctx.send(**embed_data)
            return True

    async def _update_topic_embed(self, topic_item: TopicItem):
        embed_data = await self.bot.make_generic_embed(**topic_item.embed_data)
        await topic_item.message.edit(**embed_data)

# endregion[Helper]

# region [Commands]

    @auto_meta_info_command(enabled=get_command_enabled('create_subscription_channel_header'))
    @commands.is_owner()
    async def create_subscription_channel_header(self, ctx: commands.Context):
        embed_data = await self._create_topic_subscription_header_embed()
        header_message = await self.subscription_channel.send(**embed_data)
        COGS_CONFIG.set(self.config_name, 'header_message_id', str(header_message.id))
        await delete_message_if_text_channel(ctx)

    @auto_meta_info_command(enabled=get_command_enabled('remove_topic'))
    @commands.is_owner()
    async def update_subscription_channel_header(self, ctx: commands.Context):
        embed_data = await self._create_topic_subscription_header_embed()
        header_message = await self._get_header_message()
        await header_message.edit(**embed_data)
        await delete_message_if_text_channel(ctx)

    @auto_meta_info_command(enabled=get_command_enabled('remove_topic'))
    @commands.is_owner()
    async def remove_topic(self, ctx: commands.context, topic_name: str):
        topic_item = {item.name.casefold(): item for item in self.topics}.get(topic_name.casefold(), None)
        if await self._confirm_topic_creation_deletion(ctx, topic_item, 'removal') is False:
            return
        await self._send_topic_remove_notification(topic_item)
        await topic_item.role.delete(reason=f"Topic '{topic_item.name}' was removed")
        await topic_item.message.delete()
        if ctx.channel.type is discord.ChannelType.text:
            await ctx.message.delete()
        log.info(f"Topic '{topic_item.name}' was removed, by {ctx.author.display_name}")

    @auto_meta_info_command(enabled=get_command_enabled('new_topic'))
    @commands.is_owner()
    @has_attachments(1)
    async def new_topic(self, ctx: commands.Context, topic_creator_id: int = None):
        if self.subscription_channel is None:
            await ctx.send('No subscription Channel set in Config!')
            return
        file = ctx.message.attachments[0]
        with TemporaryDirectory() as tempdir:
            path = pathmaker(tempdir, file.filename)
            await file.save(path)
            content = readit(path)
            command_data = await parse_command_text_file(content, {'name', 'emoji', 'color', 'description', 'image'})
        if command_data.get('name') in [None, ""]:
            await ctx.send('Missing required field:\n-__**Name**__\n\naborting!')
            return
        if command_data.get('emoji') in [None, ""]:
            await ctx.send('Missing required field:\n-__**Emoji**__\n\naborting!"')
            return
        if topic_creator_id is None:
            topic_creator = ctx.author
        else:
            topic_creator = await self.bot.retrieve_antistasi_member(topic_creator_id)
        if topic_creator is None:
            await ctx.send(f'Unable to find Creator with id `{topic_creator_id}`')
            return
        if emoji_count(command_data.get('emoji')) == 0:
            await ctx.send(f'Unusable emoji `{command_data.get("emoji")}`')
            return
        item = TopicItem(command_data.get('name'), command_data.get('emoji'), topic_creator, self.subscription_channel, description=command_data.get("description", ""), color=command_data.get('color'), image=command_data.get('image'))
        if await self._confirm_topic_creation_deletion(ctx, item, 'creation') is False:
            return
        try:
            await self._create_topic_role(item)
            await self._post_new_topic(item)

        except Exception as error:
            if item.role is not None:
                await item.role.delete(reason="Error at topic creation")
            if item.message is not None:
                await item.message.delete(reason="Error at topic creation")
            raise error

        await self._add_topic_data(item)
        self.topics.append(item)
        if ctx.channel.type is discord.ChannelType.text:
            await ctx.message.delete()
        log.info(f"Topic '{item.name}' was created, by {ctx.author.display_name}")

    @auto_meta_info_command()
    @commands.is_owner()
    @has_attachments(1)
    async def modify_topic_embed(self, ctx: commands.Context, topic_name: str, setting: str, value: str):
        allowed_setting_names = ['color', 'image', 'description']
        if setting.casefold() not in allowed_setting_names:
            await ctx.send(f'Setting {setting} is not a valid setting to modify, aborting!')
            return
        topic_item = {item.name.casefold(): item for item in self.topics}.get(topic_name.casefold(), None)

        setattr(topic_item, setting.casefold(), value)
        await self._update_topic_embed(topic_item)
        await self._save_topic_data()

    @auto_meta_info_command(enabled=True)
    @commands.dm_only()
    async def unsubscribe(self, ctx: commands.Context, topic_name: str):
        topic_item = {item.name.casefold(): item for item in self.topics}.get(topic_name.casefold(), None)
        if topic_item is None:
            # TODO: Custom Error and handling
            await ctx.send(f'unable to find a Topic with the name `{topic_name}`')
            return
        member = await self.bot.retrieve_antistasi_member(ctx.author.id)
        if topic_item.role not in member.roles:
            # TODO: Custom Error and handling
            await ctx.send(f'You are currently not subscribed to the topic `{topic_name}`')
            return
        await self._remove_subscription_reaction(member, topic_item)
        await self._remove_topic_role(member, topic_item)
        await self.sucess_unsubscribed_embed(member, topic_item)

    @auto_meta_info_command(enabled=True)
    @owner_or_admin()
    async def topic_template(self, ctx: commands.Context, with_example: str = None):
        embed_data = await self.bot.make_generic_embed(title="Topic Template File",
                                                       description='Please use this file to create a topic. You can then use the filled File as an attachment for the command `@AntiPetros new_topic`.\nPlease obey the following rules!',
                                                       fields=[self.bot.field_item(name='Field -> **Name**',
                                                                                   value="Preferable to not use spaces in the Name, use `_`. Names can contains spaces, but better if not."),
                                                               self.bot.field_item(name="Field -> **Emoji**",
                                                                                   value="Only Unicode Emojis are allowed, no custom emojis!\nYou can search and copy Unicode emojis [on this site](https://emojipedia.org/)"),
                                                               self.bot.field_item(name="Field -> **Color** __[OPTIONAL]__",
                                                                                   value="This field takes a color name, case insensitive, if the color isn't int he bots color list, it uses a random color."),
                                                               self.bot.field_item(name="Field -> **Image** __[OPTIONAL]__",
                                                                                   value="Https Link to an image, you can use any Image Hosting to be able to use a local image, by uploading it there."),
                                                               self.bot.field_item(name="Field -> **Describtion** __[OPTIONAL]__",
                                                                                   value="Can be multiline, just be aware that there is a character limit, so don't go overboard. The bot will give you an Error message if it is to long."),
                                                               self.bot.field_item(name="**Optional Fields**",
                                                                                   value="If you do not want to use an optional field, remove the line completely. The Keyword before the `=` and the stuff after it.")])

        template_file = discord.File(APPDATA['topic_template.txt'])
        await ctx.send(**embed_data)
        if with_example is not None and with_example.casefold() == 'example':
            example_file = discord.File(APPDATA['topic_example.txt'])
            await ctx.send(files=[template_file, example_file])
        else:
            await ctx.send(file=template_file)

    # @auto_meta_info_command(hidden=True, enabled=True)
    # @owner_or_admin()
    # async def delete_test_role(self, ctx: commands.Context, role: discord.Role):
    #     role_name = role.name
    #     await role.delete(reason='Was for testing, and threw an error, cleaning up')
    #     await ctx.send(f"`{role_name}` was removed", delete_after=60)

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
