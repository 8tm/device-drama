import argparse
import importlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from device_drama.classes.base_plugin import BasePlugin


class CommandResult:
    def __init__(self, output, return_code, error_msg):
        self.output = output
        self.return_code = return_code
        self.error_msg = error_msg


class CommandExecutor:
    @staticmethod
    def run_command(command):
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
            return CommandResult(result.stdout.strip(), result.returncode, result.stderr.strip())
        except Exception as e:
            return CommandResult("", -1, str(e))


class Config:
    arguments: argparse.Namespace
    # disabled_plugins: str = ''
    # main_hardware_plugins_dir_path: Path = Path('main_hardware')
    # operating_system_plugins_dir_path: Path = Path('operating_system')
    # activate_plugins: List[str] = []


class DDPlugin(BasePlugin):
    def run(self) -> List[Dict[str, str]]:
        return [
            {
                "title": "DDPlugin",
                "text": "BASE DDPlugin",
            }
        ]


def get_plugins(plugins_path: str, command_executor) -> Dict[str, Dict[str, DDPlugin]]:
    excluded_folders: Tuple[str, ...] = ('__pycache__',)
    plugins_directory = Path(plugins_path)

    all_plugins = {}
    sys.path.append(plugins_directory.as_posix())

    subdirs = sorted(
        [subdir for subdir in plugins_directory.iterdir() if subdir.is_dir() and subdir.name not in excluded_folders]
    )

    for subdir_path in subdirs:
        plugins_files_in_subdir = sorted([file for file in subdir_path.iterdir() if file.suffix == '.py'])

        plugins = {}
        for plugin_file in plugins_files_in_subdir:
            plugin_name = plugin_file.stem
            module_rel_path = plugin_file.relative_to(plugins_directory)
            module_import_path = '.'.join(module_rel_path.with_suffix('').parts)
            try:
                if module_import_path in sys.modules:
                    plugin_module = importlib.reload(sys.modules[module_import_path])
                else:
                    plugin_module = importlib.import_module(module_import_path)
            except ImportError as e:
                print(f"Error importing module '{module_import_path}': {str(e)}. Skipping...")
                continue

            plugin_class_name = 'DDPlugin'
            try:
                plugin_class = getattr(plugin_module, plugin_class_name)
                plugin_instance = plugin_class()
                plugin_instance.set_command_executor(command_executor)
                plugins[plugin_name] = plugin_instance
            except AttributeError:
                print(f"Plugin class '{plugin_class_name}' not found in module '{plugin_name}'. Skipping...")

        all_plugins[subdir_path.name] = plugins

    return all_plugins


def present_plugin_output(dd_plugin: DDPlugin) -> None:
    # _status_ok = f'{Fore.GREEN}{Style.BRIGHT} OK {Style.RESET_ALL}'
    # _status_fail = f'{Fore.RED}{Style.BRIGHT}FAIL{Style.RESET_ALL}'
    # colored_id = f'{Fore.LIGHTRED_EX}{Style.BRIGHT}{dd_plugin.info.id}{Style.RESET_ALL}'

    _status_ok = f' OK '
    _status_fail = f'FAIL'
    colored_id = f'{dd_plugin.info.id}'

    #if len(dd_plugin.errors) == 0 and Config.arguments.verbose:
    #    line = f'{colored_id}: [{_status_ok}] {dd_plugin.success_message}\n'

        #if Config.arguments.output:
        #    add_text_to_file(Config.arguments.output, line)

    #    print(line)

    #if len(dd_plugin.errors) > 0:
        # bright_error_message = f'{Fore.WHITE}{Style.NORMAL}{dd_plugin.error_message}{Style.RESET_ALL}'
    #    bright_error_message = f'{dd_plugin.error_message}'
    #    line = f'{colored_id}: [{_status_fail}] {bright_error_message.format(nof=str(len(dd_plugin.errors)))}\n'

        #if Config.arguments.output:
        #    add_text_to_file(Config.arguments.output, line)

    #    print(line)

    #    for error in dd_plugin.errors:

            #if Config.arguments.output:
            #    add_text_to_file(Config.arguments.output, colorizer.colorize(error))

            # print(colorizer.colorize(error))
    #        print(error)
    #    print()


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description='Device-Drama')

    argument_parser.add_argument(
        '-c', '--color', action='store_true', required=False, default=False,
        dest='args_use_color', help='Use additional colors',
    )

    argument_parser.add_argument(
        '-s', '--sudo', action='store_true', required=False, default=False,
        dest='args_use_sudo', help='Print information which required root permissions',
    )

    argument_parser.add_argument(
        '--plugins_dir', type=str, default=str(Path(__file__).parent / 'plugins'),
        dest='args_plugins_dir', help='Set transcription file names',
    )

    return argument_parser


