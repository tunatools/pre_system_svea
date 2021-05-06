import json


def load_json(file_path):
    with open(file_path, 'r') as fid:
        return json.load(fid)


def save_json(data=None, file_path=None, indent=4):
    with open(file_path, 'w') as fid:
        json.dump(data, fid, indent=indent)