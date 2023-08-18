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
