import gzip
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from boto3.dynamodb.types import Binary

from os import listdir
from os.path import isfile, join
import time
import abc


class Storage:
    """
        Base class for loading and saving data.
        Handles encoding steps and forwads to backend-specific implementations.
        Accepts backend object, with can do save and load.
        Backend should raise FileNotFoundError in case of data can not be found
    """

    def __init__(self, backend=None):
        if not backend:
            backend = StorageBackend()
        if not isinstance(backend, BackendAbstract):
            raise TypeError(
                'backend argument is not derived from BackendAbstract')
        self.backend = backend

    def _filename(self, key, ts):
        return "{}-{}.json.gz".format(key, ts)

    def load_data(self, key, ts=None):
        try:
            data = self.backend.load(key, ts)
        except FileNotFoundError:
            return None

        data = json.loads(gzip.decompress(data).decode('utf-8'))
        return data

    def save_data(self, key, value, ts=None):
        if not ts:
            ts = int(time.time())
        content = gzip.compress(json.dumps(value).encode('utf-8'))
        return self.backend.save(key=key, value=content, ts=ts, filename=self._filename(key, ts))


class BackendAbstract(object, metaclass=abc.ABCMeta):
    """
    Abstract class for all backends.
    Enforces implementing of interface methods load and save
    """
    @abc.abstractmethod
    def load(self, key):
        raise NotImplementedError('Must define load()')

    @abc.abstractmethod
    def save(self, key, content, ts):
        raise NotImplementedError('Must define save()')


DB_MAX_SIZE = 6 * 1024


class DynamoDBBackend(BackendAbstract):

    def __init__(self, profile, table, bucket, db_max_size=DB_MAX_SIZE):
        session = boto3.Session(profile_name=profile)
        self.table = session.resource('dynamodb').Table(table)
        self.s3 = session.resource('s3').Bucket(bucket)
        self.db_max_size = db_max_size

    def load(self, key, ts=None):
        args = {
            "KeyConditionExpression": Key('key').eq(key),
            "Limit": 1,
            "ScanIndexForward": False
        }
        if ts:
            args['KeyConditionExpression'] = args['KeyConditionExpression'] & Key(
                'ts').eq(ts)
        response = self.table.query(**args)
        items = response['Items']

        if not items:
            raise FileNotFoundError

        data = items[0]['val']

        if type(data) == str and data.startswith(key):
            data = self.s3.Object(data).get()['Body'].read()
        else:
            data = data.value

        return data

    def save(self, key, value, ts, filename):

        if len(value) > self.db_max_size:
            self._upload_to_s3(filename, value)
            val = filename
        else:
            val = Binary(value)

        self.table.put_item(Item={
            "key": key,
            "ts": ts,
            "val": val
        })

    def _upload_to_s3(self, key, value):
        self.s3.put_object(
            Body=value, Key=key, ContentType="application/json", ContentEncoding="gzip")


class FileBackend(BackendAbstract):

    def __init__(self, dir="jsons"):
        self.dir = dir

    def _get_last_file(self, prefix):
        path = prefix.split('/')
        key = path.pop()
        dir = "/".join(path)
        prefix_dir = join(self.dir, dir)
        files = [join(prefix_dir, f) for f in listdir(prefix_dir) if isfile(
            join(prefix_dir, f)) and f.startswith(key)]
        if not files:
            raise FileNotFoundError
        files.sort()
        return files[-1]

    def load(self, key):
        filename = self._get_last_file(key)
        with open(filename, 'rb') as f:
            value = f.read()
        return value

    def save(self, key, value, ts, filename):
        filename = join(self.dir, filename)
        with open(filename, 'wb') as f:
            f.write(value)
