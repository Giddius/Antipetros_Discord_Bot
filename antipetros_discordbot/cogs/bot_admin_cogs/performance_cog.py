

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import time
import asyncio
from io import BytesIO
from datetime import datetime, timedelta, timezone
from statistics import mean, stdev, median
from collections import deque
from textwrap import dedent
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from psutil import virtual_memory
import psutil
from discord.ext import tasks, commands
from matplotlib.ticker import FormatStrFormatter

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->

from antipetros_discordbot.utility.misc import async_seconds_to_pretty_normal, date_today, make_config_name
from antipetros_discordbot.utility.enums import DataSize, CogState, UpdateTypus
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, log_invoker, owner_or_admin
from antipetros_discordbot.utility.named_tuples import LatencyMeasurement, MemoryUsageMeasurement
from antipetros_discordbot.utility.embed_helpers import make_basic_embed, make_basic_embed_inline
from antipetros_discordbot.utility.gidtools_functions import pathmaker, writejson, bytes2human, create_folder
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCommand, AntiPetrosFlagCommand
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.sqldata_storager import AioMetaDataStorageSQLite
# endregion[Imports]

# region [TODO]


# TODO: get_logs command
# TODO: get_appdata_location command


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

DATA_COLLECT_INTERVALL = 60 if os.getenv('IS_DEV').casefold() in ['yes', 'true', '1'] else 600  # seconds
COG_NAME = "PerformanceCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)
# endregion[Constants]


