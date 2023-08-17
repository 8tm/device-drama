from typing import Dict, List, Union

from device_drama.classes.logger import Logger  # type: ignore


class PluginInfo:
    author: str = ''
    description: str = ''
    name: str = ''
    plugin_version: str = ''
    compatible_version: str = ''


class BasePlugin:
    info: PluginInfo
    args: Dict[str, Union[str, List[str], Dict[str, int]]]
    logger: Logger = Logger(__name__)

    def __init__(self) -> None:
        self.info = PluginInfo()
        self.args = {}

    def run(self) -> List[Dict[str, str]]:
        return [
            {
                'type': 'row',
                'title': 'DDPlugin',
                'text': 'BASE DDPlugin',
            }
        ]
