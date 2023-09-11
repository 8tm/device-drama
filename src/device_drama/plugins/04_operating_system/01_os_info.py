import os
from typing import Dict, List

from device_drama.classes.base_plugin import BasePlugin  # type: ignore
from device_drama.classes.logger import Logger  # type: ignore
from device_drama.misc import run_command  # type: ignore


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.logger = Logger(__name__)
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return OS Info'
        self.info.name = 'OS-Info'
        self.info.plugin_version = '23.9.4'
        self.info.compatible_version = '23.9.4'

    @staticmethod
    def get_packages_count() -> str:
        dpkg_output = run_command('dpkg --get-selections').output
        dpkg_count = len([line for line in dpkg_output.split('\n') if 'deinstall' not in line]) - 1

        snap_output = run_command('snap list').output
        snap_count = len(snap_output.split('\n')) - 1

        return f'{dpkg_count} (dpkg), {snap_count} (snap)'

    @staticmethod
    def get_gtk_info(component: str) -> str:
        command = f'gsettings get org.gnome.desktop.interface {component}-theme'
        return run_command(command).output or 'Unknown'

    @staticmethod
    def get_uptime() -> str:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])

            days = int(uptime_seconds // (24 * 3600))
            uptime_seconds = uptime_seconds % (24 * 3600)
            hours = int(uptime_seconds // 3600)
            uptime_seconds %= 3600
            minutes = int(uptime_seconds // 60)
            uptime_seconds %= 60
            seconds = int(uptime_seconds)
            return f'{days} days, {str(hours).zfill(2)}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}'

    def run(self) -> List[Dict[str, str]]:
        os_release = {}
        with open('/etc/os-release', 'r') as file:
            for line in file:
                key, value = line.strip().split('=')
                os_release[key] = value.strip('"')

        return [
            {
                'type': 'row',
                'title': 'Distribution: ',
                'text': os_release.get('NAME', 'Unknown OS'),
            },
            {
                'type': 'row',
                'title': 'Architecture: ',
                'text': os.uname().machine,
            },
            {
                'type': 'row',
                'title': '   Code Name: ',
                'text': os_release.get('VERSION_CODENAME', 'Unknown OS').title(),
            },
            {
                'type': 'row',
                'title': '      Kernel: ',
                'text': os.uname().release,
            },
            {
                'type': 'row',
                'title': '      Uptime: ',
                'text': self.get_uptime(),
            },
            {
                'type': 'row',
                'title': '    Packages: ',
                'text': self.get_packages_count(),
            },

            {
                'type': 'row',
                'title': '       Theme: ',
                'text': self.get_gtk_info('gtk'),
            },
            {
                'type': 'row',
                'title': '       Icons: ',
                'text': self.get_gtk_info('icon'),
            }
        ]
