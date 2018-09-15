import random

QUERY_FOLLOWERS = '149bef52a3b2af88c0fec37913fe1cbc'
# Doesn't make sense if >50
PER_ROUND = 50


class User:
    def __init__(self, id, fetcher, storage, logger):
        self.id = id
        self.fetcher = fetcher
        self.storage = storage
        self.logger = logger

    def calc_diff(self, old, followers):
        r = {}
        r['removed'] = {}
        r['added'] = {}
        removed = set(old) - set(followers)
        added = set(followers) - set(old)
        for item in removed:
            r['removed'][item] = old[item]
        for item in added:
            r['added'][item] = followers[item]
        return r

    def generate_query(self, first, after=None):
        vars = '"id":"{}","first":{}'.format(self.id, first)
        if after is not None:
            vars += ',"after":"{}"'.format(after)
        return "{{{}}}".format(vars)

    def get_user_info(self, item):
        details = self.storage.load_data('profiles/' + str(self.id))
        if not details:
            details = self.fetcher.user_info(item['username'])
            self.storage.save_data('profiles/' + str(item['id']), details)
        return details

    def last_followers_ts(self):
        return self.storage.get_last_ts('followers/' + str(self.id))

    def get_followers(self, ts=None):
        old = self.storage.load_data('followers/' + str(self.id), ts=None)
        if not old:
            old = {}
        return old

    def update_followers(self):
        fetch = True
        num = 30
        followers = {}
        after = None
        got = 0
        while fetch:
            q = self.generate_query(num, after)
            num = PER_ROUND + random.randint(0, 5)
            data = self.fetcher.graphql(QUERY_FOLLOWERS, q)
            if data:
                edges = data['edge_followed_by']
                total = edges['count']
                for user in edges['edges']:
                    user_data = user['node']
                    followers[user_data['id']] = user_data
                    got += 1
                self.logger.info("got %4d of %4d", got, total)
                after = edges['page_info']['end_cursor']
                if not edges['page_info']['has_next_page']:
                    break
        if followers:
            self.storage.save_data('followers/' + self.id, followers)

        return followers
