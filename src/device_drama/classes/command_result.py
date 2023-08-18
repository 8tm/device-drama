class CommandResult:
    def __init__(self, output, return_code, error_msg):
        self.output = output
        self.return_code = return_code
        self.error_msg = error_msg
