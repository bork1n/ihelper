#!/usr/bin/env python
import sys
import json
from ihelper.InstaConnection import InstaConnection
from ihelper.Fetcher import Fetcher
from ihelper.User import User
import ihelper.Storage
CONFIG_FILE = "settings.json"


with open(CONFIG_FILE) as f:
    config = json.load(f)

storage = ihelper.Storage.Storage(backend=ihelper.Storage.FileBackend())
conn = InstaConnection(
    accounts=config["connection.accounts"]
)
fetcher = Fetcher(conn=conn)
user = User(id=INSTA_ID, fetcher=fetcher, storage=storage)

#followers, old = old, followers

old = user.get_followers()
followers = user.update_followers(progress_fn=lambda x: print(x))

if not followers:
    print("followers are empty")
    sys.exit()


r = user.calc_diff(old, followers)
for i in 'added', 'removed':
    print(i)
    for id, item in r[i].items():
        details = User(id=item['id'], fetcher=fetcher,
                       storage=storage).get_user_info(item)
        if not details:
            details = item
        # if details['edge_follow']['count'] < 2000:
        #     continue
        print(
            "https://instagram.com/{}\t\"{}\"\t{} clients vs {} subs "
            .format(details['username'],
                    details['full_name'],
                    details['edge_followed_by']['count'],
                    details['edge_follow']['count']))
    print('')
