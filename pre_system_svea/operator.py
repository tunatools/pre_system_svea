import json

from pre_system_svea.resource import Resources


class Operators:
    def __init__(self):
        self.resources = Resources()
        self.file_path = self.resources.operators

        self.data = {}
        self._load_file()

    def _load_file(self):
        with open(self.file_path, 'r') as fid:
            self.data = json.load(fid)

    def _save_file(self):
        with open(self.file_path, 'w') as fid:
            json.dump(self.data, fid, indent=4)

    def get_operator_list(self):
        return sorted(self.data)

    def get_full_name(self, short_name, default=None):
        return self.data.get(short_name, default)


if __name__ == '__main__':
    op = Operators()