from pathlib import Path
import os
import re


class CtdData:

    def __init__(self, root_directory):
        self.root_directory = Path(root_directory)

        self._file_pattern = '.+_\d{4}(?=_\d{8}_\d{4}_\d{2}_\d{2}_\d{4})'

        self.raw_file_paths = {}

        self._save_raw_file_paths()

    def _save_raw_file_paths(self):
        stems = {}
        for root, dirs, files in os.walk(self.root_directory, topdown=False):
            for name in files:
                path = Path(root, name)
                stem = path.stem
                if re.findall(self._file_pattern, stem):
                    stems[stem] = Path(path.parent, stem)
        self.raw_file_paths = stems

    def get_raw_files_list(self, sbe=None, reload=False):
        if reload:
            self._save_raw_file_paths()
        stems = []
        for stem in self.raw_file_paths:
            if sbe and not stem.startswith(sbe):
                continue
            stems.append(stem)
        return sorted(set(stems))

    def series_is_present(self, sbe=None, ctry=None, ship=None, serno=None, reload=False):
        if reload:
            self._save_raw_file_paths()
        for stem in self.raw_file_paths:
            if sbe and not stem.startswith(sbe):
                continue
            if serno and not stem.endswith(serno):
                continue
            if ctry and stem[-10:-8] != ctry:
                continue
            if ctry and stem[-7:-5] != ship:
                continue
            return True
        return False


if __name__ == '__main__':
    c = CtdData(r'C:\mw\temp_svea\raw_files')
    print(c.get_raw_files_list())

