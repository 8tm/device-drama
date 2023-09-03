import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


from device_drama.classes.base_plugin import BasePlugin, PluginStatus, CompatibilityException
from device_drama.classes.config import Config
from device_drama.misc import copy_files, get_formated_text, remove_formatting


def get_plugins(plugins_path: str) -> Dict[str, Dict[str, BasePlugin]]:
    exclude_folders: Tuple[str, ...] = ('__pycache__',)
    sys.path.append(plugins_path)
    plugins_directory = Path(plugins_path)
    all_plugins = {}

    subdirs = sorted(
        [subdir for subdir in plugins_directory.iterdir() if subdir.is_dir() and subdir.name not in exclude_folders]
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

                try:
                    status = plugin_instance.check_compatibility(
                        plugin_instance.info.compatible_version, '23.1.1', Config.metadata['Version'],
                    )
                    if status == PluginStatus.COMPATIBLE:
                        # print(f'Plugin "{plugin_instance.info.name}" jest kompatybilny!')
                        plugins[plugin_name] = plugin_instance
                except CompatibilityException as e:
                    if e.status == PluginStatus.NEWER:
                        print(
                            f"Plugin {plugin_instance.info.name} NIE jest kompatybilny! Jest dla nowszej wersji biblioteki!")
                    elif e.status == PluginStatus.OLDER:
                        print(
                            f"Plugin {plugin_instance.info.name} NIE jest kompatybilny! Jest dla starszej wersji biblioteki!")
                    else:
                        print(f"Plugin {plugin_instance.info.name} - stan kompatybilności nieznany!")

            except AttributeError:
                print(f"Plugin class '{plugin_class_name}' not found in module '{plugin_name}'. Skipping...")

        all_plugins[subdir_path.name] = plugins

    return all_plugins


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
        '-e', '--plugins-export-dir', required=False, default=None, type=str,
        dest='plugins_export_dir', help='Export plugins to path',
    )

    argument_parser.add_argument(
        '-s', '--seed', type=int, default=None,
        dest='seed', help='Set seed integer value for color parameter',
    )

    argument_parser.add_argument(
        '-p', '--plugins_dir', type=str, default=str(Path(__file__).parent / 'plugins'),
        dest='plugins_dir', help='Set transcription file names',
    )

    return argument_parser


def generate_screen(plugin_modules) -> List[str]:
    color = Config.colors[4]['color'] if os.geteuid() == 0 else Config.colors[3]['color']
    screen = []

    screen.append(
        get_formated_text(text=' ', background=Config.colors[3]['background'], color=color, full_width=False) +
        get_formated_text(
            text=f'Device-Drama v{Config.metadata["Version"]}        '
                 f'({Config.metadata["Home-page"]})',
            bold=True,
            center=False,
            short_length=2,
            background=Config.colors[3]['background'],
            color=color,
        ) +
        get_formated_text(text=' ', background=Config.colors[3]['background'], color=color, full_width=False)
    )
    screen.append(
        get_formated_text(
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
            get_formated_text(text=' ', background=Config.colors[3]['background'], color=color, full_width=False) +
            get_formated_text(text=header, bold=True, center=False, short_length=2) +
            get_formated_text(text=' ', background=Config.colors[3]['background'], color=color, full_width=False)
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
                line = f' {line["title"]}{line["text"]}'  #  [{dd_plugin.info.name}]'
                screen.append(
                    get_formated_text(
                        text=' ', background=Config.colors[3]['background'], color=color, full_width=False,
                    ) +
                    get_formated_text(
                        text=line,
                        background=Config.colors[plugin_number % 2]['background'],
                        color=Config.colors[plugin_number % 2]['color'],
                        short_length=2,
                    ) +
                    get_formated_text(
                        text=' ', background=Config.colors[3]['background'], color=color, full_width=False,
                    )
                )

        screen.append(
            get_formated_text(
                text='', bold=True, center=True, background=Config.colors[3]['background'], color=color,
            )
        )
    return screen


def export_plugins(source, destination):
    try:
        copy_files(source, destination, exclude_folders=['__pycache__'])
    except PermissionError:
        print("Błąd uprawnień. Upewnij się, że masz odpowiednie uprawnienia do kopiowania.")
    except FileExistsError:
        print(f"Folder docelowy {destination} już istnieje.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")

    if not os.path.exists(source):
        print(f"Ścieżka źródłowa {source} nie istnieje.")
        return


def main():
    """
    jeżeli plugin miał podaną wersję mieszcącą sie w tycm przedziale to wczytaj plugin.
    Jeżeli nie to nie wczytuj pluginu (wywal go z listy?)
    
    Dodać wyświetlanie listy pluginów w formie tabeli (na podstawie podanej ściezki do pluginów)

    Dodać informacje jak nie ma wymaganych atrybutów (minimum jakie oczekuje od pluginu aby posiadał)
    
    """
    Config.arguments = parser().parse_args()

    if Config.arguments.plugins_export_dir:
        if not Path(Config.arguments.plugins_export_dir).exists():
            Path(Config.arguments.plugins_export_dir).mkdir(parents=True)

        export_plugins(
            Path(__file__).parent / 'plugins',
            Path(Config.arguments.plugins_export_dir) / 'device-drama_plugins',
        )
        sys.exit(0)

    plugin_modules = get_plugins(Config.arguments.plugins_dir)

    lolcat_command = ['/usr/games/lolcat', '-p', '19.0', '-F', '1.5', '-t', '-f']
    if Config.arguments.seed:
        lolcat_command = [*lolcat_command, '-S', str(Config.arguments.seed)]

    screen = '\n'.join(generate_screen(plugin_modules))

    if not Config.arguments.color and not Config.arguments.background:
        print(remove_formatting(screen))
        print()
    elif not Config.arguments.color and Config.arguments.background:
        print(screen)
    elif Config.arguments.color and not Config.arguments.background:
        process = subprocess.Popen(lolcat_command, stdin=subprocess.PIPE)
        process.communicate(input=remove_formatting(screen).encode())
        print('\n')
    elif Config.arguments.color and Config.arguments.background:
        process = subprocess.Popen(lolcat_command, stdin=subprocess.PIPE)
        process.communicate(input=screen.encode())
    else:
        print('wtf...')

"""
sudo apt install edid-decode lolcat
Dodać logowanie zdarzeń:
https://docs.python.org/3/library/logging.html
"""

if __name__ == "__main__":
    main()



