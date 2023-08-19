from device_drama.classes.disk_info import DiskInfo


class Disks:
    use_sudo: bool = False

    def __init__(self, use_sudo):
        self.use_sudo = use_sudo
        self.disks = self._fetch_all_disks_info()

    def _fetch_all_disks_info(self):
        disk_names = DiskInfo.list_all_disks()
        return [DiskInfo(disk_name, self.use_sudo) for disk_name in disk_names]

    def __str__(self):
        return "\n".join([str(disk_info) for disk_info in self.disks])
