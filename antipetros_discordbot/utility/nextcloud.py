import os


def get_nextcloud_options():
    _options = {"recv_speed": 20 * (1024**2)}
    print(50 * (1024**2))
    if os.getenv('NEXTCLOUD_USERNAME') is not None:
        _options['webdav_hostname'] = f"https://antistasi.de/dev_drive/remote.php/dav/files/{os.getenv('NEXTCLOUD_USERNAME')}/"
        _options['webdav_login'] = os.getenv('NEXTCLOUD_USERNAME')
        _options["webdav_timeout"] = 60
    else:
        raise RuntimeError('no nextcloud Username set')
    if os.getenv('NEXTCLOUD_PASSWORD') is not None:
        _options['webdav_password'] = os.getenv('NEXTCLOUD_PASSWORD')
    else:
        raise RuntimeError('no nextcloud Password set')
    return _options


NEXTCLOUD_OPTIONS = get_nextcloud_options()
