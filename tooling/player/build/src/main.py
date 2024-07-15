import argparse
import datetime
import os.path
import signal
import time
from pathlib import Path

from realtime import Player, Recorder

exit_flag = False


def signal_handler(signum, frame):
    global exit_flag

    if signum == 2:
        print("Exit Signal Received")
    else:
        print(f"Exit Signal Received: {signum}")

    exit_flag = True


def capture(args):
    global exit_flag

    recorder = Recorder(args.file, args.host, args.port, args.sub)
    recorder.start()

    while recorder.is_open():
        if exit_flag:
            print('Handling Exit Signal')
            break
        time.sleep(0.1)

    recorder.stop()


def replay(file, host, port):
    global exit_flag

    if exit_flag:
        return

    player = Player(file, host, port)
    player.start()

    while player.is_open():
        if exit_flag:
            break
        time.sleep(0.1)

    player.stop()


def main():
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description="Real-Time IIoT Capture and Replay")

    # Add subparsers for the 'anony' command
    subparsers = parser.add_subparsers(dest='command', help='commands')

    # Capture Command
    capture_parser = subparsers.add_parser('capture', help='Capture a .jsonl file')
    capture_parser.add_argument('--file', type=str, required=False,
                                help='Path to the jsonl file to capture (e.g. dataset.jsonl)')
    capture_parser.add_argument('--dir', type=str, required=False,
                                help='Path to the jsonl file to capture (e.g. datasets/)')
    capture_parser.add_argument('--host', type=str, required=True,
                            help='The MQTT Broker Host (e.g. localhost)')
    capture_parser.add_argument('--port', type=int, required=True,
                                help='The MQTT Broker Port (e.g. 1883')
    capture_parser.add_argument('--sub', type=str, required=True,
                                help='The MQTT Subscription (e.g. Enterprise/#)')

    # Play Command
    replay_parser = subparsers.add_parser('replay', help='Play a .jsonl file')
    replay_parser.add_argument('--file', type=str, required=False,
                               help='Path to the jsonl file to play (e.g. dataset.jsonl)')
    replay_parser.add_argument('--dir', type=str, required=False,
                               help='Path to the directory containing jsonl files to play (e.g. datasets/)')
    replay_parser.add_argument('--host', type=str, required=True,
                            help='The MQTT Broker Host (e.g. localhost)')
    replay_parser.add_argument('--port', type=int, required=True,
                            help='The MQTT Broker Port (e.g. 1883')

    args = parser.parse_args()

    if args.command == 'capture':
        if args.file is None:
            if args.dir is None:
                raise Exception("Either --file or --dir must be specified")
            start_time = datetime.datetime.now().astimezone(tz=datetime.timezone.utc)
            args.file = os.path.join(args.dir, start_time.isoformat(timespec='seconds').replace(':','-') + '.jsonl')
        capture(args)
    elif args.command == 'replay':
        if args.file is not None:
            replay(args.file, args.host, args.port)
        elif args.dir is not None:
            dir_path = Path(args.dir)
            for file in dir_path.glob('*.jsonl'):
                if not file.is_file():
                    raise FileNotFoundError(f'File {file} is not a file')
            for file in dir_path.glob('*.jsonl'):
                replay(str(file), args.host, args.port)
        else:
            raise Exception("Either --file or --dir must be specified")
    else:
        raise Exception('Unknown command')


if __name__ == '__main__':
    main()
