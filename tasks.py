from invoke import task, Collection
import sys
import os
import subprocess
import shutil
from datetime import datetime, timedelta, date
from pprint import pprint
from time import time, sleep
import json
from discord.ext import ipc
from PIL import Image, ImageFilter, ImageOps
import toml
import tomlkit
from dotenv import load_dotenv
import re
from jinja2 import Environment, FileSystemLoader
from collections import namedtuple
from win10toast import ToastNotifier
import mdformat
from textwrap import dedent
from rich import print as rprint, inspect as rinspect, progress_bar
from rich.progress import track
from timeit import Timer, timeit
from zipfile import ZipFile, ZIP_LZMA
from importlib import import_module
import asyncio
from inspect import getmembers, ismodule
import isort
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
GIT_EXE = shutil.which('git.exe')


SCRATCH_BOILER = dedent("""
                # region[Imports]

                import os
                import subprocess
                import shutil
                import sys
                from inspect import getmembers, isclass, isfunction
                from pprint import pprint, pformat
                from typing import Union, Dict, Set, List, Tuple
                from datetime import tzinfo, datetime, timezone, timedelta
                from icecream import ic
                import re
                from dotenv import load_dotenv
                from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
                import random
                from functools import wraps, lru_cache, singledispatch, total_ordering, partial
                from contextlib import contextmanager
                from collections import Counter, ChainMap, deque, namedtuple, defaultdict
                from enum import Enum, unique, Flag, auto
                from rich import print as rprint, inspect as rinspect
                from time import time, sleep
                from timeit import Timer, timeit
                from textwrap import dedent
                from antipetros_discordbot.utility.gidtools_functions import writejson, writeit, readit, pathmaker, loadjson, clearit, pickleit, get_pickled

                # endregion [Imports]
                """).strip()


def readit(in_file, per_lines=False, in_encoding='utf-8', in_errors=None):

    with open(in_file, 'r', encoding=in_encoding, errors=in_errors) as _rfile:
        _content = _rfile.read()
    if per_lines is True:
        _content = _content.splitlines()

    return _content


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
                _out = '%.1f %s' % (_out, s)
            return _out
    _out = n
    if annotate is True:
        _out = "%s b" % _out
    return _out


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


def loadjson(in_file):
    with open(in_file, 'r') as jsonfile:
        _out = json.load(jsonfile)
    return _out


def writejson(in_object, in_file, sort_keys=True, indent=4):
    with open(in_file, 'w') as jsonoutfile:
        print(f"writing json '{in_file}'")
        json.dump(in_object, jsonoutfile, sort_keys=sort_keys, indent=indent)


def main_dir_from_git():
    cmd = subprocess.run([GIT_EXE, "rev-parse", "--show-toplevel"], capture_output=True, text=True, shell=True, check=True)
    main_dir = pathmaker(cmd.stdout.rstrip('\n'))
    if os.path.isdir(main_dir) is False:
        raise FileNotFoundError('Unable to locate main dir of project')
    return main_dir


THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
VENV_ACTIVATOR_PATH = pathmaker(THIS_FILE_DIR, '.venv/Scripts/activate.bat', rev=True)
load_dotenv(pathmaker(THIS_FILE_DIR, 'tools/_project_devmeta.env'))
BACKUP_FOLDER = pathmaker(r"D:\Archives\git_bundles")
FOLDER = {'docs': pathmaker(THIS_FILE_DIR, 'docs'),
          'docs_data': pathmaker(THIS_FILE_DIR, 'docs', 'resources', 'data'),
          'docs_templates': pathmaker(THIS_FILE_DIR, 'docs', 'resources', 'templates'),
          'images': pathmaker(THIS_FILE_DIR, 'art', 'finished', 'images'),
          'gifs': pathmaker(THIS_FILE_DIR, 'art', 'finished', 'gifs'),
          'docs_raw_text': pathmaker(THIS_FILE_DIR, 'docs', 'resources', 'raw_text'),
          'scratches': pathmaker(THIS_FILE_DIR, 'tools', 'scratches'),
          'archived_scratches': pathmaker(THIS_FILE_DIR, 'misc', 'archive', 'archived_scratches'),
          'cogs': pathmaker(THIS_FILE_DIR, 'antipetros_discordbot', 'cogs'),
          'venv_setup_settings': pathmaker(THIS_FILE_DIR, 'tools', 'venv_setup_settings')}

FILES = {'bot_info.json': pathmaker(FOLDER.get('docs_data'), 'bot_info.json'),
         'links_data.json': pathmaker(FOLDER.get('docs_data'), 'links_data.json'),
         'future_plans.txt': pathmaker(FOLDER.get('docs_raw_text'), 'future_plans.txt'),
         'command_data.json': pathmaker(FOLDER.get('docs_data'), 'command_data.json'),
         'external_dependencies.json': pathmaker(FOLDER.get('docs_data'), 'external_dependencies.json'),
         'cogs_misc.txt': pathmaker(FOLDER.get('docs_raw_text'), 'cogs_misc.txt'),
         'cogs_info.md': pathmaker(THIS_FILE_DIR, 'antipetros_discordbot', 'cogs', 'cogs_info.md'),
         'archived_scratches_content_table.json': pathmaker(FOLDER.get('archived_scratches'), 'archived_scratches_content_table.json')}

