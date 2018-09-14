#!/usr/bin/env python
import sys
import time
import json
import logging
from ihelper.InstaConnection import InstaConnection
from ihelper.Fetcher import Fetcher
import ihelper.Storage
from ihelper.User import User
from SQSClient import SQSClient

CONFIG_FILE = "settings.json"


with open(CONFIG_FILE) as f:
    config = json.load(f)


logging.basicConfig(level=logging.CRITICAL,
                    format='%(asctime)s %(levelname)s %(message)s',)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


ddb_backend = ihelper.Storage.DynamoDBBackend(
    profile=config["dynamodb.profile"], table=config["dynamodb.table"], bucket=config["s3.bucket"])
storage = ihelper.Storage.Storage(backend=ddb_backend)


conn = InstaConnection(
    accounts=config["connection.accounts"], logger=logger
)
fetcher = Fetcher(conn=conn, logger=logger)
sqs = SQSClient(profile=config["sqs.profile"], queue=config["sqs.queue"])

while True:
    msg = None
    try:
        msg = sqs.recieve()
    except KeyboardInterrupt:
        sys.exit()
    except:
        pass

    if not msg:
        continue

    start_time = time.time()

    try:
        payload = json.loads(msg[0].body)
    except AttributeError as e:
        logger.info("msg[0] has no body attribute. WTF? removing.")
        msg[0].delete()
        continue
    except Exception as e:
        logger.exception(e)
        logger.info("cant parse JSON: {} (error: {}), removing message".format(
            msg[0].body, e))
        msg[0].delete()
        continue

    logger.info('got request for %s', payload)
    user = User(id=payload['update_followers'],
                fetcher=fetcher, storage=storage, logger=logger)

    old = user.get_followers()
    followers = user.update_followers()

    if not followers:
        logger.info("followers are empty. Something wrong?")
        continue

    r = user.calc_diff(old, followers)
    for i in 'added', 'removed':
        for id, item in r[i].items():
            details = User(id=item['id'], fetcher=fetcher,
                           storage=storage, logger=logger).get_user_info(item)
    msg[0].delete()
    elapsed_time = int(time.time() - start_time)
    logger.info("request finished in {} seconds".format(elapsed_time))
