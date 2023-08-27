import os
import platform
from typing import Dict, List

from device_drama.classes.base_plugin import BasePlugin


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return OS Name'
        self.info.id = 'S001'
        self.info.name = 'OS-Name'
        self.info.released = '23.8.20'
        self.info.version = '23.8.20'

    def get_packages_count(self):
        if platform.system() == "Linux":
            dpkg_count = int(self.command_executor.run_command('dpkg -l | wc -l').output)
            snap_count = int(self.command_executor.run_command('snap list | wc -l').output) - 1
            return f'{str(dpkg_count)} (dpkg), {str(snap_count)} (snap)'
        return [0, 0]

    def get_gtk_info(self, component):
        if platform.system() == "Linux":
            command = f'gsettings get org.gnome.desktop.interface {component}-theme'
            return self.command_executor.run_command(command).output or "Unknown"
        return "Unknown"

    def run(self) -> List[Dict[str, str]]:
        os_release = {}
        with open('/etc/os-release', 'r') as file:
            for line in file:
                key, value = line.strip().split('=')
                os_release[key] = value.strip('"')

        return [
            {
                "type": "row",
                "title": "Distribution: ",
                "text": os_release.get('NAME', 'Unknown OS'),
            },
            {
                "type": "row",
                "title": "Architecture: ",
                "text": os.uname().machine,
            },
            {
                "type": "row",
                "title": "   Code Name: ",
                "text": os_release.get('VERSION_CODENAME', 'Unknown OS').title(),
            },
            {
                "type": "row",
                "title": "      Kernel: ",
                "text": os.uname().release,
            },
            {
                "type": "row",
                "title": "      Uptime: ",
                "text": self.command_executor.run_command('uptime -p').output.replace('up ', ''),
            },
            {
                "type": "row",
                "title": "    Packages: ",
                "text": self.get_packages_count(),
            },


            {
                "type": "row",
                "title": "       Theme: ",
                "text": self.get_gtk_info('gtk'),
            },
            {
                "type": "row",
                "title": "       Icons: ",
                "text": self.get_gtk_info('icon'),
            }
        ]
