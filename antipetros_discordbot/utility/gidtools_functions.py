# region [Imports]

# * Standard Library Imports -->
import os
import json
import pickle
import shutil
import hashlib
import datetime
import configparser
from pprint import pformat
from contextlib import contextmanager
import sys

# * Gid Imports -->
import gidlogger as glog

# endregion [Imports]


# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion [Logging]


# region [Constants]


# endregion [Constants]


def loadjson(in_file):
    with open(in_file, 'r') as jsonfile:
        _out = json.load(jsonfile)
    return _out


def writejson(in_object, in_file, sort_keys=True, indent=4):
    with open(in_file, 'w') as jsonoutfile:
        json.dump(in_object, jsonoutfile, sort_keys=sort_keys, indent=indent)


def hash_to_solidcfg(in_file, in_name=None, in_config_loc='default'):
    _cfg = configparser.ConfigParser()
    _cfg_loc = pathmaker('cwd', 'config', 'solid_config.ini') if in_config_loc == 'default' else in_config_loc
    _bin_file = readbin(in_file)
    _name = splitoff(in_file)[1].replace('.', '') if in_name is None else in_name
    _cfg.read(_cfg_loc)
    _hash = hashlib.md5(_bin_file).hexdigest()
    if _cfg.has_section('hashes') is False:
        log.info("section ['hashes'] does not exist in solid_config.ini, creating it now!")
        _cfg.add_section('hashes')
        log.info("section ['hashes'] added to solid_config.ini")
    _cfg.set('hashes', _name, _hash)
    log.info(f"added hash [{_hash}] to section ['hashes'] in solid_config.ini")
    with open(_cfg_loc, 'w') as configfile:
        _cfg.write(configfile)
        log.debug("saved new solid_config.ini at '{_cfg_loc}'")
    _cfg.read(_cfg_loc)
    if _cfg.get('hashes', _name) != _hash:
        raise configparser.Error("recently saved hash does not match the file hash")


def ishash_same(in_file, in_name=None, in_config_loc='default'):
    _cfg = configparser.ConfigParser()
    _cfg_loc = pathmaker('cwd', 'config', 'solid_config.ini') if in_config_loc == 'default' else in_config_loc
    _bin_file = readbin(in_file)
    _name = splitoff(in_file)[1].replace('.', '') if in_name is None else in_name
    _cfg.read(_cfg_loc)
    _hash = hashlib.md5(_bin_file).hexdigest()
    if _cfg.has_section('hashes') is True:
        if _cfg.has_option('hashes', _name):
            if _cfg.get('hashes', _name) != _hash:
                _out = False
                log.info("hashes are !NOT! the same")
            elif _cfg.get('hashes', _name) == _hash:
                _out = True
                log.info("hashes are the same")
        else:
            _out = False
            log.info('missing option')
    else:
        log.critical("section ['hashes'] is missing in solid_config.ini, it is absolutely needed")
        raise configparser.Error("section ['hashes'] does not exist!!")

    return _out


def absolute_listdir(in_dir, in_filter=None, in_filter_type=True):
    for files in os.listdir(in_dir):
        if in_filter is not None:
            if in_filter_type is True:
                if in_filter in files:
                    yield pathmaker(in_dir, files)
            elif in_filter_type is False:
                if in_filter not in files:
                    yield pathmaker(in_dir, files)
        else:
            yield pathmaker(in_dir, files)


def readbin(in_file):
    """
    Reads a binary file.

    Parameters
    ----------
    in_file : str
        A file path

    Returns
    -------
    str
        the decoded file as string
    """
    with open(pathmaker(in_file), 'rb') as binaryfile:
        return binaryfile.read()


def readit(in_file, per_lines=False, in_encoding='utf-8', in_errors=None):
    """
    Reads a file.

    Parameters
    ----------
    in_file : str
        A file path
    per_lines : bool, optional
        If True, returns a list of all lines, by default False
    in_encoding : str, optional
        Sets the encoding, by default 'utf-8'
    in_errors : str, optional
        How to handle encoding errors, either 'strict' or 'ignore', by default 'strict'

    Returns
    -------
    str/list
        the read in file as string or list (if per_lines is True)
    """
    with open(in_file, 'r', encoding=in_encoding, errors=in_errors) as _rfile:
        _content = _rfile.read()
    if per_lines is True:
        _content = _content.splitlines()

    return _content


