# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from time import sleep
from contextlib import contextmanager
from dotenv import find_dotenv, load_dotenv
# * Third Party Imports --------------------------------------------------------------------------------->
from paramiko import SSHClient, AutoAddPolicy
from ftplib import FTP
import subprocess
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, readit, writeit
import json


def get_base_path():
    cmd = subprocess.run("git rev-parse --show-toplevel".split(), shell=True, check=True, capture_output=True, text=True)
    return cmd.stdout.strip()


MAIN_DIR = get_base_path()
load_dotenv(os.path.join(MAIN_DIR, 'antipetros_discordbot', "nextcloud.env"))
load_dotenv(os.path.join(MAIN_DIR, 'antipetros_discordbot', "token.env"))
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_version():
    # * Local Imports --------------------------------------------------------------------------------------->
    from antipetros_discordbot import __version__
    return __version__


ANTIPETROS_STOP_CMD = "antipetrosbot stop"
ANTIPETROS_START_CMD = f"nohup antipetrosbot run -t {os.getenv('DISCORD_TOKEN')} -nu {os.getenv('NEXTCLOUD_USERNAME')} -np {os.getenv('NEXTCLOUD_PASSWORD')} &"
ANTIPETROS_UPDATE_CMD = "python3.9 -m pip install --upgrade antipetros_discordbot"
ANTIPETROS_UPDATE_CMD_VERSION = ANTIPETROS_UPDATE_CMD + '==' + get_version()
ANTIPETROS_GET_PATH_CMD = "antipetrosbot get-path"
PID_GREP = 'ps -ef|grep "[a]ntipetros"'
PID_KILL_COMMAND = "kill $(ps aux | grep '[a]ntipetros' | awk '{print $2}')"

USERNAME = 'root'
PWD = os.getenv('DEVANTISTASI_AUXILIARY_KEY')
channel_files_to_close = []
install_script = "install_python_3_9_deadsnake.sh"
STATEMENT_MARKER = '#' * 15

JSON_TO_SYNC = [r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\antipetros_discordbot\init_userdata\data_pack\fixed_data\embed_data\embed_symbols.json"]


def print_statement(in_text: str):
    print(f"\n{STATEMENT_MARKER}\n{in_text}\n{STATEMENT_MARKER}\n")


@contextmanager
def start_client():
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(hostname="192.248.189.227", username=USERNAME, password=PWD)
    yield client
    client.close()


@contextmanager
def start_sftp(client):
    sftp = client.open_sftp()
    yield sftp
    sftp.close()


def copy_script():
    with start_client() as client:
        sftp = client.open_sftp()
        print(sftp.listdir())
        with open(install_script, 'r') as f:
            rf = sftp.file(install_script, 'w')
            rf.write(f.read())
            rf.close()
        sftp.close()
        stdin, stdout, stderr = client.exec_command(f"sh {install_script} 2>&1")
        while True:
            stdout_line = stdout.readline()
            if not stdout_line:
                break
            print(stdout_line, end="")


def get_file_location(client, file_name: str):
    stdin, stdout, stderr = client.exec_command(ANTIPETROS_GET_PATH_CMD + f' -f "{file_name}"' + ' 2>&1')
    output = stdout.read().decode('utf-8')
    return output.strip()


def update_json(local_content, remote_content):
    if isinstance(local_content, dict):
        return remote_content | local_content
    if isinstance(local_content, list):
        return list(set(remote_content + local_content))


def sync_json(file_path):
    with start_client() as client:
        file_name = os.path.basename(file_path)
        content_local = loadjson(file_path)
        server_file_location = get_file_location(client, file_name)
        with start_sftp(client) as sftp:
            remote_file = sftp.file(server_file_location, 'r')
            content_remote = json.loads(remote_file.read())
            remote_file.close()
            remote_file = sftp.file(server_file_location, 'w')
            json.dump(update_json(content_local, content_remote), remote_file)
            remote_file.close()


def run_command(command: str):
    with start_client() as client:
        stdin, stdout, stderr = client.exec_command(command + ' 2>&1')
        if command != ANTIPETROS_START_CMD:
            while True:
                stdout_line = stdout.readline()
                if not stdout_line:
                    break
                print(stdout_line, end="")


# if __name__ == '__main__':
#     # copy_script()
#     # run_command(ANTIPETROS_UPDATE_CMD_VERSION)
#     # sleep(10)

#     # run_command(f"antipetrosbot run -t {os.getenv('DISCORD_TOKEN')} -nu {os.getenv('NEXTCLOUD_USERNAME')} -np {os.getenv('NEXTCLOUD_PASSWORD')}")
#     # sleep(30)
#     # run_command('antipetrosbot stop')
def update_launch():
    print('*' * 30)
    print_statement("Waiting for 5 min before updating Antipetros from PyPi")
    to_go = 5
    for i in range(5):
        sleep(60)
        if i != 4:
            print_statement(f"{to_go - (i+1)} minutes to go")
    print_statement("finished waiting")
    print_statement("stoping bot via stop file")
    run_command(ANTIPETROS_STOP_CMD)
    print_statement("waiting 1 minutes to let the bot shut down completely")
    sleep(60)
    print_statement("updating bot from PyPi")
    run_command(ANTIPETROS_UPDATE_CMD_VERSION)
    sleep(15)
    print_statement('syncing json files')
    for json_file in JSON_TO_SYNC:
        print(f"syncing {os.path.basename(json_file)}")
        sync_json(json_file)
        sleep(5)
    print_statement("Waiting 30 seconds before launching bot")
    sleep(30)
    print_statement("Launching bot")
    run_command(ANTIPETROS_START_CMD)


def restart():
    run_command(ANTIPETROS_STOP_CMD)
    sleep(30)
    run_command(ANTIPETROS_START_CMD)


def launch():
    run_command(ANTIPETROS_START_CMD)


if __name__ == '__main__':
    launch()
    # restart()
