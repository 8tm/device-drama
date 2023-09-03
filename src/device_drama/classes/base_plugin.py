from typing import Dict, List, Union
from enum import Enum

from device_drama.misc import calendar_version_to_date


class PluginInfo:
    author: str = ''
    description: str = ''
    name: str = ''
    plugin_version: str = ''
    compatible_version: str = ''


class PluginStatus(Enum):
    COMPATIBLE = "compatible"
    NEWER = "newer"
    OLDER = "older"
    UNKNOWN = "unknown"


class CompatibilityException(Exception):
    def __init__(self, status: PluginStatus):
        self.status = status


class BasePlugin:
    info: PluginInfo
    args: Dict[str, Union[str, List[str], Dict[str, int]]]

    def __init__(self) -> None:
        self.info = PluginInfo()
        self.args = {}

    def run(self) -> List[Dict[str, str]]:
        return [
            {
                "type": "row",
                "title": "DDPlugin",
                "text": "BASE DDPlugin",
            }
        ]

    @staticmethod
    def check_compatibility(plugin_version: str, min_version: str, max_version: str) -> PluginStatus:
        created_date = calendar_version_to_date(plugin_version)
        min_date = calendar_version_to_date(min_version)
        max_date = calendar_version_to_date(max_version)

        if min_date <= created_date <= max_date:
            return PluginStatus.COMPATIBLE
        elif created_date < min_date:
            raise CompatibilityException(PluginStatus.OLDER)
        elif created_date > max_date:
            raise CompatibilityException(PluginStatus.NEWER)
