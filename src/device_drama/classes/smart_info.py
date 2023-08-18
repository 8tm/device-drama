import re
import subprocess

from device_drama.utils import simplify_size_string


class SmartInfo:
    def __init__(self, disk_name):
        self.disk = disk_name
        self.data = self._fetch_smart_info()

    def _fetch_smart_info(self):
        cmd = f"sudo smartctl --info /dev/{self.disk}"
        try:
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
        except subprocess.CalledProcessError:
            return {}

        info = {}
        known_smart_params = {
            'capacity': ['User Capacity:', 'Total NVM Capacity:', 'Namespace 1 Size/Capacity:'],
            'model': ['Device Model:', 'Model Number:'],
            'rotations': ['Rotation Rate:'],
        }

        for line in output.split('\n'):
            param_name = line.split(':')[0] + ':'
            param_value = line.replace(param_name, '').strip()
            for param, options in known_smart_params.items():
                if param_name in options:
                    if param == 'capacity':
                        param_value = simplify_size_string(
                            re.search(r'\[(.*?)\]', param_value).group(1).replace(',', '.')
                        )
                    if param == 'model':
                        param_value = param_value.split('-')[0]
                    if param == 'rotations':
                        param_value = param_value.replace(' rpm', '').split(' ')[0].upper().strip()
                    info[param] = param_value
        return info
