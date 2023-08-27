import platform
from typing import Dict, List

from device_drama.classes.base_plugin import BasePlugin


class Monitor:
    def __init__(self, info):
        self.resolution = self.extract_resolution(info)
        self.position = self.extract_position(info)
        self.orientation = self.determine_orientation()
        self.id = None

    @staticmethod
    def extract_resolution(info):
        for part in info.split():
            if 'x' in part and '+' in part:
                return part.split('+')[0]
        return 'Unknown'

    @staticmethod
    def extract_position(info):
        for part in info.split():
            if '+' in part and part.count('+') == 2:
                return part.split('+')[1:]
        return ["0", "0"]

    def determine_orientation(self):
        width, height = [int(dim) for dim in self.resolution.split('x')]
        return "vertical" if width < height else "horizontal"

    def set_id(self, monitor_id):
        self.id = monitor_id

    def visual_representation(self):
        vertical_symbol = '\u2395'  # Monitor pionowy
        horizontal_symbol = '\u200A\u2BF3\u200A'  # Monitor poziomy na łapkach

        return vertical_symbol if self.orientation == "vertical" else horizontal_symbol

    def __str__(self):
        return f"ID: {self.id}, Resolution: {self.resolution}, Position: {'x'.join(self.position)}, Orientation: {self.orientation}"


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return Monitors info'
        self.info.id = 'H001'
        self.info.name = 'Monitors-Info'
        self.info.released = '23.8.20'
        self.info.version = '23.8.20'

    def get_monitors_info(self):
        if platform.system() == "Linux":
            xrandr_output = self.command_executor.run_command('xrandr | grep " connected" | grep "+"').output
            monitor_lines = xrandr_output.split('\n')

            monitors = []
            for line in monitor_lines:
                monitors.append(Monitor(line))

            monitors.sort(key=lambda m: int(m.position[0]))

            for idx, monitor in enumerate(monitors, 1):
                monitor.set_id(idx)

            return monitors
        return []

    def get_full_resolution(self):
        monitors = self.get_monitors_info()
        total_width = sum([int(monitor.resolution.split('x')[0]) for monitor in monitors])
        max_height = max([int(monitor.resolution.split('x')[1]) for monitor in monitors])
        return f"{total_width}x{max_height}"

    def run(self) -> List[Dict[str, str]]:
        monitors = self.get_monitors_info()
        monitors_orientation = ''.join([monitor.visual_representation() for monitor in monitors])
        monitor_resolutions = ' + '.join([monitor.resolution for monitor in monitors])

        return [
            {
                'type': 'row',
                'title': '  Resolution: ',
                'text': f'{self.get_full_resolution()} ({monitor_resolutions})',
            },
            {
                'type': 'row',
                'title': ' Orientation: ',
                'text': f'{monitors_orientation}',
            },
        ]