HEADING_REGEX = re.compile(r"(?P<level>\#+)\s*(?P<name>.*)")
ALT_HEADING_REGEX = re.compile(r"(?P<level>\#+).*\[(?P<name>.*)\]")
ALT_ALT_HEADING_REGEX = re.compile(r'(?P<level>\<h\d\>)(?P<name>.*?)\<')
SUB_COMMAND_REGEX = re.compile(r"Commands:\n(?P<sub_commands>.*)", re.DOTALL)
SUB_COMMAND_NAME_VALUE_REGEX = re.compile(r"(?P<name>[\w\-]+)\s+(?P<description>.*)")
JINJA_ENV = Environment(loader=FileSystemLoader(FOLDER.get('docs_templates')))


def file_name_timestamp(with_brackets=False):
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    if with_brackets is True:
        return f"[{timestamp}]"
    return timestamp


def flit_data(to_get: str):
    pyproject_toml_data = toml.load(pathmaker(THIS_FILE_DIR, 'pyproject.toml'))
    data = pyproject_toml_data
    path_keys = ['tool', 'flit']

    if to_get == 'first_script':
        path_keys += ['scripts']
    elif to_get in ['project_name', "author_name", "dependencies", "license"]:
        path_keys += ['metadata']

    for key in path_keys:
        data = data.get(key, {})

    if to_get == 'first_script':
        return list(data)[0]

    if to_get == 'project_name':
        return data.get('module')
    if to_get == 'author_name':
        return data.get('author')
    if to_get == 'dependencies':
        return data.get('requires')
    if to_get == 'license':
        return data.get('license')


ANTIPETROS_CLI_COMMAND = flit_data('first_script')


COLLECT_COMMAND = 'collect-data'

PROJECT_NAME = flit_data('project_name')

PROJECT_AUTHOR = flit_data('author_name')

NOTIFIER = ToastNotifier()


def activator_run(c, command, echo=True, **kwargs):
    with c.prefix(VENV_ACTIVATOR_PATH):
        result = c.run(command, echo=echo, **kwargs)
        return result


@task
def clean_repo(c):
    to_clean_folder = ['logs', 'dist', 'report']
    to_clean_files = ['antipetros_permission_dump.json',
                      'antidevtros_permission_dump.json']
    main_dir = THIS_FILE_DIR
    for dirname, folderlist, filelist in os.walk(main_dir):
        if all(excl_folder.casefold() not in dirname.casefold() for excl_folder in ['.git', '.vscode']):
            for folder in folderlist:
                if folder.casefold() in to_clean_folder:
                    path = pathmaker(dirname, folder)
                    shutil.rmtree(path)
                    print(f"remove folder '{path}'")
            for file in filelist:
                if file.casefold() in to_clean_files:
                    path = pathmaker(dirname, file)
                    os.remove(pathmaker(dirname, file))
                    print(f"removed file '{path}'")
    print("finished cleaning repo")


@task(help={'output_file': 'alternative output file, defaults to /docs/resources/data'})
def get_command_data(c, output_file=None, verbose=False):
    """
    Runs the Bot to collect data about the commands of all enabled Cogs.

    Runs without actually connecting to Discord.

    """
    output_file = pathmaker(output_file, rev=True) if output_file is not None else output_file
    command = f"{ANTIPETROS_CLI_COMMAND} {COLLECT_COMMAND} command"
    if output_file is not None:
        command += f' -o "{output_file}"'
    if verbose is True:
        command += ' -v'
    activator_run(c, command)


@task(help={'output_file': 'alternative output file, defaults to /docs/resources/data'})
def get_config_data(c, output_file=None, verbose=False):
    output_file = pathmaker(output_file, rev=True) if output_file is not None else output_file
    command = f"{ANTIPETROS_CLI_COMMAND} {COLLECT_COMMAND} config"
    if output_file is not None:
        command += f' -o "{output_file}"'
    if verbose is True:
        command += ' -v'
    activator_run(c, command)


@task(help={'output_file': 'alternative output file'})
def get_help_data(c, output_file=None, verbose=False):
    output_file = pathmaker(output_file, rev=True) if output_file is not None else output_file
    command = f"{ANTIPETROS_CLI_COMMAND} {COLLECT_COMMAND} bot-help"
    if output_file is not None:
        command += f' -o "{output_file}"'
    if verbose is True:
        command += ' -v'
    activator_run(c, command)


@task(pre=[get_command_data, get_config_data, get_help_data])
def collect_data(c):
    print('+' * 50)
    print('\ncollected all data\n')
    print('+' * 50)


