from pathlib import Path
import yaml


class Resources:
    def __init__(self, root_directory=None):
        if root_directory:
            self.root_directory = Path(root_directory)
        else:
            self.root_directory = Path(Path(__file__).parent, 'resources')

        self.resource_settings_file_path = Path(Path(__file__).parent, 'resources', 'resources.yaml')

        self.operator_file = None
        self.station_file = None
        self.station_filter_file = None

        self._config = {}

        self._load_resources()
        self._save_paths()

    def _load_resources(self):
        with open(self.resource_settings_file_path, 'r') as fid:
            try:
                self._config = yaml.safe_load(fid)
            except yaml.YAMLError as exc:
                print(exc)

    def _get_path(self, *args, must_exist=True):
        item = self._config
        for arg in args:
            item = item.get(arg, {})
        path = item.get('path', '')
        if not path:
            raise ValueError
        if path.startswith('root'):
            full_path = Path(self.root_directory, path[5:])
        else:
            full_path = Path(path)
        if must_exist and not full_path.exists():
            raise FileNotFoundError(full_path)
        if full_path.is_dir():
            full_path = self._get_paths_in_directory(full_path)
        return full_path

    def _get_paths_in_directory(self, directory):
        if not directory.is_dir():
            raise NotADirectoryError
        return [path for path in directory.iterdir()]

    def _save_paths(self):
        self.operator_file = self._get_path('operators')
        self.station_file = self._get_path('stations', 'stationslista')
        self.station_filter_file = self._get_path('stations', 'filter')
        self.ship_file = self._get_path('ships')

        
if __name__ == '__main__':
    r = Resources()