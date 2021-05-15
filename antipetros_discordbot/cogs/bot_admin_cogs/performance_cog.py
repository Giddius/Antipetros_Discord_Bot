

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import asyncio
from io import BytesIO
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from statistics import mean, stdev, median, StatisticsError
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

from antipetros_discordbot.utility.misc import delete_message_if_text_channel
from antipetros_discordbot.utility.enums import DataSize, CogMetaStatus, UpdateTypus
from antipetros_discordbot.utility.checks import owner_or_admin
from antipetros_discordbot.utility.embed_helpers import make_basic_embed, make_basic_embed_inline
from antipetros_discordbot.utility.gidtools_functions import bytes2human, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.regexes import LOG_SCRAPE_REGEX, PROFILING_REGEX
from antipetros_discordbot.utility.sqldata_storager import general_db

from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFolder, auto_meta_info_command
from antipetros_discordbot.utility.general_decorator import universal_log_profiler

if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot

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

# endregion[Constants]


class PerformanceCog(AntiPetrosBaseCog, command_attrs={'hidden': True, 'categories': CommandCategory.META}):
    """
    Collects Latency data and memory usage every 10min and posts every 24h a report of the last 24h as graphs.
    """
# region [ClassAttributes]

    public = True
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    required_config_data = {'base_config': {},
                            'cogs_config': {"threshold_latency_warning": "250",
                                            "threshold_memory_warning": "0.5",
                                            "threshold_memory_critical": "0.75",
                                            "latency_graph_formatting": "r1-",
                                            "memory_graph_formatting": "b1-"}}

    save_folder = APPDATA['performance_data']
    required_folder = [RequiredFolder(save_folder)]
    required_files = []

# endregion[ClassAttributes]

# region [Init]

    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.start_time = datetime.utcnow()
        self.latency_thresholds = {'warning': COGS_CONFIG.getint(self.config_name, "threshold_latency_warning")}
        self.memory_thresholds = {'warning': virtual_memory().total * COGS_CONFIG.getfloat(self.config_name, "threshold_memory_warning"),
                                  'critical': virtual_memory().total * COGS_CONFIG.getfloat(self.config_name, "threshold_memory_critical")}
        self.plot_formatting_info = {'latency': COGS_CONFIG.get(self.config_name, 'latency_graph_formatting'),
                                     'memory': COGS_CONFIG.get(self.config_name, 'memory_graph_formatting'),
                                     'cpu': COGS_CONFIG.get(self.config_name, 'cpu_graph_formatting')}

        self.ready = False
        self.general_db = general_db
        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)

# endregion[Init]

# region [Setup]

    @universal_log_profiler
    async def on_ready_setup(self):
        _ = psutil.cpu_percent(interval=None)
        self.latency_measure_loop.start()
        await asyncio.sleep(2)
        self.memory_measure_loop.start()
        await asyncio.sleep(2)
        self.cpu_measure_loop.start()
        await asyncio.sleep(2)
        self.profile_info_from_logs.start()
        await asyncio.sleep(2)
        await self.format_graph(10)
        plt.style.use('dark_background')
        self.ready = True

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion[Setup]

# region [Loops]

    @tasks.loop(minutes=2, reconnect=True)
    async def profile_info_from_logs(self):
        if self.ready is False:
            return
        if os.getenv("ANTIPETROS_PROFILING") == "1":
            asyncio.create_task(self.general_db.insert_profile_data(await self.parse_logs_for_profile()))
            log.info("Inserted Profile Data into Database")

    @tasks.loop(seconds=DATA_COLLECT_INTERVALL, reconnect=True)
    @universal_log_profiler
    async def cpu_measure_loop(self):
        if self.ready is False:
            return
        log.info("measuring cpu")
        now = datetime.now(tz=timezone.utc)

        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_load_avg_1, cpu_load_avg_5, cpu_load_avg_15 = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
        await self.general_db.insert_cpu_performance(now, cpu_percent, cpu_load_avg_1, cpu_load_avg_5, cpu_load_avg_15)

    @tasks.loop(seconds=DATA_COLLECT_INTERVALL, reconnect=True)
    @universal_log_profiler
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
        await self.general_db.insert_latency_perfomance(now, raw_latency)

    @latency_measure_loop.error
    async def latency_measure_loop_error_handler(self, error):
        log.error(error, exc_info=True)
        if self.latency_measure_loop.is_running() is False:
            self.latency_measure_loop.start()
            log.warning("latency measure loop was restarted")

    @tasks.loop(seconds=DATA_COLLECT_INTERVALL, reconnect=True)
    @universal_log_profiler
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
        await self.general_db.insert_memory_perfomance(now, memory_in_use)