def linereadit(in_file, in_encoding='utf-8', in_errors='strict'):
    with open(in_file, 'r', encoding=in_encoding, errors=in_errors) as lineread_file:
        _out = lineread_file.read().splitlines()
    return _out


def from_dict_to_file(in_out_file, in_dict_name, in_dict):
    appendwriteit(in_out_file, '\n\n')
    _dict_string = in_dict_name + ' = {' + pformat(in_dict) + '\n}'
    _dict_string = _dict_string.replace('{{', '{\n').replace('}}', '}').replace('}\n}', '\n}')
    appendwriteit(in_out_file, _dict_string)


def writebin(in_file, in_data):
    """
    Writes a string to binary.

    Parameters
    ----------
    in_file : str
        The target file path
    in_data : str
        The data to write
    """
    with open(in_file, 'wb') as outbinfile:
        outbinfile.write(in_data)


def writeit(in_file, in_data, append=False, in_encoding='utf-8', in_errors=None):
    """
    Writes to a file.

    Parameters
    ----------
    in_file : str
        The target file path
    in_data : str
        The data to write
    append : bool, optional
        If True appends the data to the file, by default False
    in_encoding : str, optional
        Sets the encoding, by default 'utf-8'
    """
    _write_type = 'w' if append is False else 'a'
    with open(in_file, _write_type, encoding=in_encoding, errors=in_errors,) as _wfile:
        _wfile.write(in_data)


def appendwriteit(in_file, in_data, in_encoding='utf-8'):
    with open(in_file, 'a', encoding=in_encoding) as appendwrite_file:
        appendwrite_file.write(in_data)


def clearit(in_file):
    """
    Deletes the contents of a file.

    Parameters
    ----------
    in_file : str
        The target file path
    """
    with open(in_file, 'w') as file_to_clear:
        file_to_clear.write('')
    log.debug(f"contents of file '{in_file}' was cleared")


def pathmaker(first_segment, *in_path_segments, rev=False):
    """
    Normalizes input path or path fragments, replaces '\\\\' with '/' and combines fragments.

    Parameters
    ----------
    first_segment : str
        first path segment, if it is 'cwd' gets replaced by 'os.getcwd()'
    rev : bool, optional
        If 'True' reverts path back to Windows default, by default None

    Returns
    -------
    str
        New path from segments and normalized.
    """

    _path = first_segment

    _path = os.path.join(_path, *in_path_segments)
    if rev is True or sys.platform not in ['win32', 'linux']:
        return os.path.normpath(_path)
    return os.path.normpath(_path).replace(os.path.sep, '/')


@contextmanager
def work_in(in_dir):
    """
    A context manager which changes the working directory to the given path,
    and then changes it back to its previous value on exit.

    Parameters
    ----------
    in_dir : str
        A file directory path
    """
    prev_cwd = os.getcwd()
    os.chdir(in_dir)
    log.debug(f"starting to work in directory [{in_dir}]")
    yield
    log.debug(f"stopped to work in directory [{in_dir}] and returned to directory [{prev_cwd}]")
    os.chdir(prev_cwd)


def path_part_remove(in_file):
    """
    Removes last segment of path, to get parent path.

    Parameters
    ----------
    in_file : str
        A file path

    Returns
    -------
    str
        A new file path, parent path of input.
    """
    _file = pathmaker(in_file)
    _path = _file.split('/')
    _useless = _path.pop(-1)
    _first = _path.pop(0) + '/'
    _out = pathmaker(_first, *_path)
    log.debug(f"path segment [{_useless}] was removed from path [{_file}] to get [{_out}]")
    return _out


def dir_change(*args, in_adress_home=False, ):
    """
    changes directory to script location or provided path.

    Parameters
    ----------
    in_adress_home : bool, optional
        'in_home_adress' if True defaults everything to location of current file and *args are ignored, by default False
    """
    if in_adress_home is True:
        _path_to_home = os.path.abspath(os.path.dirname(__file__))
    else:
        _path_to_home = pathmaker(*args)
    os.chdir(_path_to_home)
    log.debug('We are now in ' + _path_to_home)