@task
def clean_userdata(c, dry_run=False):
    data_pack_path = pathmaker(THIS_FILE_DIR, PROJECT_NAME, "init_userdata\data_pack")

    folder_to_clear = ['archive', 'user_env_files', 'env_files', 'performance_data', 'stats', 'database', 'debug', 'temp_files']
    files_to_clear = ["auto_accept_suggestion_users.json",
                      "blacklist.json",
                      "give_aways.json",
                      "registered_steam_workshop_items.json",
                      "notified_log_files.json",
                      "blacklist.json",
                      "registered_timezones.json",
                      "who_is_trigger_phrases.json",
                      "team_items.json",
                      "subscription_topics_data.json",
                      "bot_feature_suggestions.json",
                      "message_reaction_instructions_data.json",
                      "is_online_messages.json",
                      "notified_log_files.json",
                      "stored_reasons.json",
                      "faq_name_table.json"]

    if dry_run is True:
        print('')
        print('#' * 150)
        print(' These Files and Folders would have been deleted '.center(150, '#'))
        print('#' * 150)
        print('')

    for dirname, folderlist, filelist in os.walk(data_pack_path):
        for file in filelist:
            file = file.casefold()
            if file in files_to_clear:
                if dry_run is True:
                    print(pathmaker(dirname, file))
                else:
                    os.remove(pathmaker(dirname, file))
                    print(f"removed file: {os.path.basename(pathmaker(dirname, file))}")
        for folder in folderlist:
            folder = folder.casefold()
            if folder in folder_to_clear:
                for file in os.scandir(pathmaker(dirname, folder)):
                    if file.is_file() and not file.name.endswith('.placeholder'):
                        if dry_run is True:
                            print(pathmaker(file.path))
                        else:
                            os.remove(file.path)
                            print(f"removed file: {file.name}")


@task(clean_userdata)
def store_userdata(c):
    exclusions = list(map(lambda x: f"-i {x}", ["oauth2_google_credentials.json",
                                                "token.pickle",
                                                "save_link_db.db",
                                                "save_suggestion.db",
                                                "general_antipetros.db",
                                                "archive/*",
                                                "performance_data/*",
                                                "stats/*",
                                                "last_shutdown_message.pkl"]))
    options = [f"-n {PROJECT_NAME}",
               f"-a {PROJECT_AUTHOR}",
               "-64",
               f"-cz {pathmaker(THIS_FILE_DIR,PROJECT_NAME, 'init_userdata', rev=True)}"]
    command = "appdata_binit " + ' '.join(options + exclusions)
    activator_run(c, command)


@task
def subreadme_toc(c, output_file=None):
    def make_title(in_string: str):
        _out = in_string.replace('_', ' ').title()
        return _out
    output_file = pathmaker(THIS_FILE_DIR, 'sub_readme_links.md') if output_file is None else output_file
    remove_path_part = pathmaker(THIS_FILE_DIR).casefold() + '/'
    found_subreadmes = []
    for dirname, folderlist, filelist in os.walk(THIS_FILE_DIR):
        if all(excl_dir.casefold() not in dirname.casefold() for excl_dir in ['.git', '.venv', '.vscode', '__pycache__', '.pytest_cache', "private_quick_scripts"]):
            for file in filelist:
                if file.casefold() == 'readme.md' and dirname.casefold() != THIS_FILE_DIR.casefold():
                    found_subreadmes.append((os.path.basename(dirname), pathmaker(dirname, file).casefold().replace(remove_path_part, '')))
    with open(output_file, 'w') as f:
        f.write('# Sub-ReadMe Links\n\n')
        for title, link in found_subreadmes:
            f.write(f"\n* [{make_title(title)}]({link})\n\n---\n")


@task
def collect_todos(c, output_file=None):
    current_branch = c.run("git rev-parse --abbrev-ref HEAD", hide='out').stdout.strip()
    base_url = f"https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/{current_branch}"
    line_specifier = "#L"
    output_file = pathmaker(THIS_FILE_DIR, "docs", "all_todos.md") if output_file is None else pathmaker(output_file)
    remove_path_part = pathmaker(THIS_FILE_DIR).casefold() + '/'
    pyfiles = []
    todos = []
    for dirname, folderlist, filelist in os.walk(pathmaker(THIS_FILE_DIR, PROJECT_NAME)):
        if all(excl_dir.casefold() not in dirname.casefold() for excl_dir in ['.git', '.venv', '.vscode', '__pycache__', '.pytest_cache', "private_quick_scripts"]):
            for file in filelist:
                if file.endswith('.py'):
                    path = pathmaker(dirname, file)
                    rel_path = path.casefold().replace(remove_path_part, '')
                    with open(path, 'r') as f:
                        content = f.read()
                    pyfiles.append({"name": file, 'path': path, "rel_path": rel_path, 'content': content, 'content_lines': content.splitlines(), 'todos': []})
    for file_data in pyfiles:
        has_todo = False
        for index, line in enumerate(file_data.get('content_lines')):
            if '# TODO' in line:
                has_todo = True
                file_data["todos"].append((line, index))
        if has_todo is True:
            todos.append(file_data)
    with open(output_file, 'w') as f:
        f.write('# TODOs collected from files\n\n')
        for item in todos:
            f.write(f"## {item.get('name')}\n\n")
            for todo, line_number in item.get('todos'):
                cleaned_todo = todo.replace('# TODO', '').strip().lstrip(':').strip()
                link = f"{base_url}/{item.get('rel_path')}{line_specifier}{str(line_number)}"
                text = f"line {str(line_number)}:"
                f.write(f"- [ ] [{text}]({link})  `{cleaned_todo}`\n<br>\n")
            f.write('\n---\n\n')


