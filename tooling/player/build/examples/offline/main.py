import json
from datetime import datetime


def handle_event(event_payload: dict):
    if 'Observation' in event_payload:
        observation: dict = event_payload['Observation']

        # This is the timestamp from the PLC or Edge Device
        #   (which might not be correct if the PLC date is not configured correctly)
        observation_datetime: datetime = datetime.fromisoformat(observation['Timestamp'])

        observation_value: object = observation['Value']
        if 'Description' in event_payload:
            observation_description = event_payload['Description']
        observation_description = None
        print(f'\tValue "{observation_value}" observed at "{observation_datetime}"')
        if observation_description is not None:
            print(f'\tDescription: "{observation_description}"')

    if 'Transaction' in event_payload:
        transaction: dict = event_payload['Transaction']

        # This is the timestamp when Change Data Capture (CDC) occurred
        #   (which might not be the exact time that the database transaction occurred)
        transaction_datetime: datetime = datetime.fromisoformat(transaction['Timestamp'])

        transaction_database = transaction['Database']
        transaction_operation = transaction['Operation']
        transaction_table = transaction['Table']
        transaction_rowid = None
        if 'RowId' in transaction:
            transaction_rowid = transaction['RowId']
        print(f'\tDatabase {transaction_database} operation {transaction_operation} occurred on '
              f'table {transaction_table}')
        if transaction_rowid is not None:
            print(f'\tRowId: {transaction_rowid}')
        pass


file_path = 'docker/player/datasets/RTMD Proof of Concept Dataset.jsonl'
with open(file_path, 'r') as file:
    print(f'Reading {file_path}...')

    line = file.readline()
    if not line.startswith('RTMDv'):
        raise Exception(f'RTMD header missing')
    version_parts = [int(p) for p in line.lstrip('RTMDv').rstrip('\n').split('.')]
    major_version = version_parts[0]
    minor_version = version_parts[1]
    if major_version != 0:
        raise Exception(f'Incompatible RTMD file major version "{line}"')
    if minor_version >= 1:
        print('Warning: RTMD file minor version is newer than this codebase')

    while True:
        line = file.readline()
        if not line:
            break  # End of file
        event = json.loads(line)

        # Make sure event matches the required event model
        if 'PAYLOAD' not in event:
            print('Error: PAYLOAD not defined in event')
            raise Exception('PAYLOAD not defined in event')
        event_payload: dict = event['PAYLOAD']

        if 'TIMESTAMP' not in event:
            print('Error: TIMESTAMP not defined in event')
            raise Exception('TIMESTAMP not defined in event')
        # This is when the data was received from the MQTT broker (not the device (PLC) timestamp)
        event_timestamp: str = event['TIMESTAMP']
        event_datetime: datetime = datetime.fromisoformat(event_timestamp)

        if 'TOPIC' not in event:
            print('Error: TOPIC not defined in event')
            raise Exception('TOPIC not defined in event')
        event_topic: str = event['TOPIC']

        # Skip Video Topics
        if event['TOPIC'].endswith('Video'):
            continue

        print(f'event occurred at {event_datetime} on topic {event_topic}:')

        handle_event(event_payload)

    print(f'Read {file_path} Complete')
