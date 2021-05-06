
from pre_system_svea.resource import Resources
from pre_system_svea import utils


class Operators:
    def __init__(self):
        self.file_path = Resources().operator_file

        self.data = {}
        self._load_file()

    def _load_file(self):
        self.data = utils.load_json(self.file_path)

    def _save_file(self):
        utils.save_json(self.data, self.file_path)

    def get_operator_list(self):
        return sorted(self.data)

    def get_full_name(self, short_name, default=None):
        return self.data.get(short_name, default)


if __name__ == '__main__':
    op = Operators()