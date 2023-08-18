import json
import os
import subprocess

from device_drama.classes.smart_info import SmartInfo
from device_drama.utils import format_size


class DiskInfo:
    def __init__(self, disk):
        self.disk = disk
        self.lsblk_info = {}
        self.info = {
            "model": "",
            "name": "",
            "tran": "",
            "rota": False,
            "capacity": "",
            "rotations": "----",
            "mounted": 'No',
        }
        self.smart_info = SmartInfo(disk)
        self._fetch_disk_info()

    @staticmethod
    def _is_mounted(device):
        with open('/proc/mounts', 'r') as mounts_file:
            mounts = mounts_file.readlines()
        for mount in mounts:
            if device in mount.split()[0]:
                return 'YES'
        return 'NO'

    def _get_disk_total_size(self, disk_name):
        size_path = f"/sys/block/{disk_name}/size"
        sector_size_path = f"/sys/block/{disk_name}/queue/hw_sector_size"

        with open(size_path, 'r') as f:
            num_sectors = int(f.read().strip())

        with open(sector_size_path, 'r') as f:
            sector_size = int(f.read().strip())

        return num_sectors * sector_size

    def _get_disk_usage(self, disk_name):
        total_space = self._get_disk_total_size(disk_name)

        with open("/proc/mounts", "r") as f:
            mounts = sorted([line.split()[1] for line in f if line.startswith(f"/dev/{disk_name}")])

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
            "size": format_size(total_space),
            "used": format_size(used_space),
            "free": format_size(free_space),
            "used_percentage": f"{used_percentage:.0f}%",
            "free_percentage": f"{free_percentage:.0f}%"
        }

    def _fetch_disk_info(self):
        cmd = f"lsblk -o MODEL,NAME,TRAN,ROTA -J"
        output = subprocess.check_output(cmd, shell=True).decode('utf-8')
        data = json.loads(output)

        for device in data["blockdevices"]:
            if device["name"] == self.disk:
                self.lsblk_info = device
                self.lsblk_info['mounted'] = self._is_mounted(device["name"])

                for param, value in self._get_disk_usage(device["name"]).items():
                    self.lsblk_info[param] = value

                # del self.lsblk_info['children']
                break

        self.info.update(self.lsblk_info)
        self.info.update(self.smart_info.data)

    @staticmethod
    def list_all_disks():
        cmd = "lsblk -o NAME,TYPE -n -l | grep -E '^(sd|nvme).*disk' | awk '{print $1}'"
        output = subprocess.check_output(cmd, shell=True).decode('utf-8')
        return [disk.strip() for disk in output.splitlines()]

    def __str__(self):
        return json.dumps(self.info, indent=4)
