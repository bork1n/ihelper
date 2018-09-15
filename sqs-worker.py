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
from time import sleep

CONFIG_FILE = "settings.json"


def update_followers(payload):
    user = User(id=payload['user_id'],
                fetcher=fetcher, storage=storage, logger=logger)
    prev_ts = user.last_followers_ts()
    followers = user.update_followers(ts=int(start_time))

    if followers:
        process_request = {
            "command": "process_diff",
            "payload": {
                "user_id": payload['user_id'],
                "from": prev_ts,
                "to": int(start_time)
            }
        }
        sqs.send(process_request)
    else:
        logger.warning("followers are empty. Something wrong?")


def process_diff(payload):
    user = User(id=payload['user_id'],
                fetcher=fetcher, storage=storage, logger=logger)
    r = user.calc_diff(payload['from'], payload['to'])
    for i in 'added', 'removed':
        size = len(r[i].items())
        counter = 0
        for id, item in r[i].items():
            if counter % 30 == 0:
                logger.info("%s %d/%d", i, counter, size)
            counter += 1

            follow_update = {
                "producer": payload['user_id'],
                "action": 1 if i is 'added' else 0
            }
            logger.info("saving: follows/%s ts=%s val=%s",
                        item['id'], payload['to'], follow_update)

            storage.save_data(
                key='follows/' + item['id'], value=follow_update, ts=payload['to'])

            details = User(id=item['id'], fetcher=fetcher,
                           storage=storage, logger=logger).get_user_info(item)
            sleep(0.01)


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
        request = json.loads(msg[0].body)
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

    command = request.get('command')
    payload = request.get('payload')
    logger.info("got request for '%s' payload %s", command, payload)

    if command == 'update_followers':
        update_followers(payload)
    elif command == 'process_diff':
        process_diff(payload)
    else:
        logger.warning('invalid request %s', request)

    msg[0].delete()
    elapsed_time = int(time.time() - start_time)
    logger.info("request finished in {} seconds".format(elapsed_time))
