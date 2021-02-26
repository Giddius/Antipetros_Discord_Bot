# * Standard Library Imports -->
# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import Union
from functools import lru_cache

# * Third Party Imports --------------------------------------------------------------------------------->
from jinja2 import Template, Environment, FileSystemLoader, meta

TEMPLATES_DIR = os.path.abspath(os.path.dirname(__file__))
if os.path.islink(TEMPLATES_DIR) is True:

    TEMPLATES_DIR = os.readlink(TEMPLATES_DIR).replace('\\\\?\\', '').replace(os.pathsep, '/')


class TemplateItem():

    def __init__(self, name: str, template_object: Template, template_vars=None):
        self.name = name
        self._template_object = template_object
        self.vars = sorted(list(template_vars))

    @property
    def cleaned_vars(self):
        if self.vars is None:
            return None
        return self.vars

    def __call__(self, **kwargs):
        return self._template_object.render(**kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name=}, {self.vars=})"


class TemplateManager:

    def __init__(self):
        self.folder_path = TEMPLATES_DIR
        self.environment = Environment(loader=FileSystemLoader(self.folder_path, encoding='utf-8'))
        self.template_extension = '.jinja'
        self.casefold_template_names = True

    def set_casefolded_names(self, value: bool):
        self.casefold_template_names = value

    @property
    def available_template_files(self) -> list:
        _out = []
        for template_name in self.environment.list_templates(extensions=self.template_extension):
            _out.append(template_name)
        return _out

    def get_vars(self, template_name: str) -> dict:
        template_source = self.environment.loader.get_source(self.environment, template_name)[0]
        parsed_content = self.environment.parse(template_source)
        return meta.find_undeclared_variables(parsed_content)

    @lru_cache()
    def get_templates(self) -> dict:
        _all_templates = {}
        for template_name in self.available_template_files:
            mod_template_name = template_name
            if self.casefold_template_names is True:
                mod_template_name = template_name.casefold()
            _all_templates[mod_template_name] = TemplateItem(name=template_name, template_object=self.environment.get_template(template_name), template_vars=self.get_vars(template_name))
        return _all_templates

    def fetch_template(self, template_name) -> TemplateItem:

        all_templates = self.get_templates()

        if not template_name.endswith(self.template_extension):
            template_name = template_name + self.template_extension
        if self.casefold_template_names is True:
            template_name = template_name.casefold()
        if template_name not in all_templates:
            raise KeyError(f'unknown template name "{template_name=}"')
        return all_templates.get(template_name)

    def __contains__(self, item):
        if self.casefold_template_names is True:
            item = item.casefold()
        return item in self.get_templates()


TEMPLATE_MANAGER = TemplateManager()