def get_absolute_path(in_path='here', include_file=False):
    """
    Generates absolute path from relative path, optional gives it out as folder, by removing the file segment.

    Parameters
    ----------
    in_path : str, optional
        A relative filepath, if 'here' gets replaced by current file, by default 'here'
    include_file : bool, optional
        if False doesn't include last segment of path, by default False

    Returns
    -------
    str
        An absolute file path
    """
    _rel_path = __file__ if in_path == 'here' else in_path
    _out = os.path.abspath(_rel_path)
    if include_file is False:
        _out = splitoff(_out)[0]
    return _out


def file_name_time(var_sep='_', date_time_sep='-', box=('[', ']')):
    """
    creates a name that is the date and time.

    Parameters
    ----------
    var_sep : str, optional
        specifies the symbol used to seperate the file name and the datetime, by default '_'
    date_time_sep : str, optional
        specifies the symbol used to seperate the date and time, by default '-'
    box : tuple, optional
        symbols used to frame the datetime, by default ('[', ']')

    Returns
    -------
    str
        New file name
    """
    whole_time = str(datetime.datetime.today()).split(' ')
    today_date_temp = whole_time[0].split('-')
    today_date = var_sep.join(today_date_temp)
    today_time_temp = whole_time[1].split('.')[0].split(':')
    today_time = '' + today_time_temp[0] + var_sep + today_time_temp[1]
    if box is not None:
        _output = box[0] + today_date + date_time_sep + today_time + box[1]
    else:
        _output = today_date + date_time_sep + today_time
    log.debug(f"created file name [{_output}]")
    return _output


def number_rename(in_file_name, in_round=1):
    """
    Appends a number to a file name if it already exists, increases the number and checks again.

    Parameters
    ----------
    in_file_name : str
        [description]
    in_round : int, optional
        specifies the number to start on, by default 0

    Returns
    -------
    str
        new file name
    """
    _temp_path = in_file_name
    _temp_path = _temp_path.split('.')
    log.debug(f" Parts of rename: [0] = {_temp_path[0]}, [1] = {_temp_path[1]}")
    _output = _temp_path[0] + str(in_round) + '.' + _temp_path[1]
    log.debug(f"Setting name to {_output}")
    _new_round = int(in_round) + 1
    return _exist_handle(_output, _new_round, _temp_path[0] + '.' + _temp_path[1])


def cascade_rename(in_file_name, in_folder, in_max_files=3):
    _temp_file_dict = {}
    _name = ext_splitter(in_file_name)
    _ext = ext_splitter(in_file_name, _out='ext')
    file_index = 1
    for files in os.listdir(in_folder):
        files = files.casefold()
        if _name in files:
            if any(letter.isdigit() for letter in files):
                _temp_file_dict[str(file_index)] = pathmaker(in_folder, files)
                file_index = int(file_index) + 1
            else:
                _temp_file_dict[str(0)] = pathmaker(in_folder, files)
    if file_index + 1 <= in_max_files:
        if file_index == 1:
            writeit(pathmaker(in_folder, _name + str(file_index) + '.' + _ext), ' ')
            _temp_file_dict[str(file_index)] = pathmaker(in_folder, _name + str(file_index) + '.' + _ext)
        else:
            writeit(pathmaker(in_folder, _name + str(file_index + 1) + '.' + _ext), ' ')
            _temp_file_dict[str(file_index + 1)] = pathmaker(in_folder, _name + str(file_index + 1) + '.' + _ext)
    for i in range(len(_temp_file_dict) - 1):
        if i != 0:
            shutil.copy(_temp_file_dict[str(i)], _temp_file_dict[str(i - 1)])
        else:
            os.remove(_temp_file_dict[str(0)])
    return pathmaker(in_folder, _temp_file_dict[str(0)])


