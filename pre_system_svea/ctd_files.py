from pathlib import Path
import os
import re
from abc import ABC, abstractmethod


class CtdFileType(ABC):
    _pattern = ''
    _example = ''

    def __repr__(self):
        return f'Pattern: {self._pattern}\nExample: {self._example}'

    @property
    def pattern(self):
        return self._pattern

    @property
    def example(self):
        return self._example

    @abstractmethod
    def year(self, file_stem):
        pass

    @abstractmethod
    def instrument(self, file_stem):
        pass

    @abstractmethod
    def ctry(self, file_stem):
        pass

    @abstractmethod
    def ship(self, file_stem):
        pass

    @abstractmethod
    def serno(self, file_stem):
        pass

    @abstractmethod
    def cruise(self, file_stem):
        pass


class CtdFileTypeFormer(CtdFileType):
    _pattern = '[^_]+_\d{4}_\d{8}_\d{4}_\d{2}_\d{2}_\d{4}'
    _example = 'SBE09_0745_20150218_1040_34_01_0122'

    def year(self, file_stem):
        return file_stem.split('_')[2][:4]

    def instrument(self, file_stem):
        return file_stem.split('_')[0]

    def ctry(self, file_stem):
        return file_stem.split('_')[4]

    def ship(self, file_stem):
        return file_stem.split('_')[5]

    def serno(self, file_stem):
        return file_stem.split('_')[6]

    def cruise(self, *args):
        return None


class CtdFile:
    def __init__(self, path, file_types=None):
        self.path = Path(path)
        self.name = self.path.name
        self.stem = self.path.stem
        for file_type in file_types:
            match = re.findall(file_type.pattern, self.stem)
            if match and match[0] == self.stem:
                self.file_type = file_type

    def get(self, item):
        if hasattr(self.file_type, item):
            return getattr(self.file_type, item)(self.stem)
        return None

    def is_matching(self, **kwargs):
        for key, value in kwargs.items():
            if not self.get(key) == value:
                return False
        return True


class CtdFiles:

    def __init__(self, root_directory):
        self.root_directory = Path(root_directory)
        if not self.root_directory.exists():
            raise NotADirectoryError

        self._file_types = set()

        self.files = {}

        self.use_stem = False

    def check_directory(self):
        self.files = {}
        for root, dirs, files in os.walk(self.root_directory, topdown=False):
            for name in files:
                path = Path(root, name)
                path = CtdFile(path, file_types=self._file_types)
                key = name
                if self.use_stem:
                    key = path.stem
                self.files[key] = path

    def add_file_type(self, file_type_object):
        self._file_types.add(file_type_object)

    def get_file_list_for_instrument(self, sbe=None):
        stems = []
        for stem in self.files:
            if sbe and not stem.startswith(sbe):
                continue
            stems.append(stem)
        return sorted(set(stems))

    def get_files_matching(self, **kwargs):
        matching_series = {}
        for name, obj in self.files.items():
            if obj.is_matching(**kwargs):
                matching_series[name] = obj
        return matching_series

    def get_next_serno(self, **kwargs):
        """
        Returns the highest serno found in files plus one. Check for matching criteria first
        :param serno:
        :return:
        """
        matching_files = self.get_files_matching(**kwargs)
        serno_list = sorted(set([obj.get('serno') for name, obj in matching_files.items()]))
        return serno_list[-1]


def get_ctd_files_object(directory):
    obj = CtdFiles(directory)
    obj.add_file_type(CtdFileTypeFormer())
    obj.check_directory()
    return obj


if __name__ == '__main__':
    c = get_ctd_files_object(r'C:\CTD_BAS_DATA\2012')

