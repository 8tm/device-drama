from typing import Dict, List

from device_drama.classes.base_plugin import BasePlugin


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return CPU info'
        self.info.name = 'CPU-Info'
        self.info.plugin_version = '23.8.20'
        self.info.compatible_version = '23.8.30'

    def run(self) -> List[Dict[str, str]]:
        with open('/proc/cpuinfo', 'r') as file:
            for line in file:
                if 'model name' in line:
                    return [
                        {
                            'type':  'row',
                            'title': ' CPU: ',
                            'text':  line.split(':')[1].strip(),
                        }
                    ]
        return [{'type': 'row', 'title': ' CPU: ', 'text': ''}]