def _exist_handle(in_path, in_round, original_path):
    """
    internal use for the "number_rename" function.
    """
    if os.path.exists(in_path) is True:
        log.debug(f"{in_path} already exists")
        _new_path = number_rename(original_path, in_round)
        log.debug(f" variables for rename round {in_round} are: original_path = {original_path}, in_round = {in_round}")
    else:
        _new_path = in_path
        log.debug(
            f'{_new_path} does not exist, setting it to f"{in_path} does not exist, setting it to {_new_path}"'
        )

    return _new_path


def splitoff(in_file):
    """splitoff, wraps os.path.dirname and os.path.basename to return both as tuple.

    Args:
        in_file (str): the full file path

    Returns:
        tuple: where '[0]' is the dirname and '[1]' is the basename(filename)"""

    _file = pathmaker(in_file)
    return (os.path.dirname(_file), os.path.basename(_file))


def timenamemaker(in_full_path):
    """
    Creates a filename, that has the time included.

    Parameters
    ----------
    in_full_path : str
        full path of the file name that is to be modified

    Returns
    -------
    str
        the new file name
    """
    _time = datetime.datetime.utcnow().strftime('_[%Y-%m-%dT%H-%M]')
    log.debug(f"_time is [{_time}]")
    _file = splitoff(in_full_path)[1]
    _file_tup = os.path.splitext(_file)
    _new_file_name = _file_tup[0] + _time + _file_tup[1]
    _path = splitoff(in_full_path)[0]
    _out = pathmaker(_path, _new_file_name)
    log.debug(f"created file name [{_out}] from original name [{in_full_path}]")
    return _out


def ext_splitter(in_file, _out='file'):
    """
    Splits a file name by the extension and returns either the name or the extension.

    Parameters
    ----------
    in_file : str
        a file name
    _out : str, optional
        the part to return either "file" or "ext", by default 'file'

    Returns
    -------
    str
        either the file name or the file extension
    """
    if '.' in in_file:
        _file = in_file.rsplit('.', maxsplit=1)[0]
        _ext = in_file.rsplit('.', maxsplit=1)[1]
    else:
        _file = in_file
        _ext = 'folder'
    if _out == 'file':
        _output = _file
    elif _out == 'ext':
        _output = _ext
    elif _out == 'both':
        _output = (_file, _ext)

    return _output


def file_name_modifier(in_path, in_string, pos='prefix', new_ext=None, seperator=None):
    """
    changes a file name by inserting a string.

    Parameters
    ----------
    in_path : str
        the file path
    in_string : str
        the string inserted in the name
    pos : str, optional
        the position where to insert the string, either "prefix" or "postfix", by default 'prefix'
    new_ext : str, optional
        a new extension for th file name if not None, by default None
    seperator : str, optional
        the symbol that is used to seperate the old and new name, by default None

    Returns
    -------
    str
        the new file path

    Raises
    ------
    Exception
        checks the input for forbidden characters for filenames on Windows.
    """
    _forbiden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    if new_ext is not None and any(chars in new_ext for chars in _forbiden_chars):
        raise Exception(f"You can't use the following symbols in file names {str(_forbiden_chars)}")
    if seperator is not None and any(chars in seperator for chars in _forbiden_chars):
        raise Exception(f"You can't use the following symbols in file names {str(_forbiden_chars)}")
    if any(chars in in_string for chars in _forbiden_chars):
        raise Exception(f"You can't use the following symbols in file names {str(_forbiden_chars)}")
    _path, _file = splitoff(pathmaker(in_path))
    if new_ext is not None:
        _file = _file.rsplit('.', 1)[0] + new_ext if '.' in new_ext else _file.rsplit('.', 1)[0] + '.' + new_ext
    _file, _ext = _file.rsplit('.', 1)
    if seperator is None:
        _outfile = in_string + _file + '.' + _ext if pos == 'prefix' else _file + in_string + '.' + _ext
    else:
        _outfile = in_string + seperator + _file + '.' + _ext if pos == 'prefix' else _file + seperator + in_string + '.' + _ext
    _out = pathmaker(_path, _outfile)
    log.debug(f"created file name [{_out}] from original name [{in_path}]")
    return _out


