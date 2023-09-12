from typing import Dict, List

from device_drama.classes.base_plugin import BasePlugin  # type: ignore
from device_drama.classes.logger import Logger  # type: ignore


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.logger = Logger(__name__)
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return CPU info'
        self.info.name = 'CPU-Info'
        self.info.plugin_version = '23.9.12'
        self.info.compatible_version = '23.9.12'

    def run(self) -> List[Dict[str, str]]:
        with open('/proc/cpuinfo', 'r') as file:
            for line in file:
                if 'model name' in line:
                    return [
                        {
                            'type': 'row',
                            'title': ' CPU: ',
                            'text': line.split(':')[1].strip(),
                        }
                    ]
        return [{'type': 'row', 'title': ' CPU: ', 'text': ''}]
