import subprocess
from antipetros_discordbot.utility.gidtools_functions import pathmaker
import os

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

VENV_ACTIVATOR_PATH = pathmaker(THIS_FILE_DIR, '../../.venv/Scripts/activate.bat', rev=True)


SUBPROCESS_COMMAND = [VENV_ACTIVATOR_PATH, '&&', 'antipetrosbot', 'info']


cmd = subprocess.run(SUBPROCESS_COMMAND, check=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, text=True, shell=False)
print(cmd.stdout)
