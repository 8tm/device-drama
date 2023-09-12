import json
import os
import re
from typing import Dict, List, Tuple

from device_drama.classes.base_plugin import BasePlugin  # type: ignore
from device_drama.classes.logger import Logger  # type: ignore
from device_drama.misc import format_size, simplify_size_string, utext  # type: ignore
from device_drama.misc import application_exists, run_command  # type: ignore


class SmartInfo:
    def __init__(self, disk_name: str) -> None:
        self.disk = disk_name
        self.data = self._fetch_smart_info()

    def _fetch_smart_info(self) -> Dict[str, str]:
        if not application_exists('smartctl'):
            return {}

        output = run_command(f'smartctl --info /dev/{self.disk}').output

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
                            re.search(r'\[(.*?)\]', param_value).group(1).replace(',', '.')  # type: ignore
                        )
                    if param == 'model':
                        param_value = param_value.split('-')[0]
                    if param == 'rotations':
                        param_value = param_value.replace(' rpm', '').split(' ')[0].upper().strip()
                    info[param] = param_value
        return info


class DiskInfo:
    def __init__(self, disk: str) -> None:
        self.disk = disk
        self.lsblk_info: Dict[str, str] = {}
        self.info = {
            'model': '',
            'name': '',
            'tran': '',
            'rota': False,
            'capacity': '------',
            'rotations': '----',
            'mounted': 'No',
        }

        if os.geteuid() == 0:
            self.smart_info = SmartInfo(disk)
        self._fetch_disk_info()

    @staticmethod
    def _is_mounted(device: str) -> Tuple[str, str]:
        with open('/proc/mounts', 'r') as mounts_file:
            mounts = mounts_file.readlines()
        for mount in mounts:
            if device in mount.split()[0]:
                return 'YES', mount.split()[1]
        return 'NO', ''

    @staticmethod
    def _get_disk_total_size(disk_name: str) -> int:
        with open(f'/sys/block/{disk_name}/size', 'r') as f:
            num_sectors = int(f.read().strip())

        with open(f'/sys/block/{disk_name}/queue/hw_sector_size', 'r') as f:
            sector_size = int(f.read().strip())

        return num_sectors * sector_size

    def _get_disk_usage(self, disk_name: str) -> Dict[str, str]:
        total_space = self._get_disk_total_size(disk_name)

        with open('/proc/mounts', 'r') as mounts_file:
            mounts = sorted([line.split()[1] for line in mounts_file if line.startswith(f'/dev/{disk_name}')])

        primary_mount = mounts[0] if mounts else None

        if primary_mount:
            stat = os.statvfs(primary_mount)
            free_space = stat.f_frsize * stat.f_bfree
            used_space = total_space - free_space
        else:
            # If the disk is unmounted, we can't get the exact used and free space
            used_space = total_space
            free_space = 0

        used_percentage = (used_space / total_space) * 100 if total_space != 0 else 0
        free_percentage = 100 - used_percentage

        return {
            'size': format_size(total_space),
            'used': format_size(used_space),
            'free': format_size(free_space),
            'used_percentage': f'{used_percentage:.0f}%',
            'free_percentage': f'{free_percentage:.0f}%'
        }

    def _fetch_disk_info(self) -> None:
        if not application_exists('lsblk'):
            self.info = {
                'model': '???',
                'name': '???',
                'tran': '???',
                'rota': False,
                'capacity': '???',
                'rotations': '???',
                'mounted': '???',
                'size': '???',
                'used': '???',
                'free': '???',
                'used_percentage': '???',
                'free_percentage': '???',
                'mount_path': '???',
            }
            return

        output = run_command('lsblk -o MODEL,NAME,TRAN,ROTA -J').output
        data = json.loads(output)

        for device in data['blockdevices']:
            if device['name'] == self.disk:
                self.lsblk_info = device
                self.lsblk_info['mounted'], self.lsblk_info['mount_path'] = self._is_mounted(device['name'])

                for param, value in self._get_disk_usage(device['name']).items():
                    self.lsblk_info[param] = value

                break

        self.info.update(self.lsblk_info)

        if os.geteuid() == 0:
            self.info.update(self.smart_info.data)

    @staticmethod
    def list_all_disks() -> List[str]:
        return sorted([device for device in os.listdir('/sys/block/') if device.startswith(('sd', 'nvme'))])

    def __str__(self) -> str:
        return json.dumps(self.info, indent=4)


class Disks:
    def __init__(self) -> None:
        self.disks = self._fetch_all_disks_info()

    @staticmethod
    def _fetch_all_disks_info() -> List[DiskInfo]:
        disk_names = DiskInfo.list_all_disks()
        return [DiskInfo(disk_name) for disk_name in disk_names]

    def __str__(self) -> str:
        return '\n'.join([str(disk_info) for disk_info in self.disks])


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.logger = Logger(__name__)
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return Disks info'
        self.info.name = 'Disks-Info'
        self.info.plugin_version = '23.9.12'
        self.info.compatible_version = '23.9.12'

    def run(self) -> List[Dict[str, str]]:
        disks_info = []
        disks = Disks()
        columns = (
            '{model} '
            '{capacity} '
            '{tran} '
            '{rotations} '
            '{size} '
            '{used} '
            '{free} '
            '{used_percentage} '
            '{free_percentage} '
            '{mounted} '
            '{mount_path}'
        )
        header = {
            'model': '{:20}'.format('Model'),
            'capacity': '{:>10}'.format('Size'),
            'tran': '{:>4}'.format('Tran'),
            'rotations': '{:^5}'.format('RPM'),
            'size': '{:>10}'.format('Real Size'),
            'used': '{:>10}'.format('Real Used'),
            'free': '{:>10}'.format('Real Free'),
            'used_percentage': '{:>5}'.format('Used%'),
            'free_percentage': '{:>5}'.format('Free%'),
            'mounted': '{:>5}'.format('Mount'),
            'mount_path': '{:50}'.format('Mount path'),

        }

        disks_info.append(
            {
                'type': 'header',
                'title': 'ID ',
                'text': columns.format(**header),
            }
        )

        for index, disk in enumerate(disks.disks, start=1):
            params = {
                'model': '{:20}'.format(utext(disk.info['model'], 20)),
                'capacity': '{:>10}'.format(utext(disk.info['capacity'], 10)),
                'tran': '{:>4}'.format(str(disk.info['tran']).upper()),
                'rotations': '{:>5}'.format(disk.info['rotations']),
                'size': '{:>10}'.format(disk.info['size']),
                'used': '{:>10}'.format(disk.info['used']),
                'free': '{:>10}'.format(disk.info['free']),
                'used_percentage': '{:>5}'.format(disk.info['used_percentage']),
                'free_percentage': '{:>5}'.format(disk.info['free_percentage']),
                'mounted': '{:>5}'.format(disk.info['mounted']),
                'mount_path': '{:50}'.format(utext(disk.info['mount_path'], 50)),
            }
            disks_info.append(
                {
                    'type': 'row',
                    'title': f'{index:^3}',
                    'text': columns.format(**params),
                }
            )

        return disks_info
