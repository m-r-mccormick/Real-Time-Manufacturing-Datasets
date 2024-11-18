# Player

This stack contains a python application which replays `*.jsonl` datasets into the MQTT broker. The application will loop through all datasets in the `player/datasets/` directory and play them sequentially. After all datasets have been replayed, it will loop back through all the datasets indefinitely. To disable indefinite playback, comment or remove `restart: unless-stopped` from `docker-compose.yml`.

Examples for consuming data using python can be found [here](build/examples).

## Dataset Replay Instructions

1. Download datasets (`*.jsonl`) and place them in the `player/datasets/` directory.

2. Start the stack:
```bash
docker-compose up -d --build
```

3. Stop the stack:
```bash
docker-copose down
```

## Dataset Capture Instructions

### Capture From Provided Broker

To capture data from the provided broker, modify `player/docker-compose.yml` environment variables:

```bash
    environment:
      - BROKER_HOST=broker
      - BROKER_PORT=1883
#      - MODE=replay
      - MODE=capture
      - BROKER_SUBSCRIPTION=Enterprise/#
```

Then, start the broker and player stacks:

```bash
cd ../broker
docker-compose up -d --build
cd ../player
docker-compose up -d --build
```

To stop capturing data, stop the stacks in the reverse order:

```bash
docker-compose down
cd ../broker
docker-compose down
cd ../player
```

### Capture From External Broker

To capture data from an external broker, modify `player/docker-compose.yml` environment variables:

```bash
    environment:
      - BROKER_HOST=192.168.1.8
      - BROKER_PORT=1883
#      - MODE=replay
      - MODE=capture
      - BROKER_SUBSCRIPTION=Enterprise/#
```

Then, start the player stack:

```bash
docker-compose up -d --build
```

To stop capturing data, stop the player stack:

```bash
docker-compose down
```

### File Ownership of Captured Datasets

Captured datasets will be saved to the `player/datasets/` directory with the capture start time as the file name.

On Linux, captured datasets will be owned by the `root` user. To change dataset file ownership to the current user after capturing, run:
```bash
sudo chown $USER:$USER player/datasets/*.jsonl
```