def get_formated_text(
        text, background: int = 47, color: int = 30, bold: bool = False, center: bool = False, full_width: bool = True,
        short_length: int = 0,
):
    columns = len(text)
    if full_width:
        columns = shutil.get_terminal_size().columns - short_length

    _bold = ''
    if bold:
        _bold = 1

    if center:
        text = text.center(columns)
    else:
        text = text.ljust(columns)

    return f"\033[{_bold};{color};{background}m{text}\033[m"


def generate_screen(plugin_modules, colors) -> List[str]:
    color = colors[4]['color'] if Config.arguments.args_use_sudo else colors[3]['color']
    screen = []

    screen.append(
        get_formated_text(
            text='Device-Drama v23.8.24',
            bold=True,
            center=True,
            background=colors[3]['background'],
            color=color,
        )
    )
    screen.append(
        get_formated_text(
            text=' ',
            bold=True,
            center=True,
            background=colors[3]['background'],
            color=color,
        )
    )

    plugin_number = 1
    for folder_name, plugins_in_folder in plugin_modules.items():
        header = ' '.join(folder_name.split('_')[1:]).title()
        screen.append(
            get_formated_text(text=' ', background=colors[3]['background'], color=color, full_width=False) +
            get_formated_text(text=header, bold=True, center=True, short_length=2) +
            get_formated_text(text=' ', background=colors[3]['background'], color=color, full_width=False)
        )

        plugin_number += 1
        for valid_dataset_plugin, dd_plugin in plugins_in_folder.items():
            plugin_number += 1
            dd_plugin.args = {
                'use_sudo': str(Config.arguments.args_use_sudo),
                'plugins_dir': str(Config.arguments.args_plugins_dir),
            }

            output: List[Dict[str, str]] = dd_plugin.run()

            for line in output:
                if len(output) > 1:
                    plugin_number += 1
                # print(f'{line["title"]}{line["text"]} [{dd_plugin.info.name}]')
                line = f' {line["title"]}{line["text"]} [{dd_plugin.info.name}]'
                screen.append(
                    get_formated_text(
                        text=' ', background=colors[3]['background'], color=color, full_width=False,
                    ) +
                    get_formated_text(
                        text=line,
                        background=colors[plugin_number % 2]['background'],
                        color=colors[plugin_number % 2]['color'],
                        short_length=2,
                    ) +
                    get_formated_text(
                        text=' ', background=colors[3]['background'], color=color, full_width=False,
                    )
                )

                # get_formated_text(text=f' MoBo: {mobo["company"]} {mobo["name"]}', background=53, color=40))
                # get_formated_text(text=f'  CPU: {self.cpu_info["info"]}', background=53, color=100))
        # print(
        #     get_formated_text(
        #         text='',
        #         background=colors[2]['background'],
        #         color=colors[2]['color']
        #     )
        # )
        screen.append(
            get_formated_text(
                text='', bold=True, center=True, background=colors[3]['background'], color=color,
            )
        )
    # print(get_formated_text(text='', bold=True, center=True, background=241, color=44))
    return screen
"""
device-drama        | lolcat -p 100 -F 0.73 -t -f -S 53
device-drama --sudo | lolcat -p 100 -F 0.73 -t -f -S 53

device-drama        | lolcat -p 19.0 -F 1.5 -S 70 -t -f

"""


def main():
    Config.arguments = parser().parse_args()
    path_to_plugins = Config.arguments.args_plugins_dir
    command_executor = CommandExecutor()
    plugin_modules = get_plugins(path_to_plugins, command_executor)
    colors = [
        {'background': 53, 'color': 40},
        {'background': 53, 'color': 100},
        {'background': 53, 'color': 39},
        {'background': 250, 'color': 44},
        {'background': 250, 'color': 41},
    ]

    screen = '\n'.join(generate_screen(plugin_modules, colors))

    if Config.arguments.args_use_color:
        process = subprocess.Popen(['lolcat', '-p', '19.0', '-F', '1.5', '-S', '70', '-t', '-f'], stdin=subprocess.PIPE)
        process.communicate(input=screen.encode())
    else:
        print(screen)

    # print(screen)


if __name__ == "__main__":
    main()
