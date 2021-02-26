# * Third Party Imports -->
# * Third Party Imports --------------------------------------------------------------------------------->
import pytest

# * Local Imports --------------------------------------------------------------------------------------->
# * Local Imports -->
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import Bold, Cursive, LineCode, CodeBlock, BlockQuote, UnderScore

def test_simple_bold():
    bold_text = Bold('test')
    assert str(bold_text) == '**test**'


def test_simple_underscore():
    underscore_text = UnderScore('test')
    assert str(underscore_text) == '__test__'


def test_simple_cursive():
    cursive_text = Cursive('test')
    assert str(cursive_text) == '*test*'


def test_simple_linecode():
    linecode_text = LineCode('test')
    assert str(linecode_text) == '`test`'


def test_simple_codeblock():
    codeblock_nolanguage_test = CodeBlock('test')
    assert str(codeblock_nolanguage_test) == '```\ntest\n```'
    codeblock_python_test = CodeBlock('test', 'python')
    assert str(codeblock_python_test) == '```python\ntest\n```'


def test_blockquote():
    blockquote_text = BlockQuote('test')
    assert str(blockquote_text) == '> test'
    multiline_string = """Test
test1
test2"""
    multiline_blockquote = BlockQuote(multiline_string)
    assert str(multiline_blockquote) == '> Test\n> test1\n> test2\n'


def test_combinations():
    underscore_bold_text = UnderScore(Bold('test'))
    assert str(underscore_bold_text) == '__**test**__'
