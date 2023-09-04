import platform
import re
import subprocess
from datetime import date, timedelta
from typing import Dict, List


from device_drama.classes.base_plugin import BasePlugin
from device_drama.classes.logger import Logger


BRANDS_DICT = {
    "LEN": "Lenovo",
    "HP": "Hawlett Packard"
}


class Monitor:
    def __init__(self, info, edid_info=None):
        self.resolution = self.extract_resolution(info)
        self.position = self.extract_position(info)
        self.orientation = self.determine_orientation()
        self.id = None

        self.interface = edid_info["interface"] if edid_info else None
        # self.model = f"{get_full_brand_name(edid_info['model'].split()[0])} {edid_info['model'].split()[1]}" if edid_info else "Unknown"
        parts = edid_info['model'].split() if edid_info else []
        brand = get_full_brand_name(parts[0]) if parts else "Unknown"
        model_name = parts[1] if len(parts) > 1 else ""
        self.model = f"{brand} {model_name}" if edid_info else "Unknown"


        self.creation_date = edid_info["creation_date"] if edid_info else "Unknown"

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
        return ['0', '0']

    def determine_orientation(self):
        width, height = [int(dim) for dim in self.resolution.split('x')]
        return 'vertical' if width < height else 'horizontal'

    def set_id(self, monitor_id):
        self.id = monitor_id

    def visual_representation(self):
        vertical_symbol = '\u2395'  # Monitor pionowy
        horizontal_symbol = '\u200A\u2BF3\u200A'  # Monitor poziomy (na podstawce)
        return vertical_symbol if self.orientation == 'vertical' else horizontal_symbol

    def __str__(self):
        return (
            f'ID: {self.id}, Resolution: {self.resolution}, Position: {"x".join(self.position)}, '
            f'Orientation: {self.orientation}, Model: {self.model}, Creation Date: {self.creation_date}'
        )


# Function to get the full brand name
def get_full_brand_name(abbreviation):
    return BRANDS_DICT.get(abbreviation, abbreviation)  # Return abbreviation if not found in the dictionary


# Utility functions from the second file
def decode_edid(edid_data):
    try:
        result = subprocess.check_output(
            ['edid-decode'],
            input=edid_data,
            text=True,
            stderr=subprocess.STDOUT
        )
        return result
    except subprocess.CalledProcessError as e:
        return e.output


def week_to_month(week, year):
    """Przelicza numer tygodnia na miesiąc."""
    d = date(year, 1, 1)
    if d.weekday() > 3:
        d = d + timedelta(7 - d.weekday())
    else:
        d = d - timedelta(d.weekday())
    dlt = timedelta(days=(week - 1) * 7)
    return (d + dlt).strftime('%Y-%m')


def extract_monitors_info(edid_output):
    monitors = []

    edids = edid_output.strip().split("--\n")

    for edid in edids:
        decoded_edid = decode_edid(edid)
        model = "Unknown"
        creation_date = "Unknown"

        model_match = re.compile(r"Display Product Name: '(.+?)'").search(decoded_edid)
        if model_match:
            model = model_match.group(1)

        date_match = re.compile(r"Made in: week (\d+) of (\d+)").search(decoded_edid)
        if date_match:
            creation_date = week_to_month(int(date_match.group(1)), int(date_match.group(2)))

        monitors.append({
            "model": model,
            "creation_date": creation_date
        })

    return monitors


def extract_connection_info(connection_output):
    connection_info_list = []

    for line in connection_output.strip().split("\n"):
        interface_match = re.compile(r"^(.*?) connected").match(line)
        resolution_match = re.compile(r"\d+x\d+").search(line)
        position_match = re.compile(r"\d+x\d+\+(\d+\+\d+)").search(line)

        if interface_match and resolution_match and position_match:
            connection_info_list.append({
                "interface": interface_match.group(1),
                "resolution": resolution_match.group(0),
                "position": position_match.group(1)
            })

    return connection_info_list


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.logger = Logger(__name__)
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return Monitors info'
        self.info.name = 'Monitors-Info'
        self.info.plugin_version = '23.9.4'
        self.info.compatible_version = '23.9.4'

    def get_full_info(self):
        xrandr_output = subprocess.check_output(
            'xrandr -q --verbose',
            shell=True,
            text=True
        )
        connection_output = "\n".join([line for line in xrandr_output.splitlines() if " connected" in line])

        # Get EDID info
        # xrandr_output = subprocess.check_output(
        #     'xrandr -q --verbose | grep -i EDID -A 8 | grep -v EDID | sed s/\\t//g',
        #     shell=True,
        #     text=True
        # ).replace('		', '')

        lines = xrandr_output.splitlines()

        # Filter out EDID related lines
        edid_sections = []
        current_section = []
        capture = False
        count = 0
        for line in lines:
            if "EDID" in line:
                if current_section:  # If we are already capturing, store the previous section and reset
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

        xrandr_output = "--\n".join(["\n".join(section) for section in edid_sections])

        connection_info_list = extract_connection_info(connection_output)
        monitors_info = extract_monitors_info(xrandr_output)

        monitors = []
        for connection, monitor in zip(connection_info_list, monitors_info):
            # Merging the two sets of data
            combined_info = {**connection, **monitor}
            info = f"{connection['resolution']}+{connection['position']}"
            monitors.append(Monitor(info, combined_info))

        monitors.sort(key=lambda m: int(m.position[0]))
        for idx, monitor in enumerate(monitors, 1):
            monitor.set_id(idx)

        return monitors

    def get_full_resolution(self, monitors):
        total_width = sum([int(monitor.resolution.split('x')[0]) for monitor in monitors])
        max_height = max([int(monitor.resolution.split('x')[1]) for monitor in monitors])
        return f'{total_width}x{max_height}'

    def run(self):
        monitors = self.get_full_info()
        monitors_orientation = ''.join([monitor.visual_representation() for monitor in monitors])
        monitor_resolutions = ' + '.join([monitor.resolution for monitor in monitors])

        results = [
            {
                'type': 'row',
                'title': '  Resolution: ',
                'text': f'{self.get_full_resolution(monitors)} ({monitor_resolutions})',
            },
            {
                'type': 'row',
                'title': ' Orientation: ',
                'text': f'{monitors_orientation}',
            }
        ]

        # Adding monitor details
        labels = ['lewy', 'środkowy', 'prawy']
        for idx, monitor in enumerate(monitors):
            results.append({
                'type': 'row',
                'title': f' Monitor {labels[idx]}: ',
                'text': f'{monitor.model} [{monitor.interface}] [{monitor.resolution}+{"x".join(monitor.position)}] [Created: {monitor.creation_date}]'
            })

        return results
