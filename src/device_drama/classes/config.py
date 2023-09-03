import argparse
import importlib.metadata
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
    compatible_from_version = '23.9.4'
    metadata = importlib.metadata.metadata(str(__package__).replace('.classes', ''))
