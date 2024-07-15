import json
import os
import time
import signal
import queue
from datetime import datetime, timezone
import paho.mqtt.client as mqtt  # pip install paho-mqtt==1.6.1

import driver

exit_flag = False

env_error = False

mqtt_broker_host = os.getenv('MQTT_BROKER_HOST')
if mqtt_broker_host is None:
    print('Error: Environment Variable MQTT_BROKER_HOST not defined')
    env_error = True
print(f'mqtt broker host: {mqtt_broker_host}')

mqtt_broker_port = os.getenv('MQTT_BROKER_PORT')
try:
    mqtt_broker_port = int(mqtt_broker_port)
except Exception as ex:
    print('Error: Environment Variable MQTT_BROKER_PORT is not an int')
    env_error = True
if mqtt_broker_port is None:
    print('Error: Environment Variable MQTT_BROKER_PORT not defined')
    env_error = True
print(f'mqtt broker port: {mqtt_broker_port}')

mqtt_subscription = os.getenv('MQTT_SUBSCRIPTION')
if mqtt_subscription is None:
    print('Error: Environment Variable MQTT_SUBSCRIPTION not defined')
    env_error = True
print(f'mqtt subscription: {mqtt_subscription}')

rtmd_database_name = os.getenv('RTMD_DATABASE_NAME')
if rtmd_database_name is None:
    print('Error: Environment Variable RTMD_DATABASE_NAME not defined')
    env_error = True
print(f'rtmd database name: {rtmd_database_name}')

mariadb_host = os.getenv('MARIADB_HOST')
if mariadb_host is None:
    print('Error: Environment Variable MARIADB_HOST not defined')
    env_error = True
print(f'mariadb host: {mariadb_host}')

mariadb_port = os.getenv('MARIADB_PORT')
try:
    mariadb_port = int(mariadb_port)
except Exception as ex:
    print('Error: Environment Variable MARIADB_PORT is not an int')
    env_error = True
if mariadb_port is None:
    print('Error: Environment Variable MARIADB_PORT not defined')
    env_error = True
print(f'mariadb port: {mariadb_port}')

mariadb_database = os.getenv('MARIADB_DATABASE')
if mariadb_database is None:
    print('Error: Environment Variable MARIADB_DATABASE not defined')
    env_error = True
print(f'mariadb database {mariadb_database}')

mariadb_user = os.getenv('MARIADB_USER')
if mariadb_user is None:
    print('Error: Environment Variable MARIADB_USER not defined')
    env_error = True
print(f'mariadb user: {mariadb_user}')

mariadb_password = os.getenv('MARIADB_PASSWORD')
if mariadb_password is None:
    print('Error: Environment Variable MARIADB_PASSWORD not defined')
    env_error = True
print(f'mariadb password: [redacted]')

if env_error:
    time.sleep(5)
    raise Exception('Environment Variables not defined')

mqtt_subscriptions = [mqtt_subscription]
db: driver.MesDriver | None = None
fully_connected = False
event_queue: queue.Queue[dict] = queue.Queue()


def process_event(event: dict):
    # Make sure event matches the required event model
    if 'PAYLOAD' not in event:
        print('Error: PAYLOAD not defined in event')
        return
    event_payload: dict = event['PAYLOAD']

    if 'TIMESTAMP' not in event:
        print('Error: TIMESTAMP not defined in event')
        return
    # This is when the data was received from the MQTT broker (not the device (PLC) timestamp)
    event_timestamp: str = event['TIMESTAMP']
    event_datetime: datetime = datetime.fromisoformat(event_timestamp)

    if 'TOPIC' not in event:
        print('Error: TOPIC not defined in event')
        return
    event_topic: str = event['TOPIC']

    # Only process Transactions
    if 'Transaction' not in event_payload:
        return
    transaction: dict = event_payload['Transaction']

    # Only process Transactions from the specified RTMD database
    if 'Database' not in transaction:
        return
    if transaction['Database'] != rtmd_database_name:
        return

    # Make sure operation and table are specified
    if 'Operation' not in transaction:
        print('Error: Operation not defined in transaction')
        return
    operation = transaction['Operation']
    if 'Table' not in transaction:
        print('Error: Table not defined in transaction')
        return
    table = transaction['Table']

    print(f'{rtmd_database_name} database {operation} operation on table {table} received at '
          f'{event_datetime}:')

    try:
        if operation == 'Drop':
            # db.table_drop_if_exists(table)
            return

        columns = transaction['Columns']

        if operation == 'Create':
            db.table_create_if_doesnt_exist(table, columns)
            return

        row_id = transaction['RowId']

        if operation == 'Delete':
            db.row_delete(table, row_id)
            return

        row = transaction['Row']

        if operation == 'Insert':
            db.row_replace_into(table, row_id, row)
            return

        if operation == 'Update':
            db.row_replace_into(table, row_id, row)
            return

        raise Exception("Unknown Operation")
    except Exception as ex:
        print(f'Exception Processing Transaction: {ex}')


