from typing import Dict

from device_drama.classes.base_plugin import BasePlugin


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return Disks info'
        self.info.id = 'D001'
        self.info.name = 'Disks-Info'
        self.info.released = '23.8.20'
        self.info.version = '23.8.20'

    def run(self) -> Dict[str, str]:
        with open('/sys/devices/virtual/dmi/id/sys_vendor', 'r') as mobo_company_file:
            company = mobo_company_file.read().strip()

        with open('/sys/devices/virtual/dmi/id/board_name', 'r') as mobo_name_file:
            model = mobo_name_file.read().strip()

        return {
            "title": "Disks",
            "text": f"{company} {model}"
        }
