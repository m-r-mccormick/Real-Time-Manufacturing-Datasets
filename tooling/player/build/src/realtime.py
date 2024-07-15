import json
import os
import time
from datetime import datetime, timezone
from queue import Queue
from threading import Thread
from typing import TextIO, List
import paho.mqtt.client as mqtt  # pip install paho-mqtt==1.6.1


major_file_version = 0
minor_file_version = 1


class _KEYS:
    timestamp = 'TIMESTAMP'
    payload = 'PAYLOAD'
    topic = 'TOPIC'


class Player:

    def __init__(self, file_path: str, host: str, port: int):
        if not isinstance(file_path, str):
            raise TypeError('file_path must be a str')
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f'file_path {file_path} must be a file')
        if not file_path.endswith('.jsonl'):
            raise ValueError(f'file_path {file_path} must be a .jsonl file')
        self._file_path = file_path

        if not isinstance(host, str):
            raise TypeError('host must be a string')
        self._host = host

        if not isinstance(port, int):
            raise TypeError('port must be an int')
        self._port = port

        self._read_thread: Thread | None = None
        self._read_thread_exit_flag = False
        self._read_thread_start_of_file = False
        self._read_thread_end_of_file = False
        self._transmit_thread: Thread | None = None
        self._transmit_thread_exit_flag = False
        self._buffer: Queue[dict] = Queue(100)

    def is_open(self):
        return (self._read_thread is not None) and (self._transmit_thread is not None)

    def start(self):
        if self._read_thread is not None:
            raise Exception('Player is already open')
        if self._transmit_thread is not None:
            raise Exception('Player is already open')

        file: TextIO = open(self._file_path, 'r')
        client = mqtt.Client()

        # Allow unlimited size queue and inflight messages
        client.max_queued_messages_set(0)
        client.max_inflight_messages_set(0)

        client.connect(self._host, self._port)

        self._read_thread_exit_flag = False
        self._read_thread = Thread(name='Read Thread',
                                   target=self._read_thread_method,
                                   args=[file])
        self._read_thread.start()
        time.sleep(0.001)
        if not self._read_thread.is_alive():
            raise Exception('Could not start Read Thread')

        self._transmit_thread_exit_flag = False
        self._transmit_thread = Thread(name='Transmit Thread',
                                       target=self._transmit_thread_method,
                                       args=[client])
        self._transmit_thread.start()
        time.sleep(0.001)
        if not self._transmit_thread.is_alive():
            raise Exception('Could not start Read Thread')

        print('Player Started')

    def stop(self):
        print('Stopping Player...')
        self._read_thread_exit_flag = True
        if self._read_thread is not None:
            if self._read_thread.is_alive():
                self._read_thread.join()
        self._transmit_thread_exit_flag = True
        if self._transmit_thread is not None:
            if self._transmit_thread.is_alive():
                self._transmit_thread.join()
        print('Player Stopped')

    def _read_thread_method(self, file: TextIO):
        try:
            self._read(file)
        except Exception as ex:
            print(f'Read Thread Exception: {ex}')
        finally:
            file.close()
            self._read_thread = None

    def _transmit_thread_method(self, client: mqtt.Client):
        try:
            self._transmit(client)
        except Exception as ex:
            print(f'Transmit Thread Exception: {ex}')
        finally:
            client.disconnect()
            self._transmit_thread = None

    def _read(self, file: TextIO):
        file_start_time: datetime | None = None
        start_time = datetime.now(tz=timezone.utc)
        self._read_thread_start_of_file = False
        self._read_thread_end_of_file = False
        read_buffer_size = 100
        read_buffer: List[dict] = []

        line = file.readline()
        if not line.startswith('RTMDv'):
            print('Error: Not a RTMD file, RTMD version not found at first line')
            time.sleep(10)
            raise Exception('Not a RTMD file, RTMD version not found at first line')

        line = [int(element) for element in line.lstrip('RTMDv').split('.')]
        if not line[0] <= major_file_version:
            print(f'Error: RTMD file major version must be less than or equal to '
                  f'{major_file_version}. Can not play file.')
            time.sleep(10)
            raise Exception(f'RTMD file major version must be less than or equal to  '
                            f'{major_file_version}. Can not play file.')
        if not line[1] <= minor_file_version:
            print(f'Warning: RTMD file minor version {line[1]} is newer than this codebase '
                  f'({minor_file_version}).')

        while True:
            if self._read_thread_exit_flag:
                return

            if self._buffer.full():
                time.sleep(0.001)
                continue

            if len(read_buffer) < read_buffer_size and not self._read_thread_end_of_file:
                line = file.readline()
                if not line:
                    self._read_thread_end_of_file = True
                    print('Read Thread Reached End of File')
                    continue

                item = json.loads(line)
                if _KEYS.timestamp not in item:
                    raise Exception(f'timestamp key {_KEYS.timestamp} not found in line')
                if _KEYS.topic not in item:
                    raise Exception(f'topic key {_KEYS.topic} not found in line')
                if _KEYS.timestamp not in item:
                    raise Exception(f'payload key {_KEYS.payload} not found in line')

                item[_KEYS.timestamp] = datetime.fromisoformat(item[_KEYS.timestamp])

                if file_start_time is None:
                    file_start_time = item[_KEYS.timestamp]

                read_buffer.append(item)

            if len(read_buffer) == 0:
                time.sleep(0.001)
                continue

            # The time since playback began
            time_delta = datetime.now().astimezone(tz=timezone.utc) - start_time
            # The time since the beginning of the file
            first = read_buffer[0]
            file_delta = first[_KEYS.timestamp] - file_start_time

            if time_delta < file_delta:
                time.sleep(0.001)
                continue

            # # Update timestamp with relative playback time
            # ts_keys = ['Timestamp', 'timestamp']
            # for ts_key in ts_keys:
            #     if ts_key not in first[_KEYS.payload]:
            #         continue
            #
            #     try:
            #         timestamp = datetime.fromisoformat(first[_KEYS.payload][ts_key])
            #         adjusted = timestamp - file_start_time + start_time
            #         first[_KEYS.payload][ts_key] = adjusted.isoformat(timespec='milliseconds')
            #     except:
            #         pass

            self._buffer.put(read_buffer.pop(0))
            if not self._read_thread_start_of_file:
                self._read_thread_start_of_file = True

    def _transmit(self, client: mqtt.Client):
        while True:
            if self._transmit_thread_exit_flag:
                return

            if not self._read_thread_start_of_file:
                time.sleep(0.001)
                continue

            if self._buffer.empty():
                if self._read_thread_end_of_file:
                    print('Transmit Thread Buffer Empty at End of File')
                    return

                time.sleep(0.001)
                continue

            item = self._buffer.get()
            topic: str = item[_KEYS.topic]
            value = json.dumps(item[_KEYS.payload], sort_keys=True)
            try:
                client.publish(topic, value)
            except Exception as ex:
                print(f'Error Publishing {topic}: {ex}')


