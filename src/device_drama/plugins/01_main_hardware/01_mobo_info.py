from typing import Dict, List
from pathlib import Path

from device_drama.classes.base_plugin import BasePlugin  # type: ignore
from device_drama.classes.logger import Logger  # type: ignore


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.logger = Logger(__name__)
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return MoBo info'
        self.info.name = 'MoBo-Info'
        self.info.plugin_version = '24.5.13'
        self.info.compatible_version = '23.9.12'

    def run(self) -> List[Dict[str, str]]:
        company = '<Unknown>'
        if Path('/sys/devices/virtual/dmi/id/sys_vendor').exists():
            with open('/sys/devices/virtual/dmi/id/sys_vendor', 'r') as mobo_company_file:
                company = mobo_company_file.read().strip()

        model = '<Unknown>'
        if Path('/sys/devices/virtual/dmi/id/board_name').exists():
            with open('/sys/devices/virtual/dmi/id/board_name', 'r') as mobo_name_file:
                model = mobo_name_file.read().strip()

        return [
            {
                'type': 'row',
                'title': 'MoBo: ',
                'text': f'{company} {model}',
            }
        ]
