from typing import Dict, List, Union


class PluginInfo:
    author: str = ''
    description: str = ''
    id: str = ''
    name: str = ''
    released: str = ''
    version: str = ''


class BasePlugin:
    info: PluginInfo = PluginInfo()
    command_executor = None
    args: Dict[str, Union[str, List[str], Dict[str, int]]]

    def set_command_executor(self, command_executor):
        self.command_executor = command_executor

    def run(self) -> Dict[str, str]:
        return {
            "title": "DDPlugin",
            "text": "BASE DDPlugin"
        }