class Recorder:

    def __init__(self, file_path: str, host: str, port: int, subscription: str):
        if not isinstance(file_path, str):
            raise TypeError('file_path must be a str')
        if not file_path.endswith('.jsonl'):
            raise ValueError('file_path must be a .jsonl file')
        self._file_path = file_path

        if not isinstance(host, str):
            raise TypeError('host must be a string')
        self._host = host

        if not isinstance(port, int):
            raise TypeError('port must be an int')
        self._port = port

        if not isinstance(subscription, str):
            raise TypeError('subscription must be a string')
        self._subscription = subscription

        self._client: mqtt.Client = mqtt.Client()
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._write_thread: Thread | None = None
        self._write_thread_exit_flag = False
        self._buffer: Queue[dict] = Queue()

    def is_open(self):
        return self._write_thread is not None

    def start(self):
        if self._write_thread is not None:
            raise Exception('Recorder is already open')

        file: TextIO = open(self._file_path, 'w')
        self._client.connect(self._host, self._port)
        self._client.loop_start()

        self._write_thread = False
        self._write_thread_exit_flag = False
        self._write_thread = Thread(name='Write Thread',
                                    target=self._write_thread_method,
                                    args=[file])
        self._write_thread.start()
        time.sleep(0.001)
        if not self._write_thread.is_alive():
            raise Exception('Could not start Write Thread')

        print('Recorder Started')

    def stop(self):
        print('Stopping Recorder...')
        self._client.disconnect()
        self._write_thread_exit_flag = True
        self._write_thread.join()
        print('Recorder Stopped')

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc):
        if rc != 0:
            print('MQTT Connect unsuccessful, return code: {rc}', rc)
            self.stop()
            return False
        self._client.subscribe(self._subscription)
        print(f'Subscribed to {self._subscription}')

    def _on_message(self, client, userdata, msg):
        #timestamp = datetime.fromtimestamp(msg.timestamp).astimezone(tz=timezone.utc)
        timestamp = datetime.now(tz=timezone.utc)
        item = {
            _KEYS.timestamp: timestamp.isoformat(timespec='milliseconds'),
            _KEYS.topic: msg.topic,
            _KEYS.payload: json.loads(msg.payload)
        }
        self._buffer.put(item)

    def _write_thread_method(self, file: TextIO):
        try:
            self._write(file)
        except Exception as ex:
            print(f'Write Thread Exception: {ex}')
        finally:
            file.close()
            self._write_thread = None

    def _write(self, file: TextIO):
        # Write Version to File
        file.write(f'RTMDv{major_file_version}.{minor_file_version}\n')

        while True:
            if self._write_thread_exit_flag:
                return

            if self._buffer.empty():
                time.sleep(0.001)
                continue

            line = json.dumps(self._buffer.get_nowait()) + '\n'
            file.write(line)

