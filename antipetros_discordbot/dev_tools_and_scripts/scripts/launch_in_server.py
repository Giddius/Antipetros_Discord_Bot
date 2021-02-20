# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from time import sleep
from contextlib import contextmanager
from dotenv import find_dotenv, load_dotenv
# * Third Party Imports --------------------------------------------------------------------------------->
from paramiko import SSHClient, AutoAddPolicy
from ftplib import FTP
load_dotenv("nextcloud.env")
load_dotenv("token.env")
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_version():
    # * Local Imports --------------------------------------------------------------------------------------->
    from antipetros_discordbot import __version__
    return __version__


ANTIPETROS_START_CMD = f"nohup antipetrosbot run -t {os.getenv('DISCORD_TOKEN')} -nu {os.getenv('NX_USERNAME')} -np {os.getenv('NX_PASSWORD')} &"
ANTIPETROS_UPDATE_CMD = "python3.9 -m pip install --force-reinstall antipetros_discordbot"
ANTIPETROS_UPDATE_CMD_VERSION = ANTIPETROS_UPDATE_CMD + '==' + get_version()

USERNAME = 'root'
PWD = os.getenv('DEVANTISTASI_AUXILIARY_KEY')
channel_files_to_close = []
install_script = "install_python_3_9_deadsnake.sh"


@contextmanager
def start_client():
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(hostname="192.248.189.227", username=USERNAME, password=PWD)
    yield client
    client.close()


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


def run_command(command: str):
    with start_client() as client:
        stdin, stdout, stderr = client.exec_command(command + ' 2>&1')
        if command != ANTIPETROS_START_CMD:
            while True:
                stdout_line = stdout.readline()
                if not stdout_line:
                    break
                print(stdout_line, end="")


if __name__ == '__main__':
    copy_script()
    run_command("python3.9 -m pip install --upgrade pip")
    run_command(ANTIPETROS_UPDATE_CMD_VERSION)
    sleep(10)
    run_command(f"antipetrosbot run -t {os.getenv('DISCORD_TOKEN')} -nu {os.getenv('NX_USERNAME')} -np {os.getenv('NX_PASSWORD')}")
    run_command(ANTIPETROS_START_CMD)
