import os
import re
import shutil
import subprocess
from datetime import datetime
from typing import List

from device_drama.classes.logger import Logger  # type: ignore


logger = Logger(__name__)


class CommandResult:
    def __init__(self, output: str, return_code: int, error_msg: str) -> None:
        self.output = output
        self.return_code = return_code
        self.error_msg = error_msg


def run_command(command: str) -> CommandResult:
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
        return CommandResult(result.stdout.strip(), result.returncode, result.stderr.strip())
    except Exception as e:
        logger.error(f'Application exception: {e}')
        return CommandResult('', 1, str(e))


def run_command_with_input(command: List[str], input_data: str) -> CommandResult:
    try:
        result = subprocess.run(command, input=input_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return CommandResult(result.stdout.strip(), result.returncode, result.stderr.strip())
    except Exception as e:
        logger.error(f'Application exception: {e}')
        return CommandResult('', 1, str(e))


def application_exists(name: str) -> bool:
    try:
        path = subprocess.check_output(['which', name])
        logger.info(f'Application exists: {name}')
    except subprocess.CalledProcessError:
        path = ''
        logger.error(f'Application NOT exists: {name}')

    return os.path.exists(path.strip())


def simplify_size_string(size_str: str) -> str:
    parts = size_str.split(' ')
    value = float(parts[0])
    formatted_value = str(int(value)) if value == int(value) else f'{value:.2f}'
    return f'{formatted_value} {parts[1]}'


def format_size(size_bytes: float) -> str:
    b_size = 1024
    units = ('B', 'KB', 'MB', 'GB', 'TB')
    for unit in units:
        if size_bytes < b_size:
            raw_str = f'{size_bytes:.2f} {unit}'
            return simplify_size_string(raw_str)
        size_bytes /= b_size
    return '?? xB'


def calendar_version_to_date(version: str) -> datetime:
    year, month, day = map(int, version.split('.'))
    return datetime(year + 2000, month, day)


def copy_files(source: str, destination: str, exclude_folders: List[str]) -> None:
    if not os.path.exists(destination):
        os.makedirs(destination)

    for item in os.listdir(source):
        source_path = os.path.join(source, item)
        destination_path = os.path.join(destination, item)

        if os.path.isdir(source_path):
            for folder_name in exclude_folders:
                if folder_name not in item:
                    copy_files(source_path, destination_path, exclude_folders)
        else:
            shutil.copy2(source_path, destination_path)


def get_formatted_text(
        text: str, background: int = 47, color: int = 30, bold: bool = False, center: bool = False,
        full_width: bool = True, short_length: int = 0,
) -> str:
    columns = len(text)
    if full_width:
        columns = shutil.get_terminal_size().columns - short_length

    _bold = ''
    if bold:
        _bold = '1'

    if center:
        text = text.center(columns)
    else:
        text = text.ljust(columns)

    return f'\033[{_bold};{color};{background}m{text}\033[m'


def remove_formatting(text: str) -> str:
    return re.sub(r'\033\[\d*(;\d+)*m', '', text).strip()


def utext(text: str, length: int) -> str:
    if len(text) <= length:
        return text
    else:
        return text[:length - 3] + '...'
