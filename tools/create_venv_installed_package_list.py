import os
import subprocess
import json
import shutil
import re
from collections import namedtuple
import sys
from textwrap import indent


def loadjson(in_file):
    with open(in_file, 'r') as jsonfile:
        _out = json.load(jsonfile)
    return _out


def writejson(in_object, in_file, sort_keys=True, indent=4, **kwargs):
    with open(in_file, 'w') as jsonoutfile:
        json.dump(in_object, jsonoutfile, sort_keys=sort_keys, indent=indent, **kwargs)


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


def main_dir_from_git():
    cmd = subprocess.run([shutil.which('git.exe'), "rev-parse", "--show-toplevel"], capture_output=True, text=True, shell=True, check=True)
    main_dir = pathmaker(cmd.stdout.rstrip('\n'))
    if os.path.isdir(main_dir) is False:
        raise FileNotFoundError('Unable to locate main dir of project')
    return main_dir


MAIN_DIR = main_dir_from_git()
OLD_CWD = os.getcwd()
os.chdir(MAIN_DIR)
CREATE_VENV_LOGS_FOLDER = pathmaker(MAIN_DIR, 'tools', 'create_venv_logs')

freeze_line_pypi_regex = r"(?P<pypiname>.*)\=\=(?P<version>[\d\.]+)"
freeze_line_git_regex = r"(?P<gitname>.*)\s\@\sgit\+(?P<url>.*)"
freeze_line_local_regex = r"(?P<localname>.*)\s\@\sfile:\/\/\/(?P<path>.*)"

freeze_line_regex = re.compile(r'|'.join([freeze_line_pypi_regex, freeze_line_git_regex, freeze_line_local_regex]))

PypiPackage = namedtuple("PypiPackage", ["pypiname", "version"])
GitPackage = namedtuple("GitPackage", ["gitname", "url"])
LocalPackage = namedtuple("LocalPackage", ["localname", "path"])


def _parse_packages(in_line: str):
    match = freeze_line_regex.match(in_line.strip())
    if match:
        group_dict = {k: v for k, v in match.groupdict().items() if v is not None}

        if 'version' in group_dict:
            return PypiPackage(**group_dict)
        if 'url' in group_dict:
            return GitPackage(**group_dict)
        if 'path' in group_dict:
            return LocalPackage(**group_dict)
    else:
        print('!' * 25 + f' no match with line:\n\n{in_line}\n\n')


def get_frozen_list():

    cmd = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True, shell=False, check=True)
    text = cmd.stdout.strip()
    for line in text.splitlines():
        if line != '':
            yield _parse_packages(line)


def to_json():
    path = pathmaker(CREATE_VENV_LOGS_FOLDER, 'installed_packages.json')
    _out = {'pypi': [], 'git': [], 'local': []}
    for item in get_frozen_list():
        if isinstance(item, PypiPackage):
            key = 'pypi'
        elif isinstance(item, GitPackage):
            key = 'git'
        elif isinstance(item, LocalPackage):
            key = "local"
        _out[key].append(item._asdict())
    writejson(_out, path, sort_keys=True)


def to_text():
    path = pathmaker(CREATE_VENV_LOGS_FOLDER, 'installed_packages.txt')
    _out = {'pypi': [], 'git': [], 'local': []}
    for item in get_frozen_list():
        if isinstance(item, PypiPackage):
            key = 'pypi'
        elif isinstance(item, GitPackage):
            key = 'git'
        elif isinstance(item, LocalPackage):
            key = "local"
        _out[key].append(item._asdict())

    text = ''
    for key, values in _out.items():
        text += f"{key}:\n"
        subtext = '\n'.join('- ' + ' | '.join(f"{subkey.removeprefix('pypi').removeprefix('git').removeprefix('local')}: {subvalue}" for subkey, subvalue in subvalues.items()) for subvalues in values)
        text += indent(subtext, '\t') + '\n\n\n'
    with open(path, 'w') as f:
        f.write(text)


INSTALLED_PACKAGES_FILES = {'json': to_json,
                            'txt': to_text,
                            'md': pathmaker(CREATE_VENV_LOGS_FOLDER, 'installed_packages.md'),
                            'html': pathmaker(CREATE_VENV_LOGS_FOLDER, 'installed_packages.html')}


def write_files(to_write: list[str]):
    for file_type in to_write:
        INSTALLED_PACKAGES_FILES.get(file_type)()


if __name__ == '__main__':
    write_files(['json', "txt"])
