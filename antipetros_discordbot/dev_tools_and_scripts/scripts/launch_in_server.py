# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from time import sleep
from contextlib import contextmanager
from dotenv import find_dotenv, load_dotenv
# * Third Party Imports --------------------------------------------------------------------------------->
from paramiko import SSHClient, AutoAddPolicy
load_dotenv("nextcloud.env")
load_dotenv("token.env")
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_version():
    # * Local Imports --------------------------------------------------------------------------------------->
    from antipetros_discordbot import __version__
    return __version__


ANTIPETROS_START_CMD = f"nohup antipetrosbot run -t {os.getenv('DISCORD_TOKEN')} -nu {os.getenv('NX_USERNAME')} -np {os.getenv('NX_PASSWORD')} &"
ANTIPETROS_UPDATE_CMD = "python3.9 -m pip install --no-cache-dir --force-reinstall antipetros_discordbot"
ANTIPETROS_UPDATE_CMD_VERSION = ANTIPETROS_UPDATE_CMD + '==' + get_version()

USERNAME = 'root'
PWD = os.getenv('DEVANTISTASI_AUXILIARY_KEY')
channel_files_to_close = []


@contextmanager
def start_client():
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(hostname="192.248.189.227", username=USERNAME, password=PWD)
    yield client
    client.close()


def run_command(command: str):
    with start_client() as client:
        stdin, stdout, stderr = client.exec_command(command)
        if command != ANTIPETROS_START_CMD:
            print('##### STDOUT #####')
            print(stdout.read().decode())
            print('##### STDERR #####')
            print(stderr.read().decode())


if __name__ == '__main__':
    run_command("python3.9 -m pip install --upgrade pip")
    run_command(ANTIPETROS_UPDATE_CMD_VERSION)
    sleep(60)
    # run_command(ANTIPETROS_START_CMD)
