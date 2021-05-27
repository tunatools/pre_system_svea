from pathlib import Path

from pre_system_svea.resource import Resources

import math
import numpy as np
import pandas as pd


class StationMethods:
    def get_closest_station(self, *args, **kwargs):
        raise NotImplementedError

    def get_proper_station_name(self, *args, **kwargs):
        raise NotImplementedError

    def get_station_info(self, *args, **kwargs):
        raise NotImplementedError

    def get_station_list(self, *args, **kwargs):
        raise NotImplementedError

    def get_position(self, *args, **kwargs):
        raise NotImplementedError


class StationsMatprogram(StationMethods):

    def __init__(self, root_directory=None):
        self.station_name_list = []
        self._resources = Resources(root_directory=root_directory)
        self._station_file = StationFile(self._resources.station_file)
        self._load_station_filter_file()

    def _load_station_filter_file(self):
        self.station_name_list = []
        with open(self._resources.station_filter_file) as fid:
            for line in fid:
                name = line.strip()
                if not name:
                    continue
                if not self._station_file.get_station_info(name):
                    print(f'Could not find station infor for station: {name}')
                    continue
                self.station_name_list.append(name)
        self.station_name_list.sort()

    def get_closest_station(self, *args, **kwargs):
        return self._station_file.get_closest_station(*args, *kwargs)

    def get_proper_station_name(self, *args, **kwargs):
        return self._station_file.get_proper_station_name(*args, *kwargs)

    def get_station_info(self, *args, **kwargs):
        return self._station_file.get_station_info(*args, *kwargs)

    def get_station_list(self, *args, **kwargs):
        return self.station_name_list

    def get_position(self, *args, **kwargs):
        return self.get_position(*args, *kwargs)


class StationFile(StationMethods):
    def __init__(self, file_path=None):

        self.file_path = Path(file_path)

        self._station_synonyms = {}

        self.lat_col = 'LATITUDE_WGS84_SWEREF99_DD'
        self.lon_col = 'LONGITUDE_WGS84_SWEREF99_DD'
        self.depth_col = 'WADEP'
        self.station_col = 'STATION_NAME'

        self._df = None
        self._load_file()

    def _load_file(self):
        self._df = pd.read_csv(self.file_path, sep='\t', encoding='cp1252')
        self._df['MEDIA'] = self._df['MEDIA'].fillna('')
        self._df[self.depth_col] = self._df[self.depth_col].fillna('')
        self._df = self._df[self._df['MEDIA'].str.contains('Vatten')].reset_index()

    def _create_station_synonyms(self):
        for name, synonym_string in zip(self._df[self.station_col], self._df['SYNONYM_NAMES'].astype(str)):
            self._station_synonyms[name.upper()] = name
            synonym_string = synonym_string.strip()
            if not synonym_string:
                continue
            synonyms = synonym_string.split('<or>')
            for syn in synonyms:
                self._station_synonyms[syn.upper()] = name

    def _add_cols_to_station_info(self, station_info):
        station_info['lat'] = station_info[self.lat_col]
        station_info['lon'] = station_info[self.lon_col]
        station_info['depth'] = str(station_info[self.depth_col])
        station_info['station'] = station_info[self.station_col]

    def get_closest_station(self, lat, lon):
        if lat is None or lon is None:
            return None
        dist = self._df.apply(lambda x: distance_to_station((lat, lon),
                                                           (x[self.lat_col],
                                                            x[self.lon_col])), axis=1)
        min_dist = min(dist)
        index = np.where(dist == min_dist)
        # print('LAT', lat)
        # print('LON', lon)
        # print('INDEX', index)
        df = self._df.loc[index[0]]
        station_info = dict(zip(df.columns, df.values[0]))
        station_info['distance'] = min_dist
        station_info['acceptable'] = min_dist <= station_info['OUT_OF_BOUNDS_RADIUS']
        self._add_cols_to_station_info(station_info)
        return station_info

    def get_proper_station_name(self, synonym):
        """
        Returns the proper name for the station given in "synonym".
        :param synonym: str
        :return:
        """
        synonym = synonym.strip().upper()
        if not self._station_synonyms:
            self._create_station_synonyms()
        return self._station_synonyms.get(synonym, None)

    def get_station_info(self, station_name):
        name = self.get_proper_station_name(station_name)
        if not name:
            return None
        station_info = self._df.loc[self._df['STATION_NAME'] == name].iloc[0].to_dict()
        self._add_cols_to_station_info(station_info)
        return station_info

    def get_station_list(self):
        return sorted(self._df['STATION_NAME'])

    def get_position(self, station_name):
        station_info = self.get_station_info(station_name)
        if not station_info:
            return None
        return station_info.get('lat'), station_info.get('lon')
    

class Stations(StationsMatprogram):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def distance_to_station(pos1, pos2):
    """
    http://www.johndcook.com/blog/python_longitude_latitude/
    Returns distance in meters
    """
    lat1, lon1 = pos1
    lat2, lon2 = pos2
    if lat1 == lat2 and lon1 == lon2:
        return 0
    degrees_to_radians = math.pi / 180.0

    phi1 = (90.0 - lat1) * degrees_to_radians
    phi2 = (90.0 - lat2) * degrees_to_radians

    theta1 = lon1 * degrees_to_radians
    theta2 = lon2 * degrees_to_radians

    cos = (math.sin(phi1) * math.sin(phi2) * math.cos(theta1 - theta2) +
           math.cos(phi1) * math.cos(phi2))

    # distance = math.acos(cos) * 6373 * 1000  # 6373 ~ radius of the earth (km) * 1000 m
    distance = math.acos(cos) * 6363 * 1000  # 6373 ~ radius of the earth (km) * 1000 m

    return round(distance)


if __name__ == '__main__':
    s = Stations()
    info = s.get_closest_station(57.0667, 19.83)