# endregion[Loops]

# region [Commands]

    @auto_meta_info_command()
    @owner_or_admin()
    async def report_latency(self, ctx, with_graph: bool = True):
        """
        Reports the latency in the last 24h

        Args:
            with_graph (bool, optional): if it should be presented in graph form. Defaults to True.

        Example:
            @AntiPetros report_latency yes
        """
        report_data = await self.general_db.get_latency_data_last_24_hours()

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

    @auto_meta_info_command()
    @owner_or_admin()
    async def report_memory(self, ctx, with_graph: bool = True, since_last_hours: int = 24):
        """
        Reports the memory use in the last 24h

        Args:
            with_graph (bool, optional): if it should be presented in graph form. Defaults to True.

        Example:
            @AntiPetros report_memory yes
        """
        initial_memory = os.getenv('INITIAL_MEMORY_USAGE')
        initial_memory_annotated = bytes2human(int(initial_memory), annotate=True)
        report_data = await self.general_db.get_memory_data_last_24_hours()

        stat_data = [item.memory_in_use for item in report_data]
        embed_data = {'Initial': initial_memory_annotated, 'Mean': bytes2human(round(mean(stat_data), 2), True), 'Median': bytes2human(round(median(stat_data), 2), True), "Std-dev": bytes2human(round(stdev(stat_data)), True)}

        _file = None
        if len(report_data) < 11:
            embed_data = embed_data | {item.date_time.strftime(self.bot.std_date_time_format): '\n\n'.join([f'in use absolute: \n{item.pretty_memory_in_use}',
                                                                                                            f'percentage used: \n{round(item.as_percent, 1)}%']) for item in report_data}

        embed = await make_basic_embed_inline(title='Memory Data',
                                              text=f"Data of the last {str(since_last_hours)} hours",
                                              symbol='graph', amount_datapoints=str(len(report_data)),
                                              **embed_data)
        if with_graph is True:
            log.debug('calling make_graph')
            _file, _url = await self.make_graph(report_data, 'memory')
            embed.set_image(url=_url)
        await ctx.send(embed=embed, file=_file)

    @auto_meta_info_command()
    @owner_or_admin()
    async def report_cpu(self, ctx, with_graph: bool = True):
        """
        Reports the cpu use in the last 24h

        Args:
            with_graph (bool, optional): if it should be presented in graph form. Defaults to True.

        Example:
            @AntiPetros report_cpu yes
        """
        report_data = await self.general_db.get_cpu_data_last_24_hours()

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

    @auto_meta_info_command()
    @owner_or_admin()
    async def report(self, ctx):
        """
        Reports all collected metrics as Graph.

        Example:
            @AntiPetros report
        """
        try:
            await ctx.invoke(self.bot.get_command('report_memory'))
            await ctx.invoke(self.bot.get_command('report_latency'))
            await ctx.invoke(self.bot.get_command('report_cpu'))
        except StatisticsError as error:
            # TODO: make as error embed
            await ctx.send('not enough data points collected to report!', delete_after=120)
            await delete_message_if_text_channel(ctx)


# endregion[Commands]

