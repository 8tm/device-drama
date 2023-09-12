import argparse
import importlib.metadata
from pathlib import Path
from typing import Dict, List


class Config:
    arguments: argparse.Namespace
    colors: List[Dict[str, int]] = [
        {'background': 53, 'color': 40},
        {'background': 53, 'color': 100},
        {'background': 53, 'color': 39},
        {'background': 250, 'color': 44},
        {'background': 250, 'color': 41},
    ]
    logger_file_path: Path = Path.home() / '.local' / 'share' / 'device-drama' / 'device-drama.log'
    required_packages = ('lolcat', 'edid-decode', 'smartmontools')
    compatible_from_version = '23.9.12'
    metadata = importlib.metadata.metadata(str(__package__).replace('.classes', ''))