@task
def docstring_data(c, output_file=None):
    def check_if_empty(path):
        with open(path, 'r') as f:
            content = f.read()
        return len(content) == 0
    from docstr_coverage.coverage import get_docstring_coverage
    pyfiles = []
    for dirname, folderlist, filelist in os.walk(pathmaker(THIS_FILE_DIR, PROJECT_NAME)):
        if all(excl_dir.casefold() not in dirname.casefold() for excl_dir in ['.git', '.venv', '.vscode', '__pycache__', '.pytest_cache', "private_quick_scripts", "dev_tools_and_scripts", 'gidsql']):
            for file in filelist:
                if file.endswith('.py'):
                    path = pathmaker(dirname, file)
                    if check_if_empty(path) is False:
                        pyfiles.append(path)
    file_stats, overall_stats = get_docstring_coverage(pyfiles, skip_magic=True)
    docstring_stats = {"files": file_stats, 'overall': overall_stats}

    output_file = pathmaker(THIS_FILE_DIR, "docs", "all_missing_docstrings.json") if output_file is None else pathmaker(output_file)
    writejson(docstring_stats, output_file)


@task
def optimize_art(c, quality=100):
    folder = pathmaker(THIS_FILE_DIR, 'art', 'finished', 'images')
    for file in os.scandir(folder):
        if file.is_file() and file.name.endswith('.png') or file.name.endswith('.jpg'):
            print(f'optimizing image "{file.name}"')
            orig_size = os.path.getsize(file.path)
            print(f"original size: {bytes2human(orig_size, True)}")
            img = Image.open(file.path)

            img.save(file.path, quality=quality, optimize=True)
            new_size = os.path.getsize(file.path)
            size_dif = max(new_size, orig_size) - min(new_size, orig_size)
            pre_mod = '-' if orig_size > new_size else '+'
            print(f"finished optimizing '{file.name}'")
            print(f"New size: {bytes2human(new_size, True)}")
            print(f"Difference: {pre_mod}{bytes2human(size_dif, True)}")
            print('#' * 50 + "\n")
            if file.name.endswith('.jpg'):
                os.rename(file.path, file.path.replace('.jpg', '.png'))


REQUIREMENT_EXTRAS = [('discord-flags', None)]
REQUIREMENT_FIXED = []


def _get_version_from_freeze(context, package_name, markers=None):  # markers is list of strings
    result = activator_run(context, "pip freeze", echo=False, hide=True).stdout.strip()
    for req_line in result.splitlines():
        req_line = req_line.strip()
        req_name = req_line.split('==')[0]
        if req_name.casefold() == package_name.casefold():
            if markers is not None:
                mod_req_line = req_line + '; ' + ', '.join(markers)
                return mod_req_line
        return req_line


@task
def clear_icecream(c):
    py_files = []
    for dirname, folderlist, filelist in os.walk(os.getenv('TOPLEVELMODULE')):
        if '__pycache__' not in dirname.casefold():
            for file in filelist:
                if file.endswith('.py'):
                    py_files.append(pathmaker(dirname, file))
    for py_file in py_files:
        new_content_lines = []
        with open(py_file, 'r') as f_orig:
            for line in f_orig.read().splitlines():
                if not line.strip().startswith('ic('):
                    new_content_lines.append(line)
        with open(py_file, 'w') as f_mod:
            f_mod.write('\n'.join(new_content_lines))


PACKAGE_URL_REGEX = re.compile(r"home-page\:\s?(?P<url>.*)", re.IGNORECASE)


def get_package_url(c, package_name):
    package_info = activator_run(c, f"pip show {package_name}")
    url_match = PACKAGE_URL_REGEX.search(package_info)
    if url_match:
        return url_match.group('url').strip()


@task
def set_requirements(c):
    old_cwd = os.getcwd()
    os.chdir(os.getenv('TOPLEVELMODULE'))
    activator_run(c, 'pigar --without-referenced-comments')
    pigar_req_file = pathmaker(os.getenv('TOPLEVELMODULE'), 'requirements.txt')
    with open(pigar_req_file, 'r') as f:
        req_content = f.read()
    _requirements = []
    for line in req_content.splitlines():
        if not line.startswith('#') and line != '' and 'antipetros_discordbot' not in line and "pyqt5_sip" not in line.casefold():
            line = line.replace(' ', '')
            _requirements.append(line)
    for req in REQUIREMENT_EXTRAS:
        _requirements.append(_get_version_from_freeze(c, req[0], req[1]))
    _requirements += REQUIREMENT_FIXED
    os.remove(pigar_req_file)
    os.chdir(os.getenv('WORKSPACEDIR'))
    with open('pyproject.toml', 'r') as f:

        pyproject = tomlkit.parse(f.read())
    pyproject["tool"]["flit"]["metadata"]['requires'] = _requirements
    with open('pyproject.toml', 'w') as f:
        f.write(tomlkit.dumps(pyproject))
    prod_file = pathmaker('temp', 'temp_requirements.json')
    specifier_regex = re.compile(r"(\=\=)|(\>\=)|(\<\=)|(\~\=)")
    temp_stored_requirements = []
    for req in _requirements:
        name, version = specifier_regex.split(req)
        temp_stored_requirements.append({'name': name.strip(),
                                         'version': version.strip(),
                                         'url': get_package_url(c, name)})
    writejson(temp_stored_requirements, prod_file, sort_keys=False)
    os.chdir(old_cwd)


