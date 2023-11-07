from pathlib import Path
import yaml


class CtdConfig:
    def __init__(self, root_directory):

        self.root_directory = Path(root_directory)

        self.resource_settings_file_path = Path(Path(__file__).parent, 'resources', 'ctd_config.yaml')

        self._config = {}
        self.seasave_xmlcon_files = {}
        self._load_config_file()
        self._save_paths()

    def _load_config_file(self):
        with open(self.resource_settings_file_path, 'r') as fid:
            try:
                self._config = yaml.safe_load(fid)
            except yaml.YAMLError as exc:
                self.root_directory = None
                raise exc

    def _get_path(self, *args, must_exist=True, path_if_not_paths=False, suffix='', dirs=False):
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
        if not dirs:
            if full_path.is_dir():
                full_path = self._get_paths_in_directory(full_path, path_if_not_paths=path_if_not_paths, suffix=suffix)
            else:
                if not full_path.suffix.lower().endswith(suffix.lower()):
                    return None
        else:
            if not full_path.is_dir():
                raise NotADirectoryError
            else:
                full_path =  [path for path in full_path.iterdir() if path.is_dir()]
        return full_path

    def _get_paths_in_directory(self, directory, path_if_not_paths=False, suffix=''):
        if not directory.is_dir():
            raise NotADirectoryError
        paths = []
        for path in directory.iterdir():
            if not path.is_file():
                continue
            if not path.suffix.lower().endswith(suffix.lower()):
                continue
            paths.append(path)

        if len(paths) == 1 and path_if_not_paths:
            paths = paths[0]
        return paths

    def _save_paths(self):
        self.seasave_program_path = self._get_path('seasave', 'program')
        self.seasave_psa_main_file = self._get_path('seasave', 'psa_main_file')
        self.xmlcon_dir = self._get_path('seasave', 'xmlcon_dir', dirs=True)
        for path in self.xmlcon_dir:
            self._save_path_general(path)

    def _save_path_general(self, path):
        instrument_name = path.name
        xmlcons = [i for i in path.iterdir() if i.suffix.lower().endswith('.xmlcon')]
        if not xmlcons:
            raise FileNotFoundError(f'No xmlcon file found for {instrument_name}')
        if type(xmlcons) == list and len(xmlcons)>1:
            raise FileExistsError(
                f'Too many xmlcon files found for {instrument_name} in directory: {xmlcons[0].parent}')
        self.seasave_xmlcon_files[instrument_name] = xmlcons[0]


if __name__ == '__main__':
    r = CtdConfig(r'C:\mw\git\ctd_config')