# region [Helper]


    async def parse_logs_for_profile(self):
        log_folder = APPDATA.log_folder
        old_logs_folder = pathmaker(log_folder, 'old_logs')
        logs = [pathmaker(file.path) for file in os.scandir(log_folder) if file.is_file() and file.name.endswith('.log')] + [pathmaker(file.path) for file in os.scandir(old_logs_folder) if file.is_file() and file.name.endswith('.log')]
        data = []
        for file in logs:
            data += await self.parse_profile_info_from_log_file(file)
        return data

    async def parse_profile_info_from_log_file(self, log_file):
        DATE_TIME_GROUP_NAMES = ["year", "month", "day", "hour", "minute", "second"]
        _out = []
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip('\n')
                log_match = LOG_SCRAPE_REGEX.search(line)
                if log_match and log_match.group('level') == 'PROFILE':
                    profiling_match = PROFILING_REGEX.search(log_match.group('message'))
                    if profiling_match:
                        date_time = datetime(**{key: int(value) for key, value in log_match.groupdict().items() if key in DATE_TIME_GROUP_NAMES}, microsecond=int(log_match.group('microsecond') + '000'), tzinfo=timezone.utc)
                        module = profiling_match.group('module').strip()
                        function = profiling_match.group('function').strip()
                        time_taken = int(profiling_match.group('time_taken'))
                        _out.append((date_time, module, function, time_taken))
                await asyncio.sleep(0)

        return _out

    @universal_log_profiler
    async def format_graph(self, amount_data: int):
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        if amount_data <= 3600 // DATA_COLLECT_INTERVALL:
            main_interval = DATA_COLLECT_INTERVALL / (60 / amount_data)
            min_interval = main_interval / 10
            plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=round(main_interval)))
            plt.gca().xaxis.set_minor_locator(mdates.MinuteLocator(interval=2))
        else:
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.rcParams["font.family"] = "Consolas"
        plt.rcParams['savefig.facecolor'] = "#2f3136"
        plt.rcParams['figure.facecolor'] = "#2f3136"
        plt.rcParams['axes.facecolor'] = "#2f3136"
        plt.rcParams['patch.facecolor'] = "#2f3136"

        plt.rc('xtick.major', size=6, pad=10)
        plt.rc("xtick.minor", width=0.25, size=3)
        plt.rc('xtick', labelsize=10)

    @ universal_log_profiler
    async def make_graph(self, data, typus: str, save_to=None):
        plt.style.use('dark_background')

        await self.format_graph(len(data))

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
            plt.savefig(image_binary, format='png', dpi=COGS_CONFIG.retrieve(self.config_name, 'report_image_dpi', typus=int, direct_fallback=150))
            plt.close()
            image_binary.seek(0)

            return discord.File(image_binary, filename=f'{typus}graph.png'), f"attachment://{typus}graph.png"

    @ universal_log_profiler
    async def convert_memory_size(self, in_bytes, new_unit: DataSize, annotate: bool = False, extra_digits=2):

        if annotate is False:
            return round(int(in_bytes) / new_unit.value, ndigits=extra_digits)
        return str(round(int(in_bytes) / new_unit.value, ndigits=extra_digits)) + ' ' + new_unit.short_name

    @ universal_log_profiler
    async def get_time_from_max_y(self, data, max_y, typus):
        for item in data:
            if typus == 'memory':
                if await self.convert_memory_size(item.memory_in_use, DataSize.GigaBytes) == max_y:
                    _out = item.date_time
            else:
                if item.latency == max_y:
                    _out = item.date_time
        return _out

# endregion[Helper]


# region [SpecialMethods]


    def __str__(self) -> str:
        return self.qualified_name

    def cog_unload(self):
        self.cpu_measure_loop.stop()
        self.latency_measure_loop.stop()
        self.memory_measure_loop.stop()
        self.report_data_loop.stop()
        self.profile_info_from_logs.stop()
        log.debug("Cog '%s' UNLOADED!", str(self))

# endregion[SpecialMethods]


def setup(bot):

    bot.add_cog(PerformanceCog(bot))


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
