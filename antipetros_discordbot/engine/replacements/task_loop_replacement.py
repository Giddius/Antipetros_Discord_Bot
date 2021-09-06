from discord.ext import tasks
import gidlogger as glog

log = glog.aux_logger(__name__)


class AntiPetrosBaseLoop(tasks.Loop):

    async def _error(self, *args):
        exception = args[-1]
        text = 'Unhandled exception in internal background task {0.__name__!r}.'.format(self.coro)
        log.error(text, exc_info=exception)
        log.critical("restarting loop %s after Error %s", self.coro.__name__, exception)
        if self.is_running() is False:
            self.start()


def custom_loop(**kwargs):
    """A decorator that schedules a task in the background for you with
    optional reconnect logic. The decorator returns a :class:`Loop`.

    Parameters
    ------------
    seconds: :class:`float`
        The number of seconds between every iteration.
    minutes: :class:`float`
        The number of minutes between every iteration.
    hours: :class:`float`
        The number of hours between every iteration.
    count: Optional[:class:`int`]
        The number of loops to do, ``None`` if it should be an
        infinite loop.
    reconnect: :class:`bool`
        Whether to handle errors and restart the task
        using an exponential back-off algorithm similar to the
        one used in :meth:`discord.Client.connect`.
    loop: :class:`asyncio.AbstractEventLoop`
        The loop to use to register the task, if not given
        defaults to :func:`asyncio.get_event_loop`.

    Raises
    --------
    ValueError
        An invalid value was given.
    TypeError
        The function was not a coroutine.
    """
    # if klass is None:
    #     klass = AntiPetrosBaseLoop

    # def decorator(func):
    #     kwargs = {
    #         'seconds': seconds,
    #         'minutes': minutes,
    #         'hours': hours,
    #         'count': count,
    #         'reconnect': reconnect,
    #         'loop': loop
    #     }
    #     return klass(func, **kwargs)
    # return decorator
    return tasks.loop(**kwargs)
