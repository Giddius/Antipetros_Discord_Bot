# * Third Party Imports -->
import discord

async def add_to_embed_listfield(embed: discord.Embed, field_name: str, items: list, prefix: str = None, in_line: bool = False):
    _value = []
    for item in items:
        item = f"{prefix}\t`{str(item)}`" if prefix is not None else f"`{str(item)}`"
        _value.append(item)
    embed.add_field(name=field_name, value='\n' + '\n'.join(_value), inline=in_line)