def get_cog_misc_data():
    text_file_regex = re.compile(r"\n?(?P<key_words>[\w\s]+).*?\=.*?(?P<value_words>.*?(?=(?:\n[^\n]*?\=)|$))", re.DOTALL)
    content = readit(FILES.get('cogs_misc.txt'))
    results = {}
    for match_data in COMMAND_TEXT_FILE_REGEX.finditer(content):
        if match_data:
            key_word = match_data.group('key_words').strip().casefold()
            results[key_word] = '\n'.join(line.strip() for line in match_data.group('value_words').splitlines() if not line.startswith('#'))

    return results


def create_cog_info_tocs(content):
    _headings = {}
    for line in content.splitlines():
        if line.strip().startswith('##') or line.strip().startswith('<p align="center"><h'):
            if '<p align="center">' in line:
                heading_match = ALT_ALT_HEADING_REGEX.search(line)
            else:
                heading_match = HEADING_REGEX.search(line)
            level, name = heading_match.groups()
            if level.startswith('<'):
                level = '#' * int(level.replace('<', '').replace('h', '').replace('>', ''))
            if name.casefold() not in ['toc', 'commands:'] and 2 <= len(level) <= 5:
                _headings[name.strip().strip('_*').strip()] = (len(level) - 1, name.replace(' ', '-').lower())
    template = JINJA_ENV.get_template('tocs_template.md.jinja')
    return template.render(tocs=_headings)


@task
def make_cogs_info(c):
    cog_info_file = pathmaker(THIS_FILE_DIR, 'antipetros_discordbot', 'cogs', 'README.md')
    command_data = loadjson(FILES.get('command_data.json'))
    template_data = {'cog_image_location': "art/finished/images/cog_icon.png",
                     'current_cogs': command_data,
                     'misc': get_cog_misc_data()}
    template = JINJA_ENV.get_template('cogs_info_template_vers_1.md.jinja')
    result_string = template.render(template_data)
    toc_string = create_cog_info_tocs(result_string)
    result = result_string.replace('$$$TOC$$$', toc_string)
    with open(cog_info_file, 'w') as f:
        f.write(result)


def get_subcommands(c, script_name):
    _out = {}
    raw_data = activator_run(c, f"{script_name} --help", hide=True).stdout

    sub_commands_match = SUB_COMMAND_REGEX.search(raw_data)
    for line in sub_commands_match.group('sub_commands').splitlines():
        if line != '':
            name, desc = SUB_COMMAND_NAME_VALUE_REGEX.search(line).groups()
            if 'dummy function' not in desc:
                _out[name.strip()] = desc.strip()

    return _out


def get_dependencies():
    _out = {}
    raw_dependencies = flit_data('dependencies')
    for raw_dependency in raw_dependencies:
        if "uvloop" not in raw_dependency:
            try:
                name, version = raw_dependency.split('==')
                _out[name.strip()] = version.strip()
            except ValueError as error:
                print(raw_dependency)
                raise error

    return dict(sorted(_out.items()))


def get_python_version():
    return sys.version.split()[0].strip()


def make_path_relative(in_path):
    return pathmaker(in_path).replace(pathmaker(THIS_FILE_DIR) + '/', '')


def get_brief_description():
    path = pathmaker(FOLDER.get('docs_raw_text'), 'brief_description.md')
    if os.path.isfile(path) is False:
        return ''
    return readit(path)


def get_long_description():
    path = pathmaker(FOLDER.get('docs_raw_text'), 'long_description.md')
    if os.path.isfile(path) is False:
        return ''
    return readit(path)


def get_package_version():
    init_file = pathmaker(THIS_FILE_DIR, PROJECT_NAME, "__init__.py")
    with open(init_file, 'r') as f:
        content = f.read()
    version_line = None

    for line in content.splitlines():
        if '__version__' in line:
            version_line = line
            break
    if version_line is None:
        raise RuntimeError('Version line not found')
    return version_line.replace('__version__', '').replace('=', '').replace('"', '').replace("'", "").strip()


COMMAND_TEXT_FILE_REGEX = re.compile(r"\n?(?P<key_words>[\w\s]+).*?\=.*?(?P<value_words>.*?(?=(?:\n[^\n]*?\=)|$))", re.DOTALL)


def get_future_plans():
    path = FILES.get('future_plans.txt')
    if os.path.isfile(path) is False:
        return {}
    content = readit(path)
    results = {}
    for match_data in COMMAND_TEXT_FILE_REGEX.finditer(content):
        if match_data:
            key_word = match_data.group('key_words').strip().casefold()
            results[key_word] = '\n'.join(line.strip() for line in match_data.group('value_words').splitlines() if not line.startswith('#'))
    return results


def get_links():
    bot_info_data = loadjson(FILES.get('bot_info.json'))
    link_data = loadjson(FILES.get('links_data.json')) if os.path.isfile(FILES.get('links_data.json')) else {}
    link_data[bot_info_data.get('guild') + " Discord Server"] = bot_info_data.get('invite_url')
    return link_data


def get_external_dependencies():
    data = loadjson(FILES.get('external_dependencies.json'))
    return data


def create_tocs(content, max_level=3):
    _headings = {}
    for line in content.splitlines():
        if line.strip().startswith('##'):
            if '<p align="center"><b>' in line:
                heading_match = ALT_HEADING_REGEX.search(line)
            else:
                heading_match = HEADING_REGEX.search(line)
            level, name = heading_match.groups()
            if name.casefold() != 'toc' and len(level) <= max_level and 'Cog' not in name:
                _headings[name.strip()] = (len(level) - 1, name.replace(' ', '-').lower())
    template = JINJA_ENV.get_template('tocs_template.md.jinja')
    return template.render(tocs=_headings)


