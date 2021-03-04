import pytest
import os
import sys
import shutil
from tempfile import TemporaryDirectory
from antipetros_discordbot.utility.gidtools_functions import pathmaker


@pytest.fixture
def non_existing_json():
    with TemporaryDirectory() as tempdir:
        json_path = pathmaker(tempdir, 'test_file.json')
        yield json_path
