import os


def get_nextcloud_options():
    # _options = {"recv_speed": 50 * (1024**2)}
    _options = {}

    if os.getenv('NEXTCLOUD_USERNAME') is not None:
        _options['hostname'] = f"https://antistasi.de/dev_drive/remote.php/dav/files/{os.getenv('NEXTCLOUD_USERNAME')}/"
        _options['login'] = os.getenv('NEXTCLOUD_USERNAME')
        _options["timeout"] = 300
    else:
        if os.getenv('INFO_RUN') != "1":
            raise RuntimeError('no nextcloud Username set')
    if os.getenv('NEXTCLOUD_PASSWORD') is not None:
        _options['password'] = os.getenv('NEXTCLOUD_PASSWORD')
    else:
        if os.getenv('INFO_RUN') != "1":
            raise RuntimeError('no nextcloud Password set')
    return _options
