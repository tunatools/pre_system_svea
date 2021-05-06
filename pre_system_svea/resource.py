from pathlib import Path


class Resources:
    def __init__(self):
        self.root_directory = Path(Path(__file__).parent, 'resources')

        self._load_resources_paths()

    def _load_resources_paths(self):
        self.operator_file = Path(self.root_directory, 'operators.json')
        self.station_file = Path(self.root_directory, 'station.txt')