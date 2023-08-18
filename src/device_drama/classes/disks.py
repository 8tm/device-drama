from device_drama.classes.disk_info import DiskInfo


class Disks:
    def __init__(self):
        self.disks = self._fetch_all_disks_info()

    @staticmethod
    def _fetch_all_disks_info():
        disk_names = DiskInfo.list_all_disks()
        return [DiskInfo(disk_name) for disk_name in disk_names]

    def __str__(self):
        return "\n".join([str(disk_info) for disk_info in self.disks])