def on_connect(client: mqtt.Client, userdata, flags, rc):
    global mqtt_subscriptions
    if rc != 0:
        print('MQTT Connect unsuccessful, return code: {rc}', rc)
        return
    for subscription in mqtt_subscriptions:
        try:
            client.subscribe(subscription, 2)
            print(f'Subscribed to {subscription}')
        except Exception as ex:
            print(f'Could not subscribe to {subscription}: {ex}')
            return


def on_message(client, userdata, msg):
    try:
        json_payload = json.loads(msg.payload)
    except Exception as ex:
        print(f'Error: Could not decode json payload: {ex}')
        return

    event = {
        'TIMESTAMP': datetime.now().astimezone(tz=timezone.utc).isoformat(timespec='milliseconds'),
        'TOPIC': msg.topic,
        'PAYLOAD': json.loads(msg.payload),
    }

    # Make sure event matches the required event model
    if 'PAYLOAD' not in event:
        print('Error: PAYLOAD not defined in event')
        return
    event_payload: dict = event['PAYLOAD']

    if 'TIMESTAMP' not in event:
        print('Error: TIMESTAMP not defined in event')
        return

    if 'TOPIC' not in event:
        print('Error: TOPIC not defined in event')
        return

    # Only process Transactions
    if 'Transaction' not in event_payload:
        return

    if fully_connected:
        process_event(event)
    else:
        event_queue.put(event)
        print(f'Enqueued event from topic {msg.topic}\n')


def signal_handler(signum, frame):
    global exit_flag

    if signum == 2:
        print("Exit Signal Received")
    else:
        print(f"Exit Signal Received: {signum}")

    exit_flag = True


def main():
    global db
    global fully_connected

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    c_i = 0
    c_i_max = 15
    while True:
        client: mqtt.Client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        try:
            client.connect(mqtt_broker_host, mqtt_broker_port)
            break
        except Exception as ex:
            print(f"Could not connect to {mqtt_broker_host}:{mqtt_broker_port} MQTT broker, "
                  f"attempt {c_i} of {c_i_max}: {ex}")
            c_i += 1

        if c_i < c_i_max:
            time.sleep(1)
            continue

        print(f"Error: Could not connect to {mqtt_broker_host}:{mqtt_broker_port} MQTT broker")
        exit(1)

    client.loop_start()
    print("Connected to MQTT broker")

    while True:
        db = driver.MesDriver(mariadb_host, mariadb_database, mariadb_user, mariadb_password,
                              mariadb_port)
        try:
            db.connect()
            break
        except Exception as ex:
            print(f"Could not connect to {mariadb_database} database, attempt {c_i} of {c_i_max}: {ex}")
            c_i += 1

        if c_i < c_i_max:
            time.sleep(1)
            continue

        print(f"Error: Could not connect to {mariadb_database} database")
        exit(1)

    print("Connected to MES database")

    # Process events which were received before connecting to the database
    while not event_queue.empty():
        event = event_queue.get_nowait()
        event_topic = event['TOPIC']
        process_event(event)
        print(f'Processed enqueued event from topic {event_topic}')
        # Avoid overloading the database
        time.sleep(0.001)

    fully_connected = True

    # Process any events which were added to the queue right before fully_connected was set
    while not event_queue.empty():
        event = event_queue.get_nowait()
        event_topic = event['TOPIC']
        process_event(event)
        print(f'Processed enqueued event from topic {event_topic} after fully connected')

    while True:
        if not client.is_connected():
            print(f'\nError: Disconnected from MQTT broker.\n')
            client.disconnect()
            db.disconnect()
            return

        if not db.is_connected():
            print(f'\nError: Disconnected from database.\n')
            client.disconnect()
            db.disconnect()
            return

        time.sleep(0.001)

        if exit_flag:
            break

    client.disconnect()
    print('Exited')


if __name__ == '__main__':
    main()
