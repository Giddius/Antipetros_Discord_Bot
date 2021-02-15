from invoke import task
import sys
import os
import toml
from pprint import pprint


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
    files_to_clear = []

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
