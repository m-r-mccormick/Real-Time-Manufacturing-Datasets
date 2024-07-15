import json
import time
import signal
from datetime import datetime, timezone
import paho.mqtt.client as mqtt  # pip install paho-mqtt==1.6.1

mqtt_broker_host = "localhost"
mqtt_broker_port = 1883
mqtt_subscriptions = ["WVU/#"]  # Wildcard subscribe to everything in topic 'WVU/'
exit_flag = False

def on_connect(client: mqtt.Client, userdata, flags, rc):
    global mqtt_subscriptions
    if rc != 0:
        print('MQTT Connect unsuccessful, return code: {rc}', rc)
        return
    for subscription in mqtt_subscriptions:
        try:
            client.subscribe(subscription)
            print(f'Subscribed to {subscription}')
        except Exception as ex:
            print(f'Could not subscribe to {subscription}: {ex}')
            return

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

def on_message(client, userdata, msg):
    event = {
        'TIMESTAMP': datetime.now().astimezone(tz=timezone.utc).isoformat(timespec='milliseconds'),
        'TOPIC': msg.topic,
        'PAYLOAD': json.loads(msg.payload),
    }

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
        return

    print(f'event occured at {event_datetime} on topic {event_topic}:')

    handle_event(event_payload)


def signal_handler(signum, frame):
    global exit_flag

    if signum == 2:
        print("Exit Signal Received")
    else:
        print(f"Exit Signal Received: {signum}")

    exit_flag = True


def main():
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    client: mqtt.Client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_broker_host, mqtt_broker_port)
    client.loop_start()
    time.sleep(1)
    while client.is_connected():
        time.sleep(0.001)
        if exit_flag:
            break
    client.disconnect()
    print('Exited')


if __name__ == '__main__':
    main()