def make_readme(c):
    bot_info_data = loadjson(FILES.get('bot_info.json'))
    command_data = loadjson(FILES.get('command_data.json'))
    template_data = {'project_name': flit_data('project_name').replace('_', ' ').title(),
                     'license': flit_data("license"),
                     'antipetros_image_location': make_path_relative(pathmaker(FOLDER.get('images'), 'AntiPetros_for_readme.png')),
                     'brief_description': get_brief_description(),
                     'bot_name': bot_info_data.get('display_name'),
                     'package_version': get_package_version(),
                     'package_name': flit_data('project_name'),
                     'long_description': get_long_description(),
                     'main_script_name': flit_data("first_script"),
                     'scripts': get_subcommands(c, flit_data("first_script")),
                     'dependencies': get_dependencies(),
                     'python_version': get_python_version(),
                     'future_plans': get_future_plans(),
                     'links': get_links(),
                     'current_cogs': command_data,
                     'external_dependencies': get_external_dependencies()}
    template = JINJA_ENV.get_template('readme_github_vers_1.md.jinja')
    result_string = template.render(template_data)
    toc_string = create_tocs(result_string)
    result = result_string.replace('$$$TOC$$$', toc_string)
    output_file = pathmaker(THIS_FILE_DIR, 'README.md')
    with open(output_file, 'w') as f:
        f.write(result)


def get_version(only_version=False):
    init_file = pathmaker(THIS_FILE_DIR, PROJECT_NAME, "__init__.py")
    with open(init_file, 'r') as f:
        content = f.read()
    version_line = None

    for line in content.splitlines():
        if '__version__' in line:
            version_line = line
            break
    if version_line is None:
        raise RuntimeError('Version line not found')
    cleaned_version_str = version_line.replace('__version__', '').replace('=', '').replace('"', '').replace("'", "").strip()
    major, minor, patch = cleaned_version_str.split('.')
    if only_version is True:
        return major, minor, patch
    return (major, minor, patch), content, version_line


def increment_version(increment_part='patch'):
    init_file = pathmaker(THIS_FILE_DIR, PROJECT_NAME, "__init__.py")
    version_tuple, content, version_line = get_version()
    major, minor, patch = version_tuple

    if increment_part == 'patch':
        patch = str(int(patch) + 1)
    elif increment_part == 'update':
        minor = str(int(minor) + 1)
        patch = str(0)
    elif increment_part == 'release':
        major = str(int(major) + 1)
        minor = str(0)
        patch = str(0)
    with open(init_file, 'w') as f:
        f.write(content.replace(version_line, f"__version__ = '{major}.{minor}.{patch}'"))
    return major, minor, patch


def commit_push(c, typus='patch', description=None):
    typus = typus.casefold()

    major, minor, patch = increment_version(typus)
    make_readme(c)
    version_str = {'release': f"**{major}**.{minor}.{patch}",
                   'update': f"{major}.**{minor}**.{patch}",
                   'patch': f"{major}.{minor}.**{patch}**"}.get(typus, f"{major}.{minor}.{patch}")
    msg = {'release': f"🎆🎆 Release of version {version_str} 🎆🎆",
           'update': f"🏷️ update {version_str}",
           'patch': f"🛠️ fix version: {version_str}"}.get(typus, f"🍱 {typus} {version_str}`")

    if description is not None:
        msg += f' | {description}'
    os.chdir(main_dir_from_git())
    c.run("git add .", echo=True)
    sleep(2)
    c.run(f'git commit -am "{msg}"', echo=True)
    sleep(2)
    c.run('git push', echo=True)
    sleep(2)


@task(pre=[clean_repo, collect_data, make_cogs_info, store_userdata, set_requirements, make_readme])
def build(c, typus='patch', description=None):
    commit_push(c, typus, description)
    os.chdir(main_dir_from_git())
    c.run("flit publish", echo=True)
    from dev_tools_and_scripts.scripts.launch_in_server import update_launch

    update_launch()
    NOTIFIER.show_toast(title=f"Finished Building {PROJECT_NAME}", icon_path=r"art/finished/icons/pip.ico", duration=15, msg=f"Published {PROJECT_NAME}, Version {get_package_version()} to PyPi")


def get_alternative_name(name, number=0, extension='.py'):
    if number == 0:
        mod_name = name
    else:
        mod_name = f"{name}_{number}"

    if mod_name.casefold() in {file.name.split('.')[0].casefold() for file in os.scandir(FOLDER.get('scratches')) if file.is_file() and file.name.endswith(extension)}:
        return get_alternative_name(name, number + 1)
    return mod_name


@task
def new_scratch(c, prefix=None):
    if os.path.isdir(FOLDER.get('scratches')) is False:
        os.makedirs(FOLDER.get('scratches'))
    name = "scratch" if prefix is None else f"{prefix}_scratch"
    file_name = get_alternative_name(name) + '.py'
    full_path = pathmaker(FOLDER.get('scratches'), file_name)
    with open(full_path, 'w') as f:
        f.write(SCRATCH_BOILER + '\n\n\n\n')
        f.write("if __name__ == '__main__':\n")
        f.write("\tpass\n")


