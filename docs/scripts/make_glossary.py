from jinja2 import Environment, FileSystemLoader
from antipetros_discordbot.utility.gidtools_functions import pathmaker, writejson, loadjson, writeit, readit, get_pickled, pickleit
import os
from pprint import pprint, pformat
from spellchecker import SpellChecker
import re
from string import punctuation
from stdlib_list import stdlib_list
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from language_tool_python import LanguageTool
import language_tool_python


# INFO glossary macros:
# ?                     - basic
# ?                     - dropdown
# ?                     - seperated_dropdown


SEPERATOR = '==='
MAIN_DIR = os.getenv('WORKSPACEDIR')
DOCS_DIR = pathmaker(MAIN_DIR, 'docs')
TEMPLATE_DIR = pathmaker(DOCS_DIR, r'resources\templates')

TEMPLATE_NAME = 'glossary_template.md.jinja'

IN_PUT_FILE = pathmaker(DOCS_DIR, r'resources\raw_text\raw_glossary_items.txt')

OUT_PUT_FILE = pathmaker(MAIN_DIR, 'glossary.md')

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

split_regex = re.compile(r"[\s\,\.\:\+\-\_\!\?\=]")

spell = SpellChecker(case_sensitive=False)
extra_words = ['executor', 'execution', 'executing', 'astupido', 'asynchronous', 'asyncio', 'async', 'def', 'plug-in', 'vs']
spell.word_frequency.load_words(extra_words)

better_punctuation = list(punctuation) + ['```', '``', '']


tool = LanguageTool('en-US')
tool.disable_spellchecking()


def misc_fixes(glossary_terms: dict):
    for key, value in glossary_terms.items():
        glossary_terms[key] = value[0].upper() + value[1:]

    return glossary_terms


def correct_grammar(in_text: str):
    matches = tool.check(in_text)
    my_mistakes = []
    my_corrections = []
    start_positions = []
    end_positions = []

    for rules in matches:
        if len(rules.replacements) > 0:
            start_positions.append(rules.offset)
            end_positions.append(rules.errorLength + rules.offset)
            my_mistakes.append(in_text[rules.offset:rules.errorLength + rules.offset])
            my_corrections.append(rules.replacements[0])

    my_new_text = list(in_text)

    for m in range(len(start_positions)):
        for i in range(len(in_text)):
            my_new_text[start_positions[m]] = my_corrections[m]
            if (i > start_positions[m] and i < end_positions[m]):
                my_new_text[i] = ""

    return "".join(my_new_text).replace('“', '``')


def correct_word(word: str):
    correction = spell.correction(word)
    # if word == 'asyncio':
    #     print(f"{word=}         |           {correction=}")
    if correction == 'i':
        return word, word
    return word, correction


def replace_many_to_none(in_string: str, in_replace: list):
    for replacement in in_replace:
        in_string = in_string.replace(replacement, '')

    return in_string


def grammar_check_values(glossary_terms: dict):
    for key, value in glossary_terms.items():
        glossary_terms[key] = correct_grammar(value)
    return glossary_terms


def spellcheck_values(glossary_terms: dict):

    for key, value in glossary_terms.items():

        results = map(correct_word, [replace_many_to_none(word, better_punctuation) for word in split_regex.split(value) if word not in better_punctuation])
        for orig, correct in results:
            value = value.replace(orig, correct)
        glossary_terms[key] = value
    return glossary_terms


def clean_values(glossary_terms: dict):
    for key, value in glossary_terms.items():
        glossary_terms[key] = '\n'.join([line for line in value]).strip('\n')
    return glossary_terms


def parse_raw_data():
    content = readit(IN_PUT_FILE)
    glossary_terms = {}
    current_term = None
    current_value_buffer = []
    for line in content.splitlines():
        if SEPERATOR in line:
            term, value = map(lambda x: x.strip(), line.split(SEPERATOR))
            if current_term is None:
                current_term = term
                current_value_buffer.append(value)
            else:
                glossary_terms[current_term] = current_value_buffer
                current_term = term
                current_value_buffer = [value]
        else:
            current_value_buffer.append(line)
    glossary_terms[current_term] = current_value_buffer
    glossary_terms = clean_values(glossary_terms)
    glossary_terms = spellcheck_values(glossary_terms)
    glossary_terms = grammar_check_values(glossary_terms)
    glossary_terms = misc_fixes(glossary_terms)
    return glossary_terms


def create_glossary_string(macro_name: str, key_formats: list, value_formats: list):
    template = env.get_template(TEMPLATE_NAME)
    return template.render(glossary_terms=parse_raw_data(), dynamic_macro_name=macro_name, key_formats=key_formats, value_formats=value_formats)


def write_glossary(macro_name='basic', key_formats=[], value_formats=[]):
    writeit(OUT_PUT_FILE, create_glossary_string(macro_name, key_formats, value_formats))


if __name__ == '__main__':
    write_glossary(macro_name='dropdown', key_formats=['b', 'u'], value_formats=[])
