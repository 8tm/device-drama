from typing import Dict

from device_drama.classes.base_plugin import BasePlugin


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return GPU info'
        self.info.id = 'H003'
        self.info.name = 'GPU-Info'
        self.info.released = '23.8.20'
        self.info.version = '23.8.20'

    def run(self) -> Dict[str, str]:
        gpu_info = self.command_executor.run_command('glxinfo').output
        gpu_name = [line.split(":")[1].strip() for line in gpu_info.split('\n') if "OpenGL renderer string" in line][0]

        gpu_available_memory = -1
        gpu_total_memory = -1000

        for line in gpu_info.split('\n'):
            if "Currently available dedicated video memory" in line:
                gpu_available_memory = int(line.split(":")[1].strip().replace("MB", ""))

        for line in gpu_info.split('\n'):
            if "Total available memory" in line:
                gpu_total_memory = int(line.split(":")[1].strip().replace("MB", ""))

        gpu_info = gpu_name
        if gpu_total_memory // 1000 > 0:
            gpu_info += f' (Used {(gpu_total_memory - gpu_available_memory) // 1000}GB of {gpu_total_memory // 1000}GB)'

        return {
            "title": " GPU",
            "text": gpu_info
        }
