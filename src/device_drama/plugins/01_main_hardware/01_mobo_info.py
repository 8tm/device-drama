from typing import Dict, List

from device_drama.classes.base_plugin import BasePlugin


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return MoBo info'
        self.info.name = 'MoBo-Info'
        self.info.plugin_version = '23.8.20'
        self.info.compatible_version = '23.8.30'

    def run(self) -> List[Dict[str, str]]:
        with open('/sys/devices/virtual/dmi/id/sys_vendor', 'r') as mobo_company_file:
            company = mobo_company_file.read().strip()

        with open('/sys/devices/virtual/dmi/id/board_name', 'r') as mobo_name_file:
            model = mobo_name_file.read().strip()

        return [
            {
                'type': 'row',
                'title': 'MoBo: ',
                'text': f'{company} {model}',
            }
        ]

"""
sudo cat /proc/version
Linux version 6.3.0-1-amd64 (debian-kernel@lists.debian.org) (gcc-12 (Debian 12.2.0-14) 12.2.0, GNU ld (GNU Binutils for Debian) 2.40) #1 SMP PREEMPT_DYNAMIC Debian 6.3.7-1 (2023-06-12)

sudo cat /proc/uptime
23089.76 508802.37

sudo cat /proc/swaps
Filename				Type		Size		Used		Priority
/dev/nvme0n1p3                          partition	1000444		0		-2


sudo cat /proc/partitions
major minor  #blocks  name

 259        0  976762584 nvme0n1
 259        1     524288 nvme0n1p1
 259        2  975236096 nvme0n1p2
 259        3    1000448 nvme0n1p3
   8       64 1953514584 sde
   8       65 1953513472 sde1
   8        0 3907018584 sda
   8        1 3907016704 sda1
   8       48 17578328064 sdd
   8       49 17578326016 sdd1
   8       32 17578328064 sdc
   8       33 17578326016 sdc1
   8       16 1953514584 sdb
   8       17 1953513472 sdb1
   7        0          4 loop0
   7        1     255056 loop1
   7        2     121068 loop2
   7        3     108364 loop3
   7        4      64972 loop4
   7        5      64988 loop5
   7        6      75628 loop6
   7        7      75648 loop7
   7        8      99316 loop8
   7        9      99624 loop9
   7       10     497168 loop10
   7       11     497168 loop11
   7       12      93888 loop12
   8       80  250085376 sdf
   8       81  125829120 sdf1
   8       82      32768 sdf2
   8       83  124222464 sdf3
   8       96   61751296 sdg
   8       97   30292992 sdg1
   8       98   31457280 sdg2


sudo cat /proc/filesystems
nodev	sysfs
nodev	tmpfs
nodev	bdev
nodev	proc
nodev	cgroup
nodev	cgroup2
nodev	cpuset
nodev	devtmpfs
nodev	debugfs
nodev	tracefs
nodev	securityfs
nodev	sockfs
nodev	bpf
nodev	pipefs
nodev	ramfs
nodev	hugetlbfs
nodev	devpts
nodev	mqueue
nodev	pstore
	ext3
	ext2
	ext4
nodev	autofs
nodev	efivarfs
nodev	configfs
	fuseblk
nodev	fuse
nodev	fusectl
	vfat
	squashfs
nodev	binfmt_misc
nodev	overlay


"""
