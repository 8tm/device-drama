from typing import Dict, List, Union


class PluginInfo:
    author: str = ''
    description: str = ''
    id: str = ''
    name: str = ''
    released: str = ''
    version: str = ''


class BasePlugin:
    info: PluginInfo
    args: Dict[str, Union[str, List[str], Dict[str, int]]]

    def __init__(self) -> None:
        self.info = PluginInfo()
        self.command_executor = None
        self.args = {}

    def set_command_executor(self, command_executor) -> None:
        self.command_executor = command_executor

    def run(self) -> List[Dict[str, str]]:
        return [
            {
                "type": "row",
                "title": "DDPlugin",
                "text": "BASE DDPlugin",
            }
        ]

