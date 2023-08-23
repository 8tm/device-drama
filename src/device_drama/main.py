import argparse
# import importlib.util
import importlib
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
    disabled_plugins: str = ''
    main_hardware_plugins_dir_path: Path = Path('main_hardware')
    operating_system_plugins_dir_path: Path = Path('operating_system')
    activate_plugins: List[str] = []


class DDPlugin(BasePlugin):
    def run(self) -> Dict[str, str]:
        return {
            "title": "DDPlugin",
            "text": "BASE DDPlugin"
        }


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
    argument_parser = argparse.ArgumentParser(description='Validate audio and text files.')

    argument_parser.add_argument(
        '-s', '--sudo', action='store_true', required=False, default=False,
        help='Print information which required root permissions',
    )

    argument_parser.add_argument(
        '--args.plugins_dir', type=str, default=str(Path(__file__).parent / 'plugins'),
        dest='args_plugins_dir', help='Set transcription file names',
    )


    # ARGS menu:
    argument_parser.add_argument(
        '--args.files', type=str, default='list_train.txt,list_val.txt',
        dest='args_files', help='Set transcription file names',
    )
    argument_parser.add_argument(
        '--args.dir-name', type=str, action='store', required=False, default='wavs',
        dest='args_dir_name', help='Name of foldr with wav files',
    )
    argument_parser.add_argument(
        '--args.path', type=str, action='store', required=False, default='',
        dest='args_path', help='Path to dataset',
    )
    argument_parser.add_argument(
        '--args.sample-rate', type=int, action='store', required=False, default=22050,
        dest='args_sample_rate', help='Set sample rate',
    )
    argument_parser.add_argument(
        '--args.number-of-channels', type=int, action='store', required=False, default=1,
        dest='args_number_of_channels', help='Set number of channels',
    )
    argument_parser.add_argument(
        '--args.min-duration', type=int, action='store', required=False, default=2000,
        dest='args_min_duration', help='Set minimum duration in miliseconds (1 second = 1000 milisecond)',
    )
    argument_parser.add_argument(
        '--args.max-duration', type=int, action='store', required=False, default=10000,
        dest='args_max_duration', help='Set maximum duration in miliseconds (1 second = 1000 milisecond)',
    )
    argument_parser.add_argument(
        '--args.number-of-pipes', type=int, action='store', required=False, default=1,
        dest='args_number_of_pipes', help='Set number of pipes in transcripton files',
    )

    # PLUGINS menu:
    argument_parser.add_argument(
        '--plugins.disable', type=str, action='store', required=False, default='',
        dest='plugins_disable', help='Disable plugins',
    )

    argument_parser.add_argument(
        '--plugins.list', action='store_true',
        dest='plugins_list', help='List plugins',
    )

    # MAIN menu:
    argument_parser.add_argument(
        '-o', '--output', type=Path, action='store', required=False, default=None,
        help='Save output to file',
    )

    argument_parser.add_argument(
        '-v', '--verbose', action='store_true', required=False, default=False,
        help='Print additional information',
    )
    return argument_parser


def main():
    Config.arguments = parser().parse_args()
    path_to_plugins = Config.arguments.args_plugins_dir
    command_executor = CommandExecutor()
    plugin_modules = get_plugins(path_to_plugins, command_executor)

    for folder_name, plugins_in_folder in plugin_modules.items():
        # Dodać formatowanie nagłówna
        print(' '.join(folder_name.split('_')[1:]).title())

        for valid_dataset_plugin, dd_plugin in plugins_in_folder.items():
            dd_plugin.args = {
                'path': str(Config.arguments.args_path),
                'files': list(path for path in str(Config.arguments.args_files).split(',')),
                'dir_name': str(Config.arguments.args_dir_name),
                'expected_properties': {
                    'sample_rate': Config.arguments.args_sample_rate,
                    'number_of_channels': Config.arguments.args_number_of_channels,
                    'min_duration': Config.arguments.args_min_duration,
                    'max_duration': Config.arguments.args_max_duration,
                    'number_of_pipes': Config.arguments.args_number_of_pipes,
                },
            }

            output = dd_plugin.run()
            # Wymyślić jak printować zawartość ze zmiennych bo dla dysków będą inne (kolumny)
            print(f'{output["title"]}: {output["text"]} [{dd_plugin.info.name}]')
        print()

        # present_plugin_output(dd_plugin, colorizer)
        # present_plugin_output(dd_plugin)

    # system_info = SystemInfo(arguments.sudo)
    # print(system_info.display_all())


if __name__ == "__main__":
    main()
