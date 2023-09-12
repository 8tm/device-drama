import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from device_drama.classes.base_plugin import BasePlugin  # type: ignore
from device_drama.classes.config import Config  # type: ignore
from device_drama.classes.logger import Logger  # type: ignore
from device_drama.classes.plugin_validator import PluginStatus, PluginValidator  # type: ignore
from device_drama.misc import copy_files, get_formatted_text, remove_formatting, run_command  # type: ignore


logger = Logger(__name__)


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description='Device-Drama')

    argument_parser.add_argument(
        '-b', '--background', action='store_true', required=False, default=False,
        dest='background', help='Add background layout',
    )

    argument_parser.add_argument(
        '-c', '--color', action='store_true', required=False, default=False,
        dest='color', help='Use colored output',
    )

    argument_parser.add_argument(
        '-d', '--dir', type=str, default=str(Path(__file__).parent / 'plugins'),
        dest='plugins_dir', help='Set transcription file names',
    )

    argument_parser.add_argument(
        '-e', '--export', required=False, default=None, type=str,
        dest='plugins_export_dir', help='Export plugins to path',
    )

    argument_parser.add_argument(
        '-s', '--seed', type=int, default=None,
        dest='seed', help='Set seed integer value for color parameter',
    )

    return argument_parser


def get_plugins(plugins_path: str) -> Dict[str, Dict[str, BasePlugin]]:
    exclude_folders: Tuple[str, ...] = ('__pycache__',)
    logger.info(f'Adding plugins path "{plugins_path}" to system PATH')
    sys.path.append(plugins_path)
    plugins_directory = Path(plugins_path)
    all_plugins = {}

    subdirs = sorted(
        [subdir for subdir in plugins_directory.iterdir() if subdir.is_dir() and subdir.name not in exclude_folders]
    )

    for subdir_path in subdirs:
        plugins_files_in_subdir = sorted([file for file in subdir_path.iterdir() if file.suffix == '.py'])
        logger.info(f'Scaning folder "{subdir_path}"')
        plugins = {}
        for plugin_file in plugins_files_in_subdir:
            plugin_name = plugin_file.stem
            module_rel_path = plugin_file.relative_to(plugins_directory)
            module_import_path = '.'.join(module_rel_path.with_suffix('').parts)
            try:
                if module_import_path in sys.modules:
                    logger.warning(f'Reloading plugin "{module_import_path}"')
                    plugin_module = importlib.reload(sys.modules[module_import_path])
                else:
                    logger.info(f'Importing plugin "{module_import_path}"')
                    plugin_module = importlib.import_module(module_import_path)
            except ImportError as e:
                msg = f'Error importing module "{module_import_path}": {str(e)}. Skipping...'
                logger.error(msg)
                print(msg)
                continue

            plugin_class_name = 'DDPlugin'
            try:
                plugin_class = getattr(plugin_module, plugin_class_name)
                plugin_validator = PluginValidator(plugin_class)

                if not plugin_validator.validated():
                    continue

                plugin_instance = plugin_class()

                status = plugin_validator.check_compatibility(
                    plugin_instance.info.compatible_version,
                    Config.compatible_from_version,
                    Config.metadata['Version'],
                )

                if status == PluginStatus.COMPATIBLE:
                    plugins[plugin_name] = plugin_instance

            except AttributeError:
                logger.warning(f'Proper plugin class "{plugin_class_name}" not found in module "{plugin_name}".')

        all_plugins[subdir_path.name] = plugins

    return all_plugins


