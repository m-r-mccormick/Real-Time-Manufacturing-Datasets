from datetime import datetime
import json
from pathlib import Path


def process_event(event: dict) -> dict:
    if not isinstance(event, dict):
        raise TypeError('event must be a dict')

    if 'PAYLOAD' not in event:
        print('Error: PAYLOAD not defined in event')
        raise Exception('PAYLOAD not defined in event')
    event_payload: dict = event['PAYLOAD']

    if 'TIMESTAMP' not in event:
        print('Error: TIMESTAMP not defined in event')
        raise Exception('TIMESTAMP not defined in event')
    # This is when the data was received from the MQTT broker (not the device (PLC) timestamp)
    event_datetime: datetime = datetime.fromisoformat(event['TIMESTAMP'])

    if 'TOPIC' not in event:
        print('Error: TOPIC not defined in event')
        raise Exception('TOPIC not defined in event')
    event_topic: str = event['TOPIC']

    # If any Transaction does not contain a 'Database' identifier, add a default 'MES' identifier.
    if 'Transaction' in event_payload:
        transaction = event_payload['Transaction']
        if 'Database' not in transaction:
            transaction['Database'] = 'MES'

    return event


def main():
    # The input directory containing all datasets to post-process
    input_directory = 'docker/player/datasets/'
    # The output directory where post-processed datasets should be saved
    output_directory = '.'

    # Determine input file and output file pairs
    io_pairs = []
    for input_path in Path(input_directory).glob('*.jsonl'):
        output_path = Path(output_directory, input_path.name)
        if output_path.exists():
            print(f'Error: output_file {output_path} already exists')
            raise FileExistsError(output_path)
        io_pairs.append((str(input_path), str(output_path)))

    for pair in io_pairs:
        input_path = Path(pair[0])
        output_path = Path(pair[1])
        print(f'Post-Processing {input_path} -> {output_path}...')

        first_line = True
        with open(input_path, 'r') as input_file:
            with open(output_path, 'w') as output_file:
                while True:
                    line = input_file.readline()
                    if not line:
                        break  # End of File
                    if first_line:
                        first_line = False
                        if line.startswith('RTMDv'):
                            output_file.write(line)
                            continue
                        else:
                            output_file.write('RTMDv0.1\n')

                    event = json.loads(line)
                    event = process_event(event)
                    output_file.write(json.dumps(event) + '\n')

        print(f'Post-Processing {input_path} -> {output_path} Complete')

    print('done')


if __name__ == '__main__':
    main()
