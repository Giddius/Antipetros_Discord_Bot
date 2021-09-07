# * Standard Library Imports -->
# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import importlib.util
import pkgutil
SUB_SUPPORT_DIR = os.path.abspath(os.path.dirname(__file__))
if os.path.islink(SUB_SUPPORT_DIR) is True:

    SUB_SUPPORT_DIR = os.readlink(SUB_SUPPORT_DIR).replace('\\\\?\\', '')


def load_all_modules_from_dir(dirname):
    path_to_here = "antipetros_discordbot.bot_support.sub_support"
    for importer, package_name, _ in pkgutil.iter_modules([dirname]):
        if package_name != 'sub_support_helper':
            full_package_name = f"{path_to_here}.{package_name}"
            module = importlib.import_module(full_package_name)
            yield module


# def module_files():
#     for file in os.scandir(SUB_SUPPORT_DIR):
#         if file.is_file() and file.name != '__init__.py':
#             module_name = file.name.removesuffix('.py')
#             yield module_name, file.path


def _get_class_from_module(in_module):
    return in_module.get_class()


# def _import_sub_module(name, path):
#     spec = importlib.util.spec_from_file_location(name, path)
#     _module = importlib.util.module_from_spec(spec)
#     spec.loader.exec_module(_module)
#     return _get_class_from_module(_module)


def collect_sub_support_classes():
    class_list = []
    for module in load_all_modules_from_dir(SUB_SUPPORT_DIR):
        sub_support_class = _get_class_from_module(module)
        if sub_support_class not in class_list:
            class_list.append(sub_support_class)
    return class_list


SUB_SUPPORT_CLASSES = collect_sub_support_classes()
