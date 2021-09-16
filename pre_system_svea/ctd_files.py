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
    def year(self, file_path):
        pass

    @abstractmethod
    def instrument(self, file_path):
        pass

    @abstractmethod
    def ship(self, file_path):
        pass

    @abstractmethod
    def serno(self, file_path):
        pass

    @abstractmethod
    def cruise(self, file_path):
        pass


class CtdFileTypeFormer(CtdFileType):
    _pattern = '[^_]+_\d{4}_\d{8}_\d{4}_\d{2}_\d{2}_\d{4}'
    _example = 'SBE09_1387_20210413_1113_77_10_0278'

    def year(self, file_path):
        return file_path.stem.split('_')[2][:4]

    def instrument(self, file_path):
        return file_path.stem.split('_')[0]

    def ship(self, file_path):
        return file_path.stem.split('_')[4] + file_path.stem.split('_')[5]

    def serno(self, file_path):
        return file_path.stem.split('_')[6]

    def cruise(self, *args):
        return None


class CtdFileTypeSvea(CtdFileType):
    _pattern = '[^_]+_\d{4}_\d{8}_\d{4}_\d{2}[a-zA-Z]{2}_\d{2}_\d{4}'
    _example = 'SBE09_1387_20210413_1113_77SE_01_0278'

    def year(self, file_path):
        return file_path.stem.split('_')[2][:4]

    def instrument(self, file_path):
        return file_path.stem.split('_')[0]

    def ship(self, file_path):
        return file_path.stem.split('_')[4]

    def serno(self, file_path):
        return file_path.stem.split('_')[6]

    def cruise(self, file_path):
        return file_path.stem.split('_')[5]


class CtdFile:
    def __init__(self, path, file_types=None):
        self.valid = True
        self.path = Path(path)
        self.name = self.path.name
        self.stem = self.path.stem
        self.suffix = self.path.suffix
        for file_type in file_types:
            match = re.findall(file_type.pattern, self.stem)
            # print('match', match)
            # print(match[0])
            # print(self.stem)
            if match and match[0] == self.stem:
                # print('OK')
                self.file_type = file_type
                break
        else:
            self.valid = False

    def get(self, item):
        if hasattr(self.file_type, item):
            return getattr(self.file_type, item)(self.path)
        return None

    def is_matching(self, **kwargs):
        for key, value in kwargs.items():
            item = self.get(key)
            # print('TRY MATCHING:', key, value, item)
            if not item:
                continue
            if item == None:
                continue
            if item != value:
                # print('NOT MATCHING:', key, value, item)
                return False
        return True


class CtdFiles:

    def __init__(self, root_directory, use_stem=False, suffix=None):
        self.root_directory = Path(root_directory)
        if not self.root_directory.exists():
            raise NotADirectoryError(self.root_directory)

        self._file_types = set()

        self.files = {}

        self.use_stem = use_stem
        self.suffix = suffix

    def check_directory(self):
        self.files = {}
        # print('ROOT directory in CtdFiles', self.root_directory)
        for root, dirs, files in os.walk(self.root_directory, topdown=False):
            for name in files:
                path = Path(root, name)
                path = CtdFile(path, file_types=self._file_types)
                # print(path.valid)
                if not path.valid:
                    continue
                if self.suffix and path.suffix != self.suffix:
                    continue
                key = name
                if self.use_stem:
                    key = path.stem
                self.files[key] = path

    def add_file_type(self, file_type_object):
        self._file_types.add(file_type_object)

    def get_files_matching(self, as_list=False, **kwargs):
        matching_series = {}
        # print('self.files', self.files)
        for name in sorted(self.files):
            obj = self.files[name]
            if obj.is_matching(**kwargs):
                matching_series[name] = obj
        if as_list:
            return list(matching_series.values())
        return matching_series

    def get_latest_serno(self, **kwargs):
        """
        Returns the highest serno found in files. Check for matching criteria in kwargs first.
        :param serno:
        :return:
        """
        # print('get_latest_serno kwargs: ', kwargs)
        matching_files = self.get_files_matching(**kwargs)
        serno_list = sorted(set([obj.get('serno') for name, obj in matching_files.items()]))
        if not serno_list:
            return None
        return serno_list[-1]

    def get_latest_series(self, path=False, **kwargs):
        serno = self.get_latest_serno(**kwargs)
        kwargs['serno'] = serno
        # print('ctd_files.get_latest_series kwargs', kwargs)
        matching_files = self.get_files_matching(**kwargs)
        if not matching_files:
            return None
        if len(matching_files) > 1:
            raise ValueError('More than one mathing file')
        obj = matching_files[list(matching_files.keys())[0]]
        if path:
            return obj.path
        return obj

    def get_next_serno(self, **kwargs):
        latest_serno = self.get_latest_serno(**kwargs)
        if not latest_serno:
            return '0001'
        next_serno = str(int(latest_serno)+1).zfill(4)
        return next_serno

    def series_exists(self, return_file_name=False, **kwargs):
        matching = self.get_files_matching(**kwargs)
        if matching:
            if return_file_name:
                return list(matching)[0]
            return True
        return False

    def get_number_of_series(self):
        return len(self.get_files_matching())


def get_ctd_files_object(directory, use_stem=False, suffix=None):
    obj = CtdFiles(directory, use_stem=use_stem, suffix=suffix)
    obj.add_file_type(CtdFileTypeFormer())
    obj.check_directory()
    return obj


if __name__ == '__main__':
    c = get_ctd_files_object(r'C:\mw\temp_ctd_pre_system_data_root\data\2021\raw', suffix='.hex')

