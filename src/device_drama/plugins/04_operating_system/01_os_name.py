from typing import Dict

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

    def run(self) -> Dict[str, str]:
        with open("/etc/os-release", "r") as file:
            for line in file:
                if line.startswith("PRETTY_NAME"):
                    return {
                        "title": "OS-name",
                        "text": line.split("=")[1].strip().strip('"')
                    }
        return {"title": "OS-name", "text": ''}