@task
def new_notebook(c, name):
    if os.path.isdir(FOLDER.get('scratches')) is False:
        os.makedirs(FOLDER.get('scratches'))
    name = name.casefold()
    file_name = get_alternative_name(name, extension='.ipynb') + '.ipynb'
    full_path = pathmaker(FOLDER.get('scratches'), file_name)
    with open(full_path, 'w') as f:
        f.write("")


def extend_content_table(archive_name, file_paths):
    name = archive_name.split('.')[0]
    scratch_folder = pathmaker(FOLDER.get('scratches'))
    content_table = loadjson(FILES.get('archived_scratches_content_table.json'))
    content_table[name] = [file_path[1] for file_path in file_paths]
    writejson(content_table, FILES.get('archived_scratches_content_table.json'))


@task
def archive_scratches(c):
    scratch_folder = pathmaker(FOLDER.get('scratches'))
    archive_name = f"scratches_{file_name_timestamp(False)}.zip"
    archive_path = pathmaker(FOLDER.get('archived_scratches'), archive_name)
    file_paths = []
    for dirname, folderlist, filelist in os.walk(scratch_folder):
        if '__pycache__' not in dirname and '.git' not in dirname:
            for file in filelist:
                path = pathmaker(dirname, file)
                rel_path = pathmaker(os.path.relpath(path, scratch_folder))
                file_paths.append((path, rel_path))
    extend_content_table(archive_name, file_paths)
    with ZipFile(archive_path, 'w', compression=ZIP_LZMA) as zippy:
        for full_path, relative_path in track(file_paths, description='archiving scratches folder...'):
            rprint(f"archiving file [bold green][u]{relative_path}[/u][/bold green]")
            zippy.write(full_path, relative_path)
    shutil.rmtree(scratch_folder)
    os.makedirs(scratch_folder)


@task
def new_cog(c, name, category="general"):
    code_template_environment = Environment(loader=FileSystemLoader(pathmaker(THIS_FILE_DIR, "dev_tools_and_scripts", "template_handling", "templates")))
    folder_name = category.lower().replace(' ', '_') + '_cogs'
    folder_path = pathmaker(FOLDER.get('cogs'), folder_name)

    if os.path.isdir(folder_path) is False:
        os.makedirs(folder_path)
        with open(pathmaker(folder_path, '__init__.py'), 'w') as f:
            f.write('')

    cog_file_name = name.lower() + '_cog.py'
    cog_path = pathmaker(folder_path, cog_file_name)
    if os.path.isfile(cog_path) is True:
        raise FileExistsError(cog_path)

    template = code_template_environment.get_template("cog_template.py.jinja")
    with open(cog_path, 'w') as f:
        f.write(template.render(cog_name=name.replace('_', ' ').title().replace(' ', '') + "Cog"))


@task
def bot_restart(c):
    from dev_tools_and_scripts.scripts.launch_in_server import restart
    restart()


@task()
def shutdown_bot(c):

    load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\antipetros_discordbot\token.env")
    client = ipc.Client(secret_key=os.getenv('IPC_SECRET_KEY'))
    request_thing = client.request("shut_down", member_id=576522029470056450)

    print(client.loop.run_until_complete(request_thing))
    client.loop.run_until_complete(client.session.close())


@task
def message_hi(c):

    load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\antipetros_discordbot\token.env")
    client = ipc.Client(secret_key=os.getenv('IPC_SECRET_KEY'))
    request_thing = client.request("say_hi", name="Giddi is the name")

    print(client.loop.run_until_complete(request_thing))
    client.loop.run_until_complete(client.session.close())


def get_all_members(in_object):

    o_name = in_object.__name__
    _out = {o_name: []}

    for name, subobject in getmembers(in_object):
        if not name.startswith('_') and not name.endswith('_'):
            try:
                if in_object.__name__ in subobject.__module__:
                    _out[o_name].append(name)
            except AttributeError:
                if ismodule(subobject):
                    print(f" {subobject.__name__} ".center(50, 'm'))
                elif isinstance(subobject, (str, int, float, tuple, set, list, dict)):
                    print(f" {name} ".center(50, 'c'))

    return _out


def isort_config():
    pyproject = toml.load(pathmaker(THIS_FILE_DIR, 'pyproject.toml'))
    return pyproject.get('tool', {}).get('isort', {})


@task
def module_members(c, module_name):
    output_folder = pathmaker(FOLDER.get('scratches'), "module_import_data")
    if os.path.isdir(output_folder) is False:
        os.makedirs(output_folder)
    module = import_module(module_name)
    all_members = get_all_members(module)

    text = []
    for key, member_list in all_members.items():
        text.append(f"from {key} import {', '.join(member_list)}")
    code_string = isort.code('\n'.join(text), **isort_config())
    with open(pathmaker(output_folder, f"{module_name.replace('.','_')}_members.py"), 'w') as f:
        f.write(code_string)


def process_pip_freeze_data(in_data: str):
    _out = {}
    for line in in_data.splitlines():
        if line != '' and not "@ git" in line and not "@ file" in line:
            name, version = line.split('==')
            _out[name.strip().casefold()] = line.strip()
    return _out


