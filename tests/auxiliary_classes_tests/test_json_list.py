import pytest
import os
from antipetros_discordbot.auxiliary_classes.json_lists import JsonListImposter, JsonSyncedList
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, readit, writeit, pathmaker


def test_jsonimposter_file_creation(non_existing_json):
    assert os.path.exists(non_existing_json) is False
    x = JsonListImposter(non_existing_json)
    assert os.path.exists(non_existing_json) is True
    assert os.path.isfile(non_existing_json) is True
    assert x == []
    assert loadjson(non_existing_json) == []


def test_jsonimposter_file_changes(non_existing_json):
    x = JsonListImposter(non_existing_json)
    assert x == []
    writejson(['a', 'b', 'c'], non_existing_json)
    assert x == ['a', 'b', 'c']
    writejson([], non_existing_json)
    assert x == []


def test_jsonlistimposter_data_changes(non_existing_json):
    x = JsonListImposter(non_existing_json)
    assert x == []
    assert loadjson(non_existing_json) == []
    x.append('a')
    assert x == ['a']
    assert loadjson(non_existing_json) == ['a']
    x.append('b')
    assert loadjson(non_existing_json) == ['a', 'b']
    assert x == ['a', 'b']
    x.remove('a')
    assert loadjson(non_existing_json) == ['b']
    assert x == ['b']
    x += ['c', 'd', 'e']
    assert loadjson(non_existing_json) == ['b', 'c', 'd', 'e']