class PerformanceCog(commands.Cog, command_attrs={'hidden': True, "name": "PerformanceCog"}):
    """
    Collects Latency data and memory usage every 10min and posts every 24h a report of the last 24h as graphs.
    """

    config_name = CONFIG_NAME
    save_folder = APPDATA['performance_data']
    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.OPEN_TODOS | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 05:25:38",
                             "f0e545c1c0066f269dc77a19380ab01ac1fc3e03b6df4662850ca4a779b4343d64c244941fdef8af3aca0342893463d9de35f8f24f71852649028411a33bebf3")}
    required_config_data = dedent("""
                                threshold_latency_warning = 250
                                threshold_memory_warning = 0.5
                                threshold_memory_critical = 0.75
                                latency_graph_formatting = r1-
                                memory_graph_formatting = b1-

                                """)

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.start_time = datetime.utcnow()
        self.latency_thresholds = {'warning': COGS_CONFIG.getint(self.config_name, "threshold_latency_warning")}
        self.memory_thresholds = {'warning': virtual_memory().total * COGS_CONFIG.getfloat(self.config_name, "threshold_memory_warning"),
                                  'critical': virtual_memory().total * COGS_CONFIG.getfloat(self.config_name, "threshold_memory_critical")}
        self.plot_formatting_info = {'latency': COGS_CONFIG.get(self.config_name, 'latency_graph_formatting'),
                                     'memory': COGS_CONFIG.get(self.config_name, 'memory_graph_formatting'),
                                     'cpu': COGS_CONFIG.get(self.config_name, 'cpu_graph_formatting')}
        create_folder(self.save_folder)
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        self.ready = False
        self.meta_db = AioMetaDataStorageSQLite()
        glog.class_init_notification(log, self)

    async def on_ready_setup(self):
        _ = psutil.cpu_percent(interval=None)
        self.latency_measure_loop.start()
        self.memory_measure_loop.start()
        self.cpu_measure_loop.start()
        await asyncio.sleep(5)
        self.ready = True

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

    @tasks.loop(seconds=DATA_COLLECT_INTERVALL, reconnect=True)
    async def cpu_measure_loop(self):
        if self.ready is False:
            return
        log.info("measuring cpu")
        now = datetime.now(tz=timezone.utc)

        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_load_avg_1, cpu_load_avg_5, cpu_load_avg_15 = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
        await self.meta_db.insert_cpu_performance(now, cpu_percent, cpu_load_avg_1, cpu_load_avg_5, cpu_load_avg_15)

    @tasks.loop(seconds=DATA_COLLECT_INTERVALL, reconnect=True)
    async def latency_measure_loop(self):
        if self.ready is False:
            return

        log.info("measuring latency")
        now = datetime.now(tz=timezone.utc)
        raw_latency = self.bot.latency * 1000
        latency = round(raw_latency)
        if latency > self.latency_thresholds.get('warning'):
            log.warning("high latency: %s ms", str(latency))
            await self.bot.message_creator(embed=await make_basic_embed(title='LATENCY WARNING!', text='Latency is very high!', symbol='warning', **{'Time': now.strftime(self.bot.std_date_time_format), 'latency': str(latency) + ' ms'}))
        await self.meta_db.insert_latency_perfomance(now, raw_latency)

    @tasks.loop(seconds=DATA_COLLECT_INTERVALL, reconnect=True)
    async def memory_measure_loop(self):
        if self.ready is False:
            return
        log.info("measuring memory usage")
        now = datetime.now(tz=timezone.utc)
        _mem_item = virtual_memory()
        memory_in_use = _mem_item.total - _mem_item.available
        if memory_in_use > self.memory_thresholds.get("critical"):
            log.critical("Memory usage is critical! Memory in use: %s", DataSize.GigaBytes.convert(memory_in_use, annotate=True))
            await self.bot.message_creator(embed=await make_basic_embed(title='MEMORY CRITICAL!', text='Memory consumption is dangerously high!', symbol='warning', **{'Time': now.strftime(self.bot.std_date_time_format), 'Memory usage absolute': await self.convert_memory_size(memory_in_use, DataSize.GigaBytes, True, 3), 'as percent': str(_mem_item.percent) + '%'}))
        elif memory_in_use > self.memory_thresholds.get("warning"):
            log.warning("Memory usage is high! Memory in use: %s", DataSize.GigaBytes.convert(memory_in_use, annotate=True))
        await self.meta_db.insert_memory_perfomance(now, memory_in_use)

    @auto_meta_info_command(enabled=True)
    @owner_or_admin()
    async def initial_memory_use(self, ctx):
        initial_memory = os.getenv('INITIAL_MEMORY_USAGE')
        await ctx.send(bytes2human(int(initial_memory), annotate=True))

    @auto_meta_info_command(enabled=True)
    @owner_or_admin()
    async def report_latency(self, ctx, with_graph: bool = True):
        report_data = await self.meta_db.get_latency_data_last_24_hours()

        stat_data = [item.latency for item in report_data]
        embed_data = {'Mean': round(mean(stat_data), 2), 'Median': round(median(stat_data), 2), "Std-dev": round(stdev(stat_data))}
        _file = None
        if len(report_data) < 11:
            embed_data = embed_data | {item.date_time.strftime(self.bot.std_date_time_format): item.pretty_latency for item in report_data}
        embed = await make_basic_embed_inline(title='Latency Data', text="Data of the last 24 hours", symbol='graph', amount_datapoints=str(len(report_data)), ** embed_data)

        if with_graph is True:
            _file, _url = await self.make_graph(report_data, 'latency')
            embed.set_image(url=_url)
        await ctx.send(embed=embed, file=_file)

    @auto_meta_info_command(enabled=True)
    @owner_or_admin()
    async def report_memory(self, ctx, with_graph: bool = True, since_last_hours: int = 24):
        report_data = await self.meta_db.get_memory_data_last_24_hours()

        stat_data = [item.memory_in_use for item in report_data]
        embed_data = {'Mean': bytes2human(round(mean(stat_data), 2), True), 'Median': bytes2human(round(median(stat_data), 2), True), "Std-dev": bytes2human(round(stdev(stat_data)), True)}

        _file = None
        if len(report_data) < 11:
            embed_data = embed_data | {item.date_time.strftime(self.bot.std_date_time_format): '\n\n'.join([f'in use absolute: \n{item.pretty_memory_in_use}',
                                                                                                            f'percentage used: \n{item.as_percent}%']) for item in report_data}

        embed = await make_basic_embed_inline(title='Memory Data',
                                              text=f"Data of the last {str(since_last_hours)} hours",
                                              symbol='graph', amount_datapoints=str(len(report_data)),
                                              **embed_data)
        if with_graph is True:
            log.debug('calling make_graph')
            _file, _url = await self.make_graph(report_data, 'memory')
            embed.set_image(url=_url)
        await ctx.send(embed=embed, file=_file)

    @auto_meta_info_command(enabled=True)
    @owner_or_admin()
    async def report_cpu(self, ctx, with_graph: bool = True):
        report_data = await self.meta_db.get_cpu_data_last_24_hours()

        stat_data = [item.usage_percent for item in report_data]
        embed_data = {'Mean': round(mean(stat_data), 2), 'Median': round(median(stat_data), 2), "Std-dev": round(stdev(stat_data))}
        _file = None
        if len(report_data) < 11:
            embed_data = embed_data | {item.date_time.strftime(self.bot.std_date_time_format): item.pretty_usage_percent for item in report_data}
        embed = await make_basic_embed_inline(title='CPU Data', text="Data of the last 24 hours", symbol='graph', amount_datapoints=str(len(report_data)), ** embed_data)

        if with_graph is True:
            _file, _url = await self.make_graph(report_data, 'cpu')
            embed.set_image(url=_url)
        await ctx.send(embed=embed, file=_file)

    async def format_graph(self):
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=max(24 // 60, 10)))
        plt.rcParams["font.family"] = "Consolas"
        plt.rc('xtick.major', size=6, pad=10)
        plt.rc('xtick', labelsize=9)

    async def make_graph(self, data, typus: str, save_to=None):
        plt.style.use('dark_background')

        await asyncio.wait_for(self.format_graph(), timeout=10)
        x = [item.date_time for item in data]

        if typus == 'latency':
            y = [item.latency for item in data]
            max_y = max(y)
            min_y = min(item.latency for item in data)
            ymin = min_y - (min_y // 6)

            ymax = max_y + (max_y // 6)
            h_line_height = max_y
            plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%d ms'))
        elif typus == 'memory':
            y = [bytes2human(item.memory_in_use) for item in data]
            raw_max_y = bytes2human(max(item.memory_in_use for item in data))
            max_y = bytes2human(max(item.total_memory for item in data))
            ymin = 0
            ymax = round(max_y * 1.1)
            h_line_height = max_y
            unit_legend = bytes2human(max(item.memory_in_use for item in data), True).split(' ')[-1]
            plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%d ' + unit_legend))
        elif typus == 'cpu':
            y = [item.usage_percent for item in data]
            ymax = 100
            ymin = 0
            h_line_height = max(y)
            plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%d%%'))
        await asyncio.sleep(0.25)

        plt.plot(x, y, self.plot_formatting_info.get(typus), markersize=2, linewidth=0.6, alpha=1)

        plt.gcf().autofmt_xdate()

        await asyncio.sleep(0.25)

        if typus == 'cpu':
            vline_max = [item.date_time for item in data if item.usage_percent == max(item.usage_percent for item in data)][0]
        elif typus == 'memory':
            vline_max = [item.date_time for item in data if item.memory_in_use == max(item.memory_in_use for item in data)][0]
        elif typus == 'latency':
            vline_max = [item.date_time for item in data if item.latency == max(item.latency for item in data)][0]

        plt.axvline(x=vline_max, color='g', linestyle=':')
        plt.axhline(y=h_line_height, color='r', linestyle='--')

        plt.axis(ymin=ymin, ymax=ymax)

        plt.title(f'{typus.title()} -- {datetime.utcnow().strftime("%Y.%m.%d")}')

        plt.xticks(rotation=90)
        await asyncio.sleep(0.25)
        if save_to is not None:
            plt.savefig(save_to, format='png')

        with BytesIO() as image_binary:
            plt.savefig(image_binary, format='png')
            plt.close()
            image_binary.seek(0)

            return discord.File(image_binary, filename=f'{typus}graph.png'), f"attachment://{typus}graph.png"

    async def convert_memory_size(self, in_bytes, new_unit: DataSize, annotate: bool = False, extra_digits=2):

        if annotate is False:
            return round(int(in_bytes) / new_unit.value, ndigits=extra_digits)
        return str(round(int(in_bytes) / new_unit.value, ndigits=extra_digits)) + ' ' + new_unit.short_name

    async def get_time_from_max_y(self, data, max_y, typus):
        for item in data:
            if typus == 'memory':
                if await self.convert_memory_size(item.memory_in_use, DataSize.GigaBytes) == max_y:
                    _out = item.date_time
            else:
                if item.latency == max_y:
                    _out = item.date_time
        return _out

    @auto_meta_info_command(enabled=True)
    @owner_or_admin()
    async def get_command_stats(self, ctx):
        data_dict = {item.name: f"{ZERO_WIDTH}\n{item.data}\n{ZERO_WIDTH}" for item in await self.bot.support.get_todays_invoke_data()}
        date = date_today()

        embed = await make_basic_embed(title=ctx.command.name, text=f'data of the last 24hrs - {date}', symbol='data', **data_dict)

        await ctx.send(embed=embed)

    @auto_meta_info_command(enabled=True)
    @owner_or_admin()
    async def report(self, ctx):
        """
        Reports both current latency and memory usage as Graph.

        Example:
            @AntiPetros report
        """
        await ctx.invoke(self.bot.get_command('report_memory'))
        await ctx.invoke(self.bot.get_command('report_latency'))
        await ctx.invoke(self.bot.get_command('report_cpu'))

    @auto_meta_info_command()
    @owner_or_admin()
    async def cpu_info(self, ctx: commands.Context):
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_logical_count = psutil.cpu_count()
        cpu_strict_count = psutil.cpu_count(logical=False)
        cpu_load_avg = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
        fields = [self.bot.field_item(name="CPU Percent", value=f"{cpu_percent} %"),
                  self.bot.field_item(name="CPU count logical", value=cpu_logical_count),
                  self.bot.field_item(name="CPU strict count", value=cpu_strict_count),
                  self.bot.field_item(name="CPU load average", value=f"1 minute: {cpu_load_avg[0]}\n5 minutes: {cpu_load_avg[1]}\n15 minutes: {cpu_load_avg[2]}")]
        embed_data = await self.bot.make_generic_embed(title="CPU Data", fields=fields)
        await ctx.send(**embed_data)

    @auto_meta_info_command()
    @owner_or_admin()
    async def socket_info(self, ctx: commands.Context):
        out = []
        net_connections = psutil.net_connections()
        for item in net_connections:
            out.append(str(item))
        writejson(out, 'net_stuff.json')
        await ctx.send('done')

    def __str__(self) -> str:
        return self.qualified_name

    def cog_unload(self):
        self.cpu_measure_loop.stop()
        self.latency_measure_loop.stop()
        self.memory_measure_loop.stop()
        self.report_data_loop.stop()
        log.debug("Cog '%s' UNLOADED!", str(self))


def setup(bot):

    bot.add_cog(attribute_checker(PerformanceCog(bot)))


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
