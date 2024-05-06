from typing import Dict, List

from device_drama.classes.base_plugin import BasePlugin  # type: ignore
from device_drama.classes.logger import Logger  # type: ignore
from device_drama.misc import application_exists, run_command  # type: ignore


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.logger = Logger(__name__)
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return WM info'
        self.info.name = 'WM-info'
        self.info.plugin_version = '23.9.16'
        self.info.compatible_version = '23.9.16'

    @staticmethod
    def get_window_manager() -> str:
        wm = 'Unknown'

        if not application_exists('xprop'):
            return wm

        process = run_command('xprop -root _NET_WM_NAME')

        if process.return_code > 0:
            return wm

        if '=' in process.output:
            wm = process.output.split('=')[1].strip().replace('"', '')

        return wm

    def run(self) -> List[Dict[str, str]]:
        return [
            {
                'type': 'row',
                'title': '          WM: ',
                'text': self.get_window_manager(),
            }
        ]
