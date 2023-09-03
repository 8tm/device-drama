import logging


class Logger:
    def __init__(self, name):
        self._logger = logging.getLogger(name)

        if not logging.root.handlers:
            self.setup_logging()

        self.info('Logger initiated!')

    @staticmethod
    def setup_logging():
        logging.basicConfig(
            filename='/tmp/device-drama.log',
            level=logging.INFO,
            format='[{asctime}.{msecs:0<3.0f}] [{levelname:7}]  {message}  [{name}]',
            datefmt='%Y-%m-%d %H:%M:%S',
            style='{',
        )

    def info(self, message):
        self._logger.info(message)

    def warning(self, message):
        self._logger.warning(message)

    def error(self, message):
        self._logger.error(message)

    def __del__(self):
        self.info('Logger terminated!')
