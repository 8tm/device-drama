import json
import os
import platform
import re
import shutil
import subprocess


def simplify_size_string(size_str):
    parts = size_str.split(' ')
    value = float(parts[0])
    formatted_value = str(int(value)) if value == int(value) else f"{value:.2f}"
    return f"{formatted_value}{parts[1][0]}"


def format_size(size_bytes):
    b_size = 1024
    units = ('B', 'K', 'M', 'G', 'T')
    for unit in units:
        if size_bytes < b_size:
            raw_str = f"{size_bytes:.2f} {unit}"
            return simplify_size_string(raw_str)
        size_bytes /= b_size


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


class Disks:
    def __init__(self):
        self.disks = self._fetch_all_disks_info()

    @staticmethod
    def _fetch_all_disks_info():
        disk_names = DiskInfo.list_all_disks()
        return [DiskInfo(disk_name) for disk_name in disk_names]

    def __str__(self):
        return "\n".join([str(disk_info) for disk_info in self.disks])


class CommandResult:
    def __init__(self, output, return_code, error_msg):
        self.output = output
        self.return_code = return_code
        self.error_msg = error_msg


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
        return "Unknown"

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


class SystemInfo:
    def __init__(self):
        self.os_info = self.get_os_info()
        self.cpu_info = self.get_cpu_info()
        self.gpu_info = self.get_gpu_info()

    @staticmethod
    def run_command(command):
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
            return CommandResult(result.stdout.strip(), result.returncode, result.stderr.strip())
        except Exception as e:
            return CommandResult("", -1, str(e))

    def get_os_info(self):
        os_release = {}
        with open('/etc/os-release', 'r') as file:
            for line in file:
                key, value = line.strip().split('=')
                os_release[key] = value.strip('"')
        pretty_name = os_release.get('PRETTY_NAME', 'Unknown OS')
        host_type = os.uname().machine
        kernel = os.uname().release
        uptime = self.run_command("uptime -p").output.replace("up ", "")
        return {
            "pretty_name": pretty_name,
            "host_type": host_type,
            "kernel": kernel,
            "uptime": uptime
        }

    def get_cpu_info(self):
        cpu_name_cmd = "cat /proc/cpuinfo | grep 'model name' | uniq | awk 'BEGIN {FS=\":\"}{print $2}' | sed -e 's/(R) Core(TM)//g'"
        cpu_name = self.run_command(cpu_name_cmd).output
        cpu_max_speed_cmd = "lscpu | grep 'CPU max MHz' | awk 'BEGIN {FS=\":\"}{print $2}' | sed -e 's/ //g' | awk 'BEGIN {FS=\",\"}{print $1}'"
        cpu_max_speed = int(self.run_command(cpu_max_speed_cmd).output)
        nproc = int(self.run_command("nproc").output)
        cpu_info = f"{cpu_name} ({nproc}) @ {cpu_max_speed // 1000}.{cpu_max_speed % 1000}GHz"
        return {
            "info": cpu_info
        }

    def get_gpu_info(self):
        gpu_info_cmd = "glxinfo"
        gpu_info = self.run_command(gpu_info_cmd).output
        gpu_name = [line.split(":")[1].strip() for line in gpu_info.split('\n') if "OpenGL renderer string" in line][0]

        gpu_available_memory = -1
        gpu_total_memory = -1000

        for line in gpu_info.split('\n'):
            if "Currently available dedicated video memory" in line:
                gpu_available_memory = int(line.split(":")[1].strip().replace("MB", ""))

        for line in gpu_info.split('\n'):
            if "Total available memory" in line:
                gpu_total_memory = int(line.split(":")[1].strip().replace("MB", ""))

        #gpu_available_memory = int(
        #    [line.split(":")[1].strip().replace("MB", "") for line in gpu_info.split('\n') if "Currently available dedicated video memory" in line][0])
        #gpu_total_memory = int(
        #    [line.split(":")[1].strip().replace("MB", "") for line in gpu_info.split('\n') if "Total available memory" in line][0])

        # for line in gpu_info.split('\n'):
        #     if "Currently available dedicated video memory" in line:
        #         gpu_available_memory = int(
        #             [line.split(":")[1].strip().replace("MB", "") for line in gpu_info.split('\n') if
        #              "Currently available dedicated video memory" in line][0])
        #         gpu_total_memory = int([line.split(":")[1].strip().replace("MB", "") for line in gpu_info.split('\n') if
        #                                 "Total available memory" in line][0])
        #     else:
        #         gpu_available_memory = -1
        #         gpu_total_memory = -1001

        return {
            "name": gpu_name,
            "used_memory_gb": (gpu_total_memory - gpu_available_memory) // 1000,
            "total_memory_gb": gpu_total_memory // 1000
        }

    def get_shell_info(self):
        shell_path = os.environ.get('SHELL', 'Unknown Shell')
        shell_name = os.path.basename(shell_path)
        shell_version_command = f"{shell_path} --version"
        shell_version_output = self.run_command(shell_version_command).output
        shell_version = shell_version_output.split()[3].split('(')[0] if shell_version_output.split() else "Unknown Version"
        return f"{shell_name.title()} {shell_version}"

    def get_window_manager(self):
        if platform.system() == "Linux":
            return self.run_command("xprop -root _NET_WM_NAME").output.split("=")[1].strip().replace('"', '') or "Unknown WM"
        return "Unknown WM"

    def get_gtk_theme_and_icons(self):
        if platform.system() == "Linux":
            theme = self.run_command("gsettings get org.gnome.desktop.interface gtk-theme").output or "Unknown Theme"
            icons = self.run_command("gsettings get org.gnome.desktop.interface icon-theme").output or "Unknown Icons"
            return theme, icons
        return "Unknown Theme", "Unknown Icons"

    def get_monitors_info(self):
        if platform.system() == "Linux":
            xrandr_output = self.run_command('xrandr | grep " connected" | grep "+"').output
            monitor_lines = xrandr_output.split('\n')

            monitors = []
            for line in monitor_lines:
                monitors.append(Monitor(line))

            monitors.sort(key=lambda m: int(m.position[0]))

            for idx, monitor in enumerate(monitors, 1):
                monitor.set_id(idx)

            return monitors
        return []

    def get_terminal_name(self):
        parent_pid = self.run_command('ps -o ppid= -p $$').output.strip()
        grandparent_pid = self.run_command(f'ps -o ppid= -p {parent_pid}').output.strip()
        great_grandparent_pid = self.run_command(f'ps -o ppid= -p {grandparent_pid}').output.strip()
        terminal_process = self.run_command(f'ps -o comm= -p {great_grandparent_pid}').output.strip()
        return terminal_process

    def get_full_resolution(self):
        monitors = self.get_monitors_info()
        total_width = sum([int(monitor.resolution.split('x')[0]) for monitor in monitors])
        max_height = max([int(monitor.resolution.split('x')[1]) for monitor in monitors])
        return f"{total_width}x{max_height}"

    def get_packages_count(self):
        if platform.system() == "Linux":
            dpkg_count = int(self.run_command("dpkg -l | wc -l").output)
            snap_count = int(self.run_command("snap list | wc -l").output) - 1  # odejmujemy 1, aby wykluczyć nagłówek
            return dpkg_count, snap_count
        return 0, 0

    @staticmethod
    def get_memory_info():
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()

        total_memory = "Unknown"
        used_memory = "Unknown"

        for line in lines:
            if line.startswith("MemTotal:"):
                total_memory = int(line.split()[1]) * 1024   # Convert from KiB to MiB
            elif line.startswith("MemAvailable:"):
                free_memory = int(line.split()[1]) * 1024 # Convert from KiB to MiB
                used_memory = total_memory - free_memory

        return format_size(used_memory), format_size(total_memory), round((used_memory / total_memory) * 100,2)

    @staticmethod
    def get_motherboard_info():
        info = {}

        with open('/sys/devices/virtual/dmi/id/sys_vendor', 'r') as mobo_company_file:
            info["company"] = mobo_company_file.read().strip()

        with open('/sys/devices/virtual/dmi/id/board_name', 'r') as mobo_name_file:
            info["name"] = mobo_name_file.read().strip()

        return info

    def get_formated_text(self, text, background=47, color=30, bold=False, center=False):
        columns = shutil.get_terminal_size().columns
        _bold = ''
        if bold:
            _bold = 1

        if center:
            text = text.center(columns)
        else:
            text = text.ljust(columns)

        return f"\033[{_bold};{color};{background}m{text}\033[m"

    def display_all(self):
        shell = self.get_shell_info()
        wm = self.get_window_manager()
        theme, icons = self.get_gtk_theme_and_icons()
        terminal_name = self.get_terminal_name()
        dpkg_count, snap_count = self.get_packages_count()
        used_memory, total_memory, percentage_used_memory = self.get_memory_info()
        monitors = self.get_monitors_info()
        monitors_orientation = ''.join([monitor.visual_representation() for monitor in monitors])
        monitor_resolutions = ' + '.join([monitor.resolution for monitor in monitors])
        full_resolution = self.get_full_resolution()
        mobo = self.get_motherboard_info()
        disks = Disks()
        line = '{model} {capacity} {tran} {rotations} {size} {used} {free} {used_percentage} {free_percentage} {mounted}'
        header = {
            'model': '{:20}'.format('Model'),
            'capacity': '{:>5}'.format('Size'),
            'tran': '{:>4}'.format('Tran'),
            'rotations': '{:^5}'.format('RPM'),
            'size': '{:>8}'.format('Size'),
            'used': '{:>8}'.format('Used'),
            'free': '{:>8}'.format('Free'),
            'used_percentage': '{:>5}'.format('Used%'),
            'free_percentage': '{:>5}'.format('Free%'),
            'mounted': '{:>5}'.format('Mount'),
        }

        os_info = []
        os_info.append('')
        os_info.append(self.get_formated_text(text="Main hardware", bold=True, center=True))
        os_info.append(self.get_formated_text(text=f' MoBo: {mobo["company"]} {mobo["name"]}', background=53, color=40))
        os_info.append(self.get_formated_text(text=f'  CPU: {self.cpu_info["info"]}', background=53, color=100))

        if self.gpu_info["total_memory_gb"] > 0:
            os_info.append(self.get_formated_text(text=f'  GPU: {self.gpu_info["name"]} (Used {self.gpu_info["used_memory_gb"]}GB of {self.gpu_info["total_memory_gb"]}GB)', background=53, color=40))
        else:
            os_info.append(self.get_formated_text(text=f'  GPU: {self.gpu_info["name"]}', background=53, color=40))

        os_info.append(self.get_formated_text(text=f'  RAM: used {used_memory} of {total_memory} ({percentage_used_memory} %)', background=53, color=100))
        os_info.append(self.get_formated_text(text='', background=53, color=39))
        os_info.append('')
        os_info.append(self.get_formated_text(text="Disks", bold=True, center=True))
        os_info.append(self.get_formated_text(text=f' {line.format(**header)}', background=53, color=40))
        for index, disk in enumerate(disks.disks, start=1):
            params = {
                'model': '{:20}'.format(disk.info['model']),
                'capacity': '{:>5}'.format(disk.info['capacity']),
                'tran': '{:>4}'.format(disk.info['tran'].upper()),
                'rotations': '{:>5}'.format(disk.info['rotations']),
                'size': '{:>8}'.format(disk.info['size']),
                'used': '{:>8}'.format(disk.info['used']),
                'free': '{:>8}'.format(disk.info['free']),
                'used_percentage': '{:>5}'.format(disk.info['used_percentage']),
                'free_percentage': '{:>5}'.format(disk.info['free_percentage']),
                'mounted': '{:>5}'.format(disk.info['mounted']),
            }
            os_info.append(self.get_formated_text(text=f' {line.format(**params)}', background=52, color=39))
        os_info.append(self.get_formated_text(text='', background=53, color=39))

        os_info.append(self.get_formated_text(text="Monitors", bold=True, center=True))
        os_info.append(f' Resolution: {full_resolution} ({monitor_resolutions})')
        os_info.append(f' Orientation: {monitors_orientation}\n')

        os_info.append(self.get_formated_text(text="Operating System", bold=True, center=True))
        os_info.append(f' Distribution: {self.os_info["pretty_name"]} {self.os_info["host_type"]}')
        os_info.append(f'       Kernel: {self.os_info["kernel"]}')
        os_info.append(f'       Uptime: {self.os_info["uptime"]}')
        os_info.append(f'        Shell: {shell}')
        os_info.append(f'           WM: {wm}')
        os_info.append(f'        Theme: {theme} [GTK2/3]')
        os_info.append(f'        Icons: {icons} [GTK2/3]')
        os_info.append(f'     Terminal: {terminal_name}')
        os_info.append(f'     Packages: {dpkg_count} (dpkg), {snap_count} (snap)')
        os_info.append(self.get_formated_text(text='', background=53, color=39))
        return '\n'.join(os_info)


def main():
    system_info = SystemInfo()
    print(system_info.display_all())


if __name__ == "__main__":
    main()
