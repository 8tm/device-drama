import logging

from device_drama.classes.config import Config  # type: ignore


class Logger:
    separator_logged = False

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

        if not logging.root.handlers:
            self.setup_logging()

        if not Logger.separator_logged:
            self._logger.info(f'{6*"-"} <<<< NEXT EXECUTION >>>> {6*"-"}')
            Logger.separator_logged = True

        self.info('Logger initiated.')

    @staticmethod
    def setup_logging() -> None:
        Config.logger_file_path.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=Config.logger_file_path,
            level=logging.INFO,
            format='[{asctime}.{msecs:0<3.0f}] [{levelname:7}]  {message}  [{name}]',
            datefmt='%Y-%m-%d %H:%M:%S',
            filemode='a',
            style='{',
        )

    def info(self, message: str) -> None:
        self._logger.info(message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)

    def error(self, message: str) -> None:
        self._logger.error(message)

    def __del__(self) -> None:
        try:
            self.info('Logger terminated.')
        except NameError:
            pass
