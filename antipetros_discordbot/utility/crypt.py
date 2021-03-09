"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os

# * Third Party Imports --------------------------------------------------------------------------------->
from cryptography.fernet import Fernet, InvalidToken

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import readit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper

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
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


def write_key(file_path):
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open(file_path, "wb") as key_file:
        key_file.write(key)


def load_key(file_path):
    """
    Loads the key from the current directory named `key.key`
    """
    with open(file_path, 'rb') as key_file:
        return key_file.read()


def encrypt_string(in_data: str, key=None, key_file=None):

    if key is None:
        if key_file is not None:
            if os.path.exists(key_file):
                key = load_key(key_file)
            else:
                write_key(key_file)
                key = load_key(key_file)
        else:
            raise RuntimeError
    fernet_crypt = Fernet(key)
    string_data = in_data.encode()
    return fernet_crypt.encrypt(string_data)


def decrypt_string(in_data: bytes, key=None, key_file=None):

    if key is None:
        if key_file is not None:
            if os.path.exists(key_file):
                key = load_key(key_file)

    if key is None:
        raise RuntimeError

    fernet_crypt = Fernet(key)
    return fernet_crypt.decrypt(in_data).decode()


def encrypt_file(file_path, key):
    fernet_crypt = Fernet(key)
    with open(file_path, 'rb') as in_f:
        file_data = in_f.read()
    encrypt_file_data = fernet_crypt.encrypt(file_data)
    with open(file_path, 'wb') as out_f:
        out_f.write(encrypt_file_data)


def decrypt_file(file_path, key):
    fernet_crypt = Fernet(key)
    with open(file_path, 'rb') as in_f:
        file_data = in_f.read()
    decrypt_file_data = fernet_crypt.decrypt(file_data)
    with open(file_path, 'wb') as out_f:
        out_f.write(decrypt_file_data)


def new_db_key(token_file):
    new_key = Fernet.generate_key()
    token_content = readit(token_file)
    with open(token_file, 'w') as f:
        for line in token_content.splitlines():
            if line.split('=', maxsplit=1)[0] == 'DB_KEY':
                line = f"DB_KEY={new_key.decode()}"
            f.write(line + '\n')


def encrypt_db(key):
    for file in os.scandir(APPDATA['database']):
        if file.is_file() and file.name.endswith('.db'):
            encrypt_file(file.path, key=key)


def decrypt_db(key):

    for file in os.scandir(APPDATA['database']):
        if file.is_file() and file.name.endswith('.db'):
            try:
                decrypt_file(file, key=key)
            except InvalidToken as inval_token_error:
                log.error('InvalidToken encountered while decrypting DB, DB is probably not encrypted')


# region[Main_Exec]
if __name__ == '__main__':
    pass


# endregion[Main_Exec]