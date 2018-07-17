import gzip
import json

from os import listdir
from os.path import isfile, join
import time


class Storage:
    """
    load_data - loads LATEST data for provided key
    save_data - saves data for provided key with current TS
    """
    DIR = "jsons"

    def _get_last_file(self, prefix):
        path = prefix.split('/')
        key = path.pop()
        dir = "/".join(path)
        prefix_dir = join(self.DIR, dir)
        files = [join(prefix_dir, f) for f in listdir(prefix_dir) if isfile(
            join(prefix_dir, f)) and f.startswith(key)]
        if not files:
            return None
        files.sort()
        return files[-1]

    def load_data(self, key):
        file = self._get_last_file(key)
        if file is None:
            return None

        with gzip.open(file) as f:
            data = json.loads(f.read().decode('utf-8'))

        return data

    def save_data(self, key, value):
        with gzip.open(join(self.DIR, key + "-" + str(int(time.time())) + ".json.gz"), 'w') as f:
            f.write(json.dumps(value).encode('utf-8'))
