from collections import UserDict
from asyncio import sleep, create_task
from discord.ext import commands
from discord.ext.commands import BucketType
from random import seed, randint


class CoolDownDict(UserDict):
    data_lut = {BucketType.role: lambda x: getattr(x, 'author').top_role.id,
                BucketType.channel: lambda x: getattr(x, 'channel').id,
                BucketType.user: lambda x: getattr(x, 'author').id,
                BucketType.category: lambda x: getattr(x, 'channel').name,
                BucketType.guild: lambda x: getattr(x, 'guild').id,
                BucketType.member: lambda x: getattr(x, 'author').id,
                BucketType.default: 100}

    @staticmethod
    def string_to_int(string_data: str, digits: int = 5):
        seed(string_data)
        start = int('1' + ('0' * (digits - 1)))
        stop = int('9' * digits)
        _out = randint(start, stop)
        seed(a=None)
        return _out

    async def _timed_removal(self, key, value):
        await sleep(value.get("time_remaining"))
        del self[key]

    async def add(self, ctx: commands.Context, error: commands.CommandOnCooldown):

        _id = self.data_lut.get(error.cooldown.type)(ctx)
        key = _id + self.string_to_int(ctx.command.name)
        value = {'id': _id, 'context': ctx, 'error': error, 'time_remaining': error.retry_after}
        self.data[key] = value
        create_task(self._timed_removal(key, value))

    def in_data(self, ctx: commands.Context, error: commands.CommandOnCooldown):
        _id = self.data_lut.get(error.cooldown.type)(ctx)
        command_name = ctx.command.name
        key = _id + self.string_to_int(command_name)
        return key in self.data
