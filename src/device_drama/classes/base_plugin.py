from datetime import datetime
from typing import Dict, List, Union


class PluginInfo:
    author: str = ''
    description: str = ''
    name: str = ''
    version: str = ''
    compatible_version: str = ''


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

    def _version_to_date(self, version: str) -> datetime:
        """Converts a version string to a datetime object."""
        year, month, day = map(int, version.split('.'))
        # Add 2000 to year for correct date representation
        return datetime(year + 2000, month, day)

    def is_compatible(self, plugin_version: str, min_version: str, max_version: str) -> str:
        created_date = self._version_to_date(plugin_version)
        min_date = self._version_to_date(min_version)
        max_date = self._version_to_date(max_version)

        if min_date <= created_date <= max_date:
            return "="  # Plugin jest kompatybilny
        elif created_date < min_date:
            return "-"  # Plugin jest niekompatybilny (stworzony dla starszej wersji).
        else:
            return "+"  # Plugin jest niekompatybilny (stworzony dla nowszej wersji skryptu).
