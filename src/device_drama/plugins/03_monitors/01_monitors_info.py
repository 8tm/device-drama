import re
from datetime import date, timedelta
from typing import Dict, List

from device_drama.classes.base_plugin import BasePlugin  # type: ignore
from device_drama.classes.logger import Logger  # type: ignore
from device_drama.misc import application_exists, run_command, run_command_with_input  # type: ignore


BRANDS_DICT = {
    'LEN': 'Lenovo',
    'HP': 'Hewlett Packard'
}


class Monitor:
    def __init__(self, info: str, edid_info: Dict[str, str]) -> None:
        self.resolution = self.extract_resolution(info)
        self.position = self.extract_position(info)
        self.orientation = self.determine_orientation()
        self.id = -1

        self.interface = edid_info['interface'] if edid_info else None
        parts = edid_info['model'].split() if edid_info else []
        brand = self.get_full_brand_name(parts[0]) if parts else 'Unknown'
        model_name = parts[1] if len(parts) > 1 else ''
        self.model = f'{brand} {model_name}' if edid_info else 'Unknown'
        self.creation_date = edid_info['creation_date'] if edid_info else 'Unknown'

    @staticmethod
    def extract_resolution(info: str) -> str:
        for part in info.split():
            if 'x' in part and '+' in part:
                return part.split('+')[0]
        return 'Unknown'

    @staticmethod
    def extract_position(info: str) -> List[str]:
        for part in info.split():
            if '+' in part and part.count('+') == 2:
                return part.split('+')[1:]
        return ['0', '0']

    @staticmethod
    def get_full_brand_name(abbreviation: str) -> str:
        return BRANDS_DICT.get(abbreviation, abbreviation)

    def determine_orientation(self) -> str:
        width, height = [int(dim) for dim in self.resolution.split('x')]
        return 'vertical' if width < height else 'horizontal'

    def set_id(self, monitor_id: int) -> None:
        self.id = monitor_id

    def visual_representation(self) -> str:
        vertical_symbol = '\u2395'                # Vertical monitor
        horizontal_symbol = '\u200A\u2BF3\u200A'  # Horizontal monitor (on stand)
        return vertical_symbol if self.orientation == 'vertical' else horizontal_symbol

    def __str__(self) -> str:
        return (
            f'ID: {self.id}, Resolution: {self.resolution}, Position: {"x".join(self.position)}, '
            f'Orientation: {self.orientation}, Model: {self.model}, Creation Date: {self.creation_date}'
        )


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.logger = Logger(__name__)
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return Monitors info'
        self.info.name = 'Monitors-Info'
        self.info.plugin_version = '23.9.12'
        self.info.compatible_version = '23.9.12'

    @staticmethod
    def extract_connection_info(connection_output: str) -> List[Dict[str, str]]:
        connection_info_list = []

        for line in connection_output.strip().split('\n'):
            interface_match = re.compile(r'^(.*?) connected').match(line)
            resolution_match = re.compile(r'\d+x\d+').search(line)
            position_match = re.compile(r'\d+x\d+\+(\d+\+\d+)').search(line)

            if interface_match and resolution_match and position_match:
                connection_info_list.append({
                    'interface': interface_match.group(1),
                    'resolution': resolution_match.group(0),
                    'position': position_match.group(1)
                })

        return connection_info_list

    @staticmethod
    def week_to_month(week: int, year: int) -> str:
        d = date(year, 1, 1)
        if d.weekday() > 3:
            d = d + timedelta(7 - d.weekday())
        else:
            d = d - timedelta(d.weekday())
        dlt = timedelta(days=(week - 1) * 7)
        return (d + dlt).strftime('%Y-%m')

    @staticmethod
    def decode_edid(edid_data: str) -> str:
        if not application_exists('edid-decode'):
            return ''

        result = run_command_with_input(['edid-decode'], edid_data)

        if result.return_code > 0:
            return result.error_msg

        return result.output

    def extract_monitors_info(self, edid_output: str) -> List[Dict[str, str]]:
        monitors = []

        edids = edid_output.strip().split('--\n')

        for edid in edids:
            decoded_edid = self.decode_edid(edid)
            model = 'Unknown'
            creation_date = 'Unknown'

            model_match = re.compile(r"Display Product Name: '(.+?)'").search(decoded_edid)
            if model_match:
                model = model_match.group(1)

            date_match = re.compile(r'Made in: week (\d+) of (\d+)').search(decoded_edid)
            if date_match:
                creation_date = self.week_to_month(int(date_match.group(1)), int(date_match.group(2)))

            monitors.append({
                'model': model,
                'creation_date': creation_date
            })

        return monitors

    def get_full_info(self) -> List[Monitor]:
        if not application_exists('xrandr'):
            return []

        xrandr_output = run_command('xrandr -q --verbose').output
        connection_output = '\n'.join([line for line in xrandr_output.splitlines() if ' connected' in line])

        lines = xrandr_output.splitlines()

        edid_sections = []
        current_section: List[str] = []
        capture = False
        count = 0
        for line in lines:
            if 'EDID' in line:
                if current_section:
                    edid_sections.append(current_section)
                    current_section = []
                capture = True
                count = 0
                continue
            if capture:
                count += 1
                if count <= 8:
                    current_section.append(
                        line.strip())
                else:
                    capture = False

        if current_section:
            edid_sections.append(current_section)

        xrandr_output = '--\n'.join(['\n'.join(section) for section in edid_sections])

        connection_info_list = self.extract_connection_info(connection_output)
        monitors_info = self.extract_monitors_info(xrandr_output)

        monitors: List[Monitor] = []
        for connection, monitor in zip(connection_info_list, monitors_info):
            combined_info = {**connection, **monitor}
            info = f"{connection['resolution']}+{connection['position']}"
            monitors.append(Monitor(info, combined_info))

        monitors.sort(key=lambda m: int(m.position[0]))
        for idx, monitor in enumerate(monitors, 1):  # type: ignore
            monitor.set_id(idx)  # type: ignore

        return monitors

    @staticmethod
    def get_full_resolution(monitors: List[Monitor]) -> str:
        total_width = sum([int(monitor.resolution.split('x')[0]) for monitor in monitors])
        max_height = max([int(monitor.resolution.split('x')[1]) for monitor in monitors])
        return f'{total_width}x{max_height}'

    def run(self) -> List[Dict[str, str]]:
        monitors = self.get_full_info()
        if len(monitors) == 0:
            return [
                {
                    'type': 'row',
                    'title': ' Orientation: ',
                    'text': 'Unknown',
                },
                {
                    'type': 'row',
                    'title': '  Resolution: ',
                    'text': 'Unknown',
                }
            ]

        monitors_orientation = ''.join([monitor.visual_representation() for monitor in monitors])
        monitor_resolutions = ' + '.join([monitor.resolution for monitor in monitors])

        results = [
            {
                'type': 'row',
                'title': ' Orientation: ',
                'text': f'{monitors_orientation}',
            },
            {
                'type': 'row',
                'title': '  Resolution: ',
                'text': f'{self.get_full_resolution(monitors)} ({monitor_resolutions})',
            }
        ]

        for idx, monitor in enumerate(monitors, start=1):
            results.append({
                'type': 'row',
                'title': f'  Monitor {idx:2}: ',
                'text': f'{monitor.model:20} '
                        f'[{monitor.interface:^8}] '
                        f'[{monitor.resolution:9}] '
                        f'[Constructed: {monitor.creation_date:7}]'
            })

        return results
