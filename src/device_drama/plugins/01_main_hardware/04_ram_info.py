from typing import Dict, List

from device_drama.classes.base_plugin import BasePlugin  # type: ignore
from device_drama.classes.logger import Logger  # type: ignore
from device_drama.misc import format_size  # type: ignore


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.logger = Logger(__name__)
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return RAM info'
        self.info.name = 'RAM-Info'
        self.info.plugin_version = '23.9.12'
        self.info.compatible_version = '23.9.12'

    def run(self) -> List[Dict[str, str]]:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()

        total_memory = 0
        used_memory = 0

        for line in lines:
            if line.startswith('MemTotal:'):
                total_memory = int(line.split()[1]) * 1024   # Convert from KiB to MiB
            elif line.startswith('MemAvailable:'):
                free_memory = int(line.split()[1]) * 1024  # Convert from KiB to MiB
                used_memory = total_memory - free_memory

        percentage_used_memory = round((used_memory / total_memory) * 100, 2)
        used_memory = format_size(used_memory)
        total_memory = format_size(total_memory)

        return [
            {
                'type': 'row',
                'title': ' RAM: ',
                'text': f'Used {used_memory} of {total_memory} ({percentage_used_memory} %)',
            }
        ]
