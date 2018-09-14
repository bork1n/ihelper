import boto3


class SQSClient:
    def __init__(self, profile, queue):
        session = boto3.Session(profile_name=profile)
        self.queue = session.resource(
            'sqs').get_queue_by_name(QueueName=queue)

    def recieve(self):
        return self.queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=20)