def pickleit(obj, in_path):
    """
    saves an object as pickle file.

    Parameters
    ----------
    obj : object
        the object to save
    in_name : str
        the name to use for the pickled file
    in_dir : str
        the path to the directory to use
    """
    with open(pathmaker(in_path), 'wb') as filetopickle:
        log.debug(f"saved object [{str(obj)}] as pickle file [{in_path}]")
        pickle.dump(obj, filetopickle, pickle.HIGHEST_PROTOCOL)


def get_pickled(in_path):
    """
    loads a pickled file.

    Parameters
    ----------
    in_path : str
        the file path to the pickle file

    Returns
    -------
    object
        the pickled object
    """
    with open(pathmaker(in_path), 'rb') as pickletoretrieve:
        log.debug(f"loaded pickle file [{in_path}]")
        return pickle.load(pickletoretrieve)


def file_walker(in_path, in_with_folders=False):
    """
    walks recursively through a file system and returns a list of file paths.

    Parameters
    ----------
    in_path : str
        the path to the directory from where to start

    Returns
    -------
    list
        a list of all files found as file paths.
    """
    _out_list = []
    log.debug(f"start to walk and find all files in [{in_path}]")
    for root, _, filelist in os.walk(in_path):
        for files in filelist:
            _out = os.path.join(root, files)
            _out_list.append(_out)
        if in_with_folders is True and root != in_path:
            _out_list.append(root)
    log.debug(f"finished walking [{in_path}]")
    return _out_list


def _filter_by_fileage(file_path):
    return os.stat(file_path).st_ctime


def limit_amount_files_absolute(in_basename, in_directory, in_amount_max):
    existing_files = []
    for file in os.scandir(in_directory):
        if in_basename in file.name:
            existing_files.append(pathmaker(file.path))
    existing_files = sorted(existing_files, key=_filter_by_fileage)
    while len(existing_files) > in_amount_max:
        os.remove(existing_files.pop(0))


def limit_amount_of_files(in_basename, in_directory, in_amount_max):
    """
    limits the amount of files in a folder that have a certain basename,

    if needed deletes the oldest and renames every file to move up namewise.

    (second oldest gets named to the oldest,...)

    Parameters
    ----------
    in_basename : str
        the common string all file names that should be affected share.
    in_directory : str
        path of the directory to affect
    in_amount_max : int
        the max amount of files allowed
    """
    log.debug(f"checking amount of files with name [{in_basename}] in [{in_directory}], if more than [{in_amount_max}]")
    _existing_file_list = []
    for files in os.listdir(pathmaker(in_directory)):
        if in_basename in files:
            _existing_file_list.append(pathmaker(in_directory, files))
    if len(_existing_file_list) > in_amount_max:
        log.debug(f"files are exceding max amount by [{len(_existing_file_list)-in_amount_max}]")
        _existing_file_list.sort(key=os.path.getmtime)
        for index, files in enumerate(_existing_file_list):
            _rename_index = index - 1
            if index == 0:
                os.remove(files)
                log.debug(f"removing oldest file [{files}]")
            elif index > in_amount_max:
                break
            else:
                os.rename(files, _existing_file_list[_rename_index])
                log.debug(f"renaming file [{files}] to [{_existing_file_list[_rename_index]}]")


def create_folder(in_path):
    if os.path.isdir(in_path) is False:
        log.error(f"Folder '{in_path}' does **NOT** exist!")
        os.makedirs(in_path)
        log.info("Created Folder '{in_path}'")
    else:
        log.info(f"Folder '{in_path}' does exist!")


def bytes2human(n, annotate=False):
    # http://code.activestate.com/recipes/578019
    # >>> bytes2human(10000)
    # '9.8K'
    # >>> bytes2human(100001221)
    # '95.4M'
    symbols = ('Kb', 'Mb', 'Gb', 'Tb', 'Pb', 'Eb', 'Zb', 'Yb')
    prefix = {s: 1 << (i + 1) * 10 for i, s in enumerate(symbols)}
    for s in reversed(symbols):
        if n >= prefix[s]:
            _out = float(n) / prefix[s]
            if annotate is True:
                _out = '%.1f%s' % (_out, s)
            return _out
    _out = n
    if annotate is True:
        _out = "%sb" % _out
    return _out


# region [Main_Exec]
if __name__ == '__main__':
    pass


# endregion [Main_Exec]