@task()
def pin_reqs(c):
    req_line_regex = re.compile(r"\=\=|\>\=|\<\=|\~\=|\!\=", re.IGNORECASE)
    req_files = []
    for file in os.scandir(FOLDER.get('venv_setup_settings')):
        if file.is_file() and file.name.startswith('required_') and 'personal_packages' not in file.name.casefold() and not 'from_github' in file.name.casefold():
            req_files.append(pathmaker(file.path))
    pprint(req_files)
    pip_freeze_data = process_pip_freeze_data(activator_run(c, 'pip freeze').stdout)
    for req_file in req_files:
        print(req_file)
        new_req_file_content = []
        for line in readit(req_file).splitlines():
            line = line.casefold()
            if line != '' and not line.startswith('https:'):
                name = req_line_regex.split(line)[0].replace('_', '-')
                for pinned_req_name, pinned_req_line in pip_freeze_data.items():
                    if name.casefold() == pinned_req_name:
                        line = pinned_req_line
            new_req_file_content.append(line)
        with open(req_file, 'w') as f:
            f.write('\n'.join(new_req_file_content))


def parse_git_branches(raw_text: str):
    _out = []
    for line in raw_text.splitlines():
        if line != '' and "origin/HEAD" not in line and "master" not in line:
            line = line.strip(' *')
            if line.casefold() != 'development':
                _out.append(line)
    _out.sort(key=lambda x: (x.startswith('remotes/'), x.replace('remotes/', ''), x.split('/')[-1]))
    return _out


@task(name='mass-git-rebase')
def update_git_branches_from_development(c):
    result = c.run("git branch", echo=False, hide=True)
    parsed_data = parse_git_branches(result.stdout)
    for branch in parsed_data:
        c.run(f"git checkout {branch} && git rebase development")


def get_branch_names(c, branch_type: str = 'local'):

    command = "git branch"
    if branch_type == "remote":
        command += " -r"
    elif branch_type == "all":
        command += " -a"

    result = c.run(command, echo=False, hide=True)
    return parse_git_branches(result.stdout)


@task(name='git-bundle')
def create_git_bundle(c, target_folder=None, target_name=None):
    target_folder = pathmaker(BACKUP_FOLDER) if target_folder is None else pathmaker(target_folder)
    target_name = os.getenv('PROJECT_NAME') if target_name is None else target_name
    target_name = f"{target_name}[{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}].bundle"
    target_path = pathmaker(target_folder, target_name, rev=True)
    c.run(f"git bundle create {target_path} --all", echo=True)


@task(name='mass-git-branch-delete', pre=[create_git_bundle])
def delete_all_git_branches_except_development(c, force=False):
    force = '-d' if force is False else '-D'
    not_fully_merged = []
    local_branches = get_branch_names(c, 'local')
    for branch in local_branches:
        try:
            c.run(f"git branch {force} {branch}", echo=True)
        except Exception as error:
            print(error)
            not_fully_merged.append(branch)
        try:
            c.run(f"git push -d origin {branch}", echo=True, warn=True)
        except Exception as error:
            print(error)
        c.run("git remote prune origin", echo=True, warn=True)
    print("the following branches are not fully merged:\n" + '\n'.join(not_fully_merged))


@task(name='process-meta-data')
def process_meta_data(c):
    docstring_regex = re.compile(r"(?P<description>.*?)(?P<args>args\:.*?(?=example\:)?)?(?P<example>example\:.*?)?(?P<extra_info>info\:.*)?$", re.IGNORECASE | re.DOTALL)
    file_path = pathmaker(THIS_FILE_DIR, 'antipetros_discordbot', 'init_userdata', 'data_pack', 'fixed_data', 'documentation', 'command_meta_data.json')
    data = loadjson(file_path)
    _new_dict = {}
    for command_name, command_attrs in data.items():
        new_attrs = {'docstring': None,
                     'example': None,
                     'long_description': None,
                     'brief': None,
                     'extra_info': None,
                     'description': None,
                     'short_doc': None} | command_attrs

        if new_attrs.get('docstring'):
            docstring = new_attrs.get('docstring')
            docstring_match = docstring_regex.search(docstring)
            if docstring_match:
                if not new_attrs.get('description') and docstring_match.group('description'):
                    new_attrs['description'] = '\n'.join(map(lambda x: x.strip(), [line for line in docstring_match.group('description').splitlines() if line != '']))

                if not new_attrs.get('example') and docstring_match.group('example'):
                    new_attrs['example'] = '\n'.join(map(lambda x: x.strip(), [line for line in docstring_match.group('example').splitlines() if line != '' and line.strip().casefold() != 'example:']))

                if not new_attrs.get('extra_info') and docstring_match.group('extra_info'):
                    new_attrs['extra_info'] = '\n'.join(map(lambda x: x.strip(), [line for line in docstring_match.group('extra_info').splitlines() if line != '' and line.strip().casefold() != 'info:']))

                if not new_attrs.get('short_doc') and docstring_match.group('description'):
                    new_attrs['short_doc'] = list(map(lambda x: x.strip(), [line for line in docstring_match.group('description').splitlines() if line != '']))[0]

                if not new_attrs.get('brief') and new_attrs.get('short_doc'):
                    brief = new_attrs.get("short_doc")
                    new_attrs['brief'] = shorten(brief, 30)

        _new_dict[command_name] = new_attrs
    writejson(_new_dict, file_path)
