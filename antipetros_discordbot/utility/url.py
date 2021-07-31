import yarl
from typing import Union


def make_url_absolute(base_url: Union[str, yarl.URL], relative_path: str):
    if isinstance(base_url, str):
        base_url = yarl.URL(base_url)
    return base_url.with_path(path=relative_path)


def fix_url(url: str):
    _url = yarl.URL(url)
    if _url.is_absolute() is False:
        _url = yarl.URL('//' + url)
        _url = _url.with_scheme('https')
    return _url
