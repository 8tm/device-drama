import os
from typing import Dict, List

from device_drama.classes.base_plugin import BasePlugin  # type: ignore
from device_drama.classes.logger import Logger  # type: ignore
from device_drama.misc import application_exists, run_command  # type: ignore


class DDPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.logger = Logger(__name__)
        self.info.author = 'Tadeusz Miszczyk'
        self.info.description = 'Return Terminal info'
        self.info.name = 'Terminal-info'
        self.info.plugin_version = '23.9.16'
        self.info.compatible_version = '23.9.16'

    @staticmethod
    def get_process_name(pid: str) -> str:
        return run_command(f'ps -o comm= -p {pid}').output.strip()

    @staticmethod
    def get_process_pid(pid_id: str) -> str:
        return run_command(f'ps -o ppid= -p {pid_id}').output.strip()

    def get_terminal_name(self) -> str:
        if not application_exists('ps'):
            return 'Unknown'

        device_drama_pid = self.get_process_pid('$$')            # device-drama pid
        bash_pid = self.get_process_pid(device_drama_pid)        # shell pid
        terminal_or_su_pid = self.get_process_pid(bash_pid)      # terminator pid or su pid if user
        terminal_pid = terminal_or_su_pid

        if os.geteuid() == 0:
            sudo_pid = self.get_process_pid(terminal_or_su_pid)  # sudo pid
            sudo_2_pid = self.get_process_pid(sudo_pid)          # again sudo pid (sudo is running sudo)
            shell_pid = self.get_process_pid(sudo_2_pid)         # shell pid
            terminal_pid = self.get_process_pid(shell_pid)       # terminal pid

        return self.get_process_name(terminal_pid)

    def run(self) -> List[Dict[str, str]]:
        return [
            {
                'type': 'row',
                'title': '    Terminal: ',
                'text': self.get_terminal_name(),
            }
        ]
