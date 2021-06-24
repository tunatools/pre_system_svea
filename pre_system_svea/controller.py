from pre_system_svea.operator import Operators
from pre_system_svea.station import Stations
from pre_system_svea.ship import Ships

from pre_system_svea.ctd_config import CtdConfig
from pre_system_svea.ctd_files import get_ctd_files_object
from  pre_system_svea import utils

import threading
import subprocess
from pathlib import Path
import datetime
import os
import psutil

from ctd_processing import psa
from ctd_processing import xmlcon


class Controller:

    def __init__(self, ctd_config_root_directory=None, ctd_data_root_directory=None):
        self.ctd_config = None
        self.ctd_files = None

        self.__ctd_config_root_directory = None
        self.__ctd_data_root_directory = None
        self.__ctd_data_root_directory_server = None

        self.ctd_config_root_directory = ctd_config_root_directory
        self.ctd_data_root_directory = ctd_data_root_directory

        self.operators = Operators()
        self.stations = Stations()
        self.ships = Ships()

    @property
    def ctd_config_root_directory(self):
        return self.__ctd_config_root_directory

    @ctd_config_root_directory.setter
    def ctd_config_root_directory(self, directory):
        if not directory:
            return
        directory = Path(directory)
        if not directory.exists():
            return
        self.__ctd_config_root_directory = directory
        self.ctd_config = CtdConfig(directory)

    @property
    def ctd_data_root_directory(self):
        return self.__ctd_data_root_directory

    @ctd_data_root_directory.setter
    def ctd_data_root_directory(self, directory=None):
        if directory is None:
            return
        directory = Path(directory)
        if directory.name != 'data':
            directory = Path(directory, 'data')
        if not directory.exists():
            os.makedirs(directory)
        self.__ctd_data_root_directory = directory

    @property
    def ctd_data_root_directory_server(self):
        return self.__ctd_data_root_directory_server

    @ctd_data_root_directory_server.setter
    def ctd_data_root_directory_server(self, directory=None):
        if directory is None:
            return
        directory = Path(directory)
        if directory.name != 'data':
            directory = Path(directory, 'data')
        if not directory.exists():
            os.makedirs(directory)
        self.__ctd_data_root_directory_server = directory

    def get_station_list(self):
        return self.stations.get_station_list()

    def get_operator_list(self):
        return self.operators.get_operator_list()

    def get_closest_station(self, lat, lon):
        return self.stations.get_closest_station(lat, lon)

    def get_station_info(self, station_name):
        return self.stations.get_station_info(station_name)

    def _get_running_programs(self):
        program_list = []
        for p in psutil.process_iter():
            program_list.append(p.name())
        return program_list

    def run_seasave(self):
        if 'Seasave.exe' in self._get_running_programs():
            raise ChildProcessError('Seasave is already running!')
        t = threading.Thread(target=self._subprocess_seasave)
        t.daemon = True  # close pipe if GUI process exits
        t.start()

    def _subprocess_seasave(self):
        subprocess.run([str(self.ctd_config.seasave_program_path), f'-p={self.ctd_config.seasave_psa_main_file}'])

    def get_xmlcon_path(self, instrument):
        if instrument.lower() in ['sbe09', 'sbe9']:
            file_path = str(self.ctd_config.seasave_sbe09_xmlcon_file)
        elif instrument.lower() == 'sbe19':
            file_path = str(self.ctd_config.seasave_sbe19_xmlcon_file)
        else:
            raise ValueError(f'Incorrect instrument number: {instrument}')
        return file_path
    
    def get_seasave_psa_path(self):
        return self.ctd_config.seasave_psa_main_file

    def _get_xmlcon_object(self, instrument):
        xmlcon_file_path = self.get_xmlcon_path(instrument)
        obj = xmlcon.XMLCONfile(xmlcon_file_path)
        return obj

    def _get_main_psa_object(self):
        return psa.SeasavePSAfile(self.ctd_config.seasave_psa_main_file)

    def update_xmlcon_in_main_psa_file(self, instrument):
        xmlcon_file_path = self.get_xmlcon_path(instrument)
        psa_obj = self._get_main_psa_object()
        psa_obj.xmlcon_path = xmlcon_file_path
        psa_obj.save()

    def update_main_psa_file(self,
                             instrument=None,
                             depth=None,
                             nr_bins=None,
                             cruise_nr=None,
                             ship_code=None,
                             serno=None,
                             station='',
                             operator='',
                             year=None,
                             position=None):

        if not year:
            year = str(datetime.datetime.now().year)

        if instrument:
            print('INSTRUMENT', instrument)
            self.update_xmlcon_in_main_psa_file(instrument)

        hex_file_path = self._get_hex_file_path(instrument=instrument,
                                                cruise_nr=cruise_nr,
                                                ship_code=ship_code,
                                                serno=serno)
        directory = hex_file_path.parent
        if not directory.exists():
            os.makedirs(directory)

        psa_obj = self._get_main_psa_object()
        psa_obj.data_path = hex_file_path

        if depth:
            psa_obj.display_depth = depth

        if nr_bins:
            psa_obj.nr_bins = nr_bins

        if station:
            psa_obj.station = station

        if operator:
            psa_obj.operator = operator

        if ship_code:
            psa_obj.ship = self.ships.get_code(ship_code)

        if cruise_nr:
            psa_obj.cruise = f'SMHI-{cruise_nr.zfill(2)}-{year}'

        if position:
            psa_obj.position = position

        psa_obj.save()

    def _get_hex_file_path(self, instrument=None, cruise_nr=None, ship_code=None, serno=None):
        if not all([
            instrument,
            cruise_nr,
            ship_code,
            serno
        ]):
            raise ValueError('Missing information')
        # Builds the file stem to be as the name for the processed file.
        # sbe09_1387_20200207_0801_77_10_0120
        now = datetime.datetime.now()
        time_str = now.strftime('%Y%m%d_%H%M')
        year = str(now.year)

        file_stem = '_'.join([
            instrument,
            self.get_instrument_serial_number(instrument),
            time_str,
            self.ships.get_code(ship_code),
            cruise_nr.zfill(2),
            serno
        ])
        
        directory = Path(self.ctd_data_root_directory, 'raw')
        file_path = Path(directory, f'{file_stem}.hex')
        return file_path

    def get_sensor_info_in_xmlcon(self, instrument):
        xmlcon = self._get_xmlcon_object(instrument)
        return xmlcon.get_sensor_info()

    def get_instrument_serial_number(self, instrument):
        xmlcon = self._get_xmlcon_object(instrument)
        return xmlcon.serial_number

    def _get_root_data_path(self, server=False):
        root_path = self.ctd_data_root_directory
        if server:
            root_path = self.ctd_data_root_directory_server
        if not root_path:
            # return ''
            raise NotADirectoryError
        return root_path

    def series_exists(self, **kwargs):
        root_path = self._get_root_data_path(server=server)
        ctd_files_obj = get_ctd_files_object(root_path, use_stem=True)
        return ctd_files_obj.series_exists(**kwargs)

    def get_next_serno(self, server=False, **kwargs):
        print('get_next_serno')
        root_path = self._get_root_data_path(server=server)
        ctd_files_obj = get_ctd_files_object(root_path, use_stem=True)
        return ctd_files_obj.get_next_serno(**kwargs)


if __name__ == '__main__':
    root_directory = f'C:\mw\git\ctd_config'
    c = Controller(ctd_config_root_directory=root_directory)
    c.update_main_psa_file('sbe09')
    # c.run_seasave()
