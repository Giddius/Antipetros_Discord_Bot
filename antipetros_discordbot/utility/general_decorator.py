"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import time
from time import process_time_ns, time
from functools import wraps

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from inspect import iscoroutinefunction
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]

NANO_SECONDS_FACTOR = 1_000_000_000


def debug_timing_print(func):
    @wraps(func)
    def _function_print_time(*args, **kwargs):
        start_time = time()
        _out = func(*args, **kwargs)

        if len(args) != 0 and hasattr(args[0], func.__name__):
            report = f"'{func.__name__}' of the '{args[0].__class__.__name__}' class took {str(round(time()-start_time, ndigits=4))} seconds"
        else:
            report = f"'{func.__name__}' took {str(round(time()-start_time, ndigits=4))} seconds"

        print(report)
        return _out
    if os.getenv('IS_DEV') == 'true':
        return _function_print_time
    else:
        return func


def debug_timing_log(logger):
    def _decorator(func):
        @wraps(func)
        def _function_print_time(*args, **kwargs):
            start_time = time()
            _out = func(*args, **kwargs)
            if len(args) != 0 and hasattr(args[0], func.__name__):
                report = f"'{func.__name__}' of '{str(args[0])}' took {str(round(time()-start_time, ndigits=4))} seconds"
            else:
                report = f"'{func.__name__}' took {str(round(time()-start_time, ndigits=4))} seconds"

            logger.debug(report, extra={'func_name_override': func.__name__})
            return _out
        if os.getenv('IS_DEV') == 'true':
            return _function_print_time
        else:
            return func
    return _decorator


def async_log_profiler(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        if os.getenv('ANTIPETROS_PROFILING') == '1':
            logger = glog.aux_logger(__name__)
            start_time = process_time_ns()
            _out = await f(*args, **kwargs)
            time_taken = process_time_ns() - start_time
            logger.profile("<PROFILING> module: %s, function: %s, time_taken: %s ns </PROFILING>", f.__module__, f.__name__, str(time_taken))
        else:
            _out = await f(*args, **kwargs)
        return _out
    return wrapper


def sync_log_profiler(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if os.getenv('ANTIPETROS_PROFILING') == '1':
            logger = glog.aux_logger(__name__)
            start_time = process_time_ns()
            _out = f(*args, **kwargs)
            time_taken = process_time_ns() - start_time
            logger.profile("<PROFILING> module: %s, function: %s, time_taken: %s ns</PROFILING>", f.__module__, f.__name__, str(time_taken))
        else:
            _out = f(*args, **kwargs)
        return _out
    return wrapper


def universal_log_profiler(f):
    pretty = True if os.getenv('ANTIPETROS_PROFILING_PRETTY', '0') == "1" else False

    @wraps(f)
    async def async_wrapper(*args, **kwargs):
        if os.getenv('ANTIPETROS_PROFILING', '0') == '1':
            logger = glog.aux_logger(__name__)
            start_time = process_time_ns()
            _out = await f(*args, **kwargs)
            time_taken = process_time_ns() - start_time
            if time_taken > 0:
                time_string = str(round(time_taken / NANO_SECONDS_FACTOR, 2)) + ' s' if pretty is True else str(time_taken) + ' ns'
                logger.critical("<PROFILING> module: %s, function: %s, time_taken: %s</PROFILING>", f.__module__, f.__name__, time_string)
        else:
            _out = await f(*args, **kwargs)
        return _out

    @wraps(f)
    def wrapper(*args, **kwargs):
        if os.getenv('ANTIPETROS_PROFILING', '0') == '1':
            logger = glog.aux_logger(__name__)
            start_time = process_time_ns()
            _out = f(*args, **kwargs)
            time_taken = process_time_ns() - start_time
            if time_taken > 0:
                time_string = str(round(time_taken / NANO_SECONDS_FACTOR, 2)) + ' s' if pretty is True else str(time_taken) + ' ns'
                logger.critical("<PROFILING> module: %s, function: %s, time_taken: %s</PROFILING>", f.__module__, f.__name__, time_string)
        else:
            _out = f(*args, **kwargs)
        return _out
    if iscoroutinefunction(f):
        return async_wrapper
    return wrapper


def is_refresh_task(f):

    f.is_refresh_task = True

    return f


def handler_method(f):

    f.is_handler = True
    f.handled_attr = f.__name__.removeprefix('_handle_')
    f.applicable_to = 'all'

    return f


def handler_method_only_commands(f):
    f.is_handler = True
    f.handled_attr = f.__name__.removeprefix('_handle_')
    f.applicable_to = 'commands'

    return f


def handler_method_only_categories(f):
    f.is_handler = True
    f.handled_attr = f.__name__.removeprefix('_handle_')
    f.applicable_to = 'categories'

    return f

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
