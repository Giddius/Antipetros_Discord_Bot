import platform
from rich import inspect as rinspect
from rich.console import Console as RichConsole
from typing import Union, Optional, Callable, Iterable, TYPE_CHECKING
from rich.rule import Rule


RICH_POSSIBLE_KWARGS = {"color_system",
                        "force_terminal",
                        "force_jupyter",
                        "force_interactive",
                        "soft_wrap",
                        "theme",
                        "stderr",
                        "file",
                        "quiet",
                        "width",
                        "height",
                        "style",
                        "no_color",
                        "tab_size",
                        "markup",
                        "emoji",
                        "highlight",
                        "log_time",
                        "log_path",
                        "log_time_format",
                        "highlighter",
                        "legacy_windows",
                        "safe_box",
                        "get_datetime",
                        "get_time",
                        "_environ"}

RINSPECT_POSSIBLE_KWARGS = {"title",
                            "help",
                            "methods",
                            "docs",
                            "private",
                            "dunder",
                            "sort",
                            "all",
                            "value"}

RICH_CONSOLE_STD_KWARGS = {'soft_wrap': True}

RINSPECT_STD_KWARGS = {'methods': True}


def show_toast(title: str, msg: str, duration: int = 5):
    if platform.system().casefold() != 'windows':
        print(title, msg, str(duration))
        return
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    toaster.show_toast(title=title, msg=msg, duration=duration)


def rinspect_object(in_object, output_file: str = None, **kwargs):
    def _apply_possible_console_kwargs(in_console_kwargs):
        found_kwargs = {}
        for key, value in kwargs.items():
            if key in RICH_POSSIBLE_KWARGS:
                found_kwargs[key] = value
        return in_console_kwargs | found_kwargs

    def _apply_possible_rinspect_kwargs(in_rinspect_kwargs):
        found_kwargs = {}
        for key, value in kwargs.items():
            if key in RINSPECT_POSSIBLE_KWARGS:
                found_kwargs[key] = value
        return in_rinspect_kwargs | found_kwargs

    console_kwargs = _apply_possible_console_kwargs(RICH_CONSOLE_STD_KWARGS.copy())
    rinspect_kwargs = _apply_possible_rinspect_kwargs(RINSPECT_STD_KWARGS.copy())
    if output_file is not None:
        console_kwargs['record'] = True

    temp_console = RichConsole(**console_kwargs)

    rinspect(in_object, console=temp_console, **rinspect_kwargs)

    if output_file is not None:
        save_method = "export_html" if output_file.split('.')[-1].casefold() == 'html' else "export_text"
        with open(output_file, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(getattr(temp_console, save_method)())
    temp_console.clear()


def console_print(to_print, output_file: str = None, header_rule: Union[str, bool] = False, **kwargs):
    def _apply_possible_console_kwargs(in_console_kwargs):
        found_kwargs = {}
        for key, value in kwargs.items():
            if key in RICH_POSSIBLE_KWARGS:
                found_kwargs[key] = value
        return in_console_kwargs | found_kwargs

    console_kwargs = _apply_possible_console_kwargs(RICH_CONSOLE_STD_KWARGS.copy())
    if output_file is not None:
        console_kwargs['record'] = True

    temp_console = RichConsole(**console_kwargs)
    if header_rule is not False:
        header_title = header_rule.title() if isinstance(header_rule, str) else None
        rule = Rule(header_title)
        temp_console.print(rule)
    temp_console.print(to_print)

    if output_file is not None:
        save_method = "export_html" if output_file.split('.')[-1].casefold() == 'html' else "export_text"
        with open(output_file, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(getattr(temp_console, save_method)())
    temp_console.clear()
