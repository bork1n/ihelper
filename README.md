# iHelper (Instagram helper)
---

# Note: this is research project. Before using it please read Instagram's ToS

Arhitechture:
  AWS:
    DynamoDB: store info about data snapshot and snapshot itself(if it has small size)
    S3: stores big snapshots (to offload DynamoDB)
    Cognito: provides frontend read-only access to DynamoDB and S3
    SQS: queue for backend requests to fetch data
  FE:
    React, making queries to DynamoDB/S3
  BE:
    Python worker, who handles data update, listening to SQS

For AWS part to work, please:
  - create needed roles:
    - for BE(full access to dynamodb table, S3 and SQS)
    - for FE: cognito idedntity pool with role with RO access to DynamoDB and S3
  - allow CORS for S3

Helps people to get some analytics about their subscribers
