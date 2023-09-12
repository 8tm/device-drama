from typing import Dict, List

from device_drama.classes.base_plugin import BasePlugin  # type: ignore
from device_drama.classes.logger import Logger  # type: ignore
from device_drama.misc import application_exists, run_command  # type: ignore


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.logger = Logger(__name__)
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return GPU info'
        self.info.name = 'GPU-Info'
        self.info.plugin_version = '23.9.12'
        self.info.compatible_version = '23.9.12'

    def run(self) -> List[Dict[str, str]]:
        if not application_exists('glxinfo'):
            return [
                {
                    'type': 'row',
                    'title': ' GPU: ',
                    'text': 'Unknown',
                }
            ]

        gpu_info = run_command('glxinfo').output
        gpu_name = [line.split(':')[1].strip() for line in gpu_info.split('\n') if 'OpenGL renderer string' in line][0]

        gpu_available_memory = -1
        gpu_total_memory = -1000

        for line in gpu_info.split('\n'):
            if 'Currently available dedicated video memory' in line:
                gpu_available_memory = int(line.split(':')[1].strip().replace('MB', ''))

        for line in gpu_info.split('\n'):
            if 'Total available memory' in line:
                gpu_total_memory = int(line.split(':')[1].strip().replace('MB', ''))

        gpu_info = gpu_name
        if gpu_total_memory // 1000 > 0:
            gpu_info += (
                f' (Used {(gpu_total_memory - gpu_available_memory) // 1000} GB of {gpu_total_memory // 1000} GB)'
            )

        return [
            {
                'type': 'row',
                'title': ' GPU: ',
                'text': gpu_info,
            }
        ]
