from ctd_processing import xmlcon
import pathlib


class SensorInfo:
    def __init__(self):
        self._config_file = None
        self._stem = None
        self._data = ['This', 'is', 'a', 'test', 'file']

    def create_file_from_config_file(self, config_file):
        """
        Created a sensor info file with information in given XMLCON file.
        The file is created at the same location as the config file.
        """
        self._config_file = pathlib.Path(config_file)
        self._stem = self._config_file.stem
        self._save_file()

    def _save_file(self):
        save_path = pathlib.Path(self._config_file.parent, f'{self._stem}.sensorinfo')
        with open(save_path, 'w') as fid:
            fid.write('\n'.join(self._data))


if __name__ == '__main__':
    file_path = r'C:\mw\temp_ctd_pre_system_data_root\raw/SBE09_1387_20210413_1113_77SE_00_0278.XMLCON'
    x = xmlcon.XMLCONfile(file_path)
    for item in x.get_sensor_info():
        print(item)