def generate_screen(plugin_modules: Dict[str, Dict[str, BasePlugin]]) -> List[str]:
    color = Config.colors[4]['color'] if os.geteuid() == 0 else Config.colors[3]['color']
    screen = []

    screen.append(
        get_formatted_text(text=' ', background=Config.colors[3]['background'], color=color, full_width=False)
        + get_formatted_text(
            text=f'Device-Drama v{Config.metadata["Version"]}        '
                 f'({Config.metadata["Home-page"]})',
            bold=True,
            center=False,
            short_length=2,
            background=Config.colors[3]['background'],
            color=color,
        )
        + get_formatted_text(text=' ', background=Config.colors[3]['background'], color=color, full_width=False)
    )
    screen.append(
        get_formatted_text(
            text=' ',
            bold=True,
            center=False,
            background=Config.colors[3]['background'],
            color=color,
        )
    )

    plugin_number = 1
    for folder_name, plugins_in_folder in plugin_modules.items():
        header = '        ' + ' '.join(folder_name.split('_')[1:]).title()
        screen.append(
            get_formatted_text(text=' ', background=Config.colors[3]['background'], color=color, full_width=False)
            + get_formatted_text(text=header, bold=True, center=False, short_length=2)
            + get_formatted_text(text=' ', background=Config.colors[3]['background'], color=color, full_width=False)
        )

        plugin_number += 1
        for valid_dataset_plugin, dd_plugin in plugins_in_folder.items():
            plugin_number += 1
            dd_plugin.args = {
                'plugins_dir': str(Config.arguments.plugins_dir),
                'color': str(Config.arguments.color),
                'background': str(Config.arguments.background),
            }

            output: List[Dict[str, str]] = dd_plugin.run()

            for line in output:
                if len(output) > 1:
                    plugin_number += 1
                formatted_line = f' {line["title"]}{line["text"]}'
                screen.append(
                    get_formatted_text(
                        text=' ', background=Config.colors[3]['background'], color=color, full_width=False,
                    )
                    + get_formatted_text(
                        text=formatted_line,
                        background=Config.colors[plugin_number % 2]['background'],
                        color=Config.colors[plugin_number % 2]['color'],
                        short_length=2,
                    )
                    + get_formatted_text(
                        text=' ', background=Config.colors[3]['background'], color=color, full_width=False,
                    )
                )

        screen.append(
            get_formatted_text(
                text='', bold=True, center=True, background=Config.colors[3]['background'], color=color,
            )
        )
    return screen


def export_plugins(source: str, destination: str) -> None:
    if not os.path.exists(source):
        msg = f'Source path {source} does not exist.'
        print(msg)
        logger.error(msg)
        return

    try:
        logger.info(f'Copying plugins from "{source}" to "{destination}"')
        copy_files(source, destination, exclude_folders=['__pycache__'])
        logger.info('Copying plugins finished')
    except PermissionError:
        msg = 'Permission error. Make sure you have the correct permissions to copy.'
        print(msg)
        logger.error(msg)
    except FileExistsError:
        msg = f'The destination folder {destination} already exists.'
        print(msg)
        logger.error(msg)
    except Exception as e:
        msg = f'An error occurred: {e}'
        print(msg)
        logger.error(msg)


def check_package_installed(package_name: str) -> bool:
    command_result = run_command(f'dpkg -l {package_name}')
    return command_result.return_code == 0


def main() -> None:
    logger.info('---------- STARTED  ----------')

    not_installed_packages = [pkg for pkg in Config.required_packages if not check_package_installed(pkg)]
    if len(not_installed_packages) > 0:
        print(
            '\n  Please install required packages using one of command:\n\n'
            f'      sudo apt install {" ".join(not_installed_packages)}\n'
            f'      sudo apt-get install {" ".join(not_installed_packages)}\n'
            f'      sudo aptitude install {" ".join(not_installed_packages)}\n'
        )
        sys.exit(1)

    Config.arguments = parser().parse_args()

    if Config.arguments.plugins_export_dir:
        logger.info(f'User requested to export plugins to "{Config.arguments.plugins_export_dir}"')
        if not Path(Config.arguments.plugins_export_dir).exists():
            logger.info('Creating not existing folder to export plugins')
            Path(Config.arguments.plugins_export_dir).mkdir(parents=True)

        logger.info('Exporting plugins')
        export_plugins(
            str(Path(__file__).parent / 'plugins'),
            str(Path(Config.arguments.plugins_export_dir)),
        )
        logger.info('Application finished after plugin export')
        sys.exit(0)

    logger.info(f'Searching for plugins in "{Config.arguments.plugins_dir}"')
    plugin_modules = get_plugins(Config.arguments.plugins_dir)

    lolcat_command = ['/usr/games/lolcat', '-p', '19.0', '-F', '1.5', '-t', '-f']
    if Config.arguments.seed:
        lolcat_command = [*lolcat_command, '-S', str(Config.arguments.seed)]

    screen = '\n'.join(generate_screen(plugin_modules))

    if not Config.arguments.color and not Config.arguments.background:
        print(' ' + remove_formatting(screen))
        print()
    elif not Config.arguments.color and Config.arguments.background:
        print(screen)
    elif Config.arguments.color and not Config.arguments.background:
        process = subprocess.Popen(lolcat_command, stdin=subprocess.PIPE)
        process.communicate(input=b' ' + remove_formatting(screen).encode())
        print('\n')
    elif Config.arguments.color and Config.arguments.background:
        process = subprocess.Popen(lolcat_command, stdin=subprocess.PIPE)
        process.communicate(input=screen.encode())
    else:
        logger.error('Unknown color/background setting selected...')
    logger.info('---------- FINISHED ----------')


if __name__ == '__main__':
    main()
