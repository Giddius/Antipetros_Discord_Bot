from invoke import task
import sys
import os
import toml
from pprint import pprint
from time import sleep
import json
from PIL import Image, ImageFilter, ImageOps


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


def writejson(in_object, in_file, sort_keys=True, indent=4):
    with open(in_file, 'w') as jsonoutfile:
        print(f"writing json '{in_file}'")
        json.dump(in_object, jsonoutfile, sort_keys=sort_keys, indent=indent)


THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

VENV_ACTIVATOR_PATH = pathmaker(THIS_FILE_DIR, '.venv/Scripts/activate.bat', rev=True)

PYPROJECT_TOML_DATA = toml.load(pathmaker(THIS_FILE_DIR, 'pyproject.toml'))


def flit_data(to_get: str):
    data = PYPROJECT_TOML_DATA
    path_keys = ['tool', 'flit']

    if to_get == 'first_script':
        path_keys += ['scripts']
    elif to_get == 'project_name':
        path_keys += ['metadata']
    elif to_get == 'author_name':
        path_keys += ['metadata']

    for key in path_keys:
        data = data.get(key, {})

    if to_get == 'first_script':
        return list(data)[0]

    if to_get == 'project_name':
        return data.get('module')
    if to_get == 'author_name':
        return data.get('author')


ANTIPETROS_CLI_COMMAND = flit_data('first_script')


COLLECT_COMMAND = 'collect-data'

PROJECT_NAME = flit_data('project_name')

PROJECT_AUTHOR = flit_data('author_name')


def activator_run(c, command):
    with c.prefix(VENV_ACTIVATOR_PATH):
        c.run(command, echo=True)


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


@task(help={'output_file': 'alternative output file, defaults to /docs/resources/data'})
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
    files_to_clear = ["blacklist.json", "give_aways.json", "registered_steam_workshop_items.json"]

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
def increment_version(c, increment_part='minor'):
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
    cleaned_version_line = version_line.replace('__version__', '').replace('=', '').replace('"', '').replace("'", "").strip()
    major, minor, patch = cleaned_version_line.split('.')

    if increment_part == 'patch':
        patch = str(int(patch) + 1)
    elif increment_part == 'minor':
        minor = str(int(minor) + 1)
        patch = str(0)
    elif increment_part == 'major':
        major = str(int(major) + 1)
        minor = str(0)
        patch = str(0)
    with open(init_file, 'w') as f:
        f.write(content.replace(version_line, f"__version__ = '{major}.{minor}.{patch}'"))


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
