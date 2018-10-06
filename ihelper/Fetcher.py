import urllib
import urllib.parse
import json
import time
import random


URL_GRAPHQL = 'https://www.instagram.com/graphql/query/?query_hash={}&variables={}'
URL_PROFILE = "https://www.instagram.com/{}/?__a=1"


class Fetcher:
    def __init__(self, conn, logger):
        self.conn = conn
        self.logger = logger

    def pause_between(self, name):
        if name == 'graphql':
            time.sleep(5 + random.randint(2, 7))
        else:
            time.sleep(1 + random.randint(0, 2))

    def _json_get_request(self, url):
        data = self.conn.get(url)
        if data.status_code == 200:
            f = json.loads(data.text)
            return f
        elif data.status_code in [500, 502, 503]:
            self.logger.error('Insta is dead: %s, sleeping 10', data.status_code)
            time.sleep(10)
        elif data.status_code in [400, 429]:
            self.logger.info('Rate limited, sleeing 600')
            time.sleep(600)
        else:
            self.logger.info(data.__dict__)
        return None

    def graphql(self, query_hash, vars):
        self.pause_between('graphql')
        vars_encoded = urllib.parse.quote(vars)
        data = self._json_get_request(
            URL_GRAPHQL.format(query_hash, vars_encoded))
        if data:
            return data['data']['user']
        return None

    def user_info(self, login):
        self.pause_between('profile')
        data = self._json_get_request(URL_PROFILE.format(login))
        if data:
            return data['graphql']['user']
        return None
