import boto3
import json


class SQSClient:
    def __init__(self, profile, queue):
        session = boto3.Session(profile_name=profile)
        self.queue = session.resource(
            'sqs').get_queue_by_name(QueueName=queue)

    def recieve(self):
        return self.queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=20)

    def send(self, message):
        return self.queue.send_message(MessageBody=json.dumps(message))
