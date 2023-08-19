import argparse

from device_drama.classes.system_info import SystemInfo

def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description='Validate audio and text files.')

    argument_parser.add_argument(
        '-s', '--sudo', action='store_true', required=False, default=False,
        help='Print information which required root permissions',
    )
    return argument_parser


def main():
    arguments = parser().parse_args()
    system_info = SystemInfo(arguments.sudo)
    print(system_info.display_all())


if __name__ == "__main__":
    main()
