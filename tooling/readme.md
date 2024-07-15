# Dataset Replay Instructions

This directory contains multiple docker-compose stacks which jump-start the consumption of [Real-Time Manufacturing Datasets](https://github.com/m-r-mccormick/Real-Time-Manufacturing-Datasets).

If using git on windows, ensure that files are checked out with linux line endings (LF, not CRLF) before cloning this repository:
```
git config --global core.autocrlf input
```

The stacks have been developed and tested on [Debian](https://www.debian.org/). Other operating systems (e.g., Windows and MacOS) are not officially supported. However, debian derivatives (e.g., [Ubuntu](https://ubuntu.com/), [Linux Mint](https://linuxmint.com/)) are likely to work.

All services in all stacks use the following credentials:
- Username: `admin`
- Password: `password`

The stacks should be started in the order listed below, and stopped in the reverse order.

### Makefile

To make operating all stacks seamless, a `makefile` is included. In this directory, run `make` to see available commands. To get up and running quickly:

1. Install Make
   - Debian
     ```bash
     sudo apt-get install make
     ```
   - Windows
     - Download and install [Make for Windows](https://gnuwin32.sourceforge.net/packages/make.htm).
     - Ensure that `C:\Program Files (x86)\GnuWin32\bin` is in the `Path` environment variable.
2. Install Docker
   - Debian
     ```bash
     sudo apt-get install docker docker.io docker-compose
     ```
     Add user to the docker group so the user can execute docker commands without `sudo`:
     ```bash
     sudo groupadd docker
     sudo usermod -aG docker $USER
     sudo reboot
     ```
   - Windows
     - Download and install [Docker Desktop on Windows](https://docs.docker.com/desktop/install/windows-install/).
3. Place `base.gwbk` in the `ignition/restore/` directory.
4. Place the [Hydra-MQTT](https://github.com/m-r-mccormick/Hydra-MQTT/releases) module (`Hydra-MQTT.modl`) in the `ignition/build/modules/` directory.
5. Place datasets (`*.jsonl`) in the `player/datasets/` directory.
6. Run `make up`
7. Start the Ignition gateway at [http://localhost:8088](http://localhost:8088).
8. Open the Ignition perspective demo project at [http://localhost:8088/data/perspective/client/DemoProject](http://localhost:8088/data/perspective/client/DemoProject).
9. Open the InfluxDB explorer at [http://localhost:8086](http://localhost:8086) and query data in the `telegraf` bucket.
10. When done, run `make down` or `make clear`

### 1. Broker

This stack contains a MQTT broker running on port `1883`. You can view real-time data passing through the broker by connecting to `mqtt://localhost:1883` with no username and no password using [MQTT Explorer](http://mqtt-explorer.com/).

1. Start the stack:
```bash
cd broker
docker-compose up -d --build
cd ..
```

2. Stop the stack:
```bash
cd broker
docker-copose down
cd ..
```

### 2. Ignition

This stack contains an [Ignition](https://inductiveautomation.com/) gateway and [MariaDB](https://mariadb.org/) historian. Both are pre-configured via a gateway backup (`base.gwbk`). The Ignition gateway provides real-time visualization of data visible in a [Demo Project](http://localhost:8088/data/perspective/client/DemoProject). The MariaDB historian is utilized by the Ignition gateway and is not intended to be used by the end user.

1. Download the gateway backup (`base.gwbk`) and place it in the `ignition/restore/` directory.
    - Gateway backups are provided by the author of datasets, or on the [Releases](https://github.com/m-r-mccormick/Real-Time-Manufacturing-Datasets/releases) page.
2. Download the [Hydra-MQTT](https://github.com/m-r-mccormick/Hydra-MQTT/releases) module (`*.modl`) and place it in the `ignition/build/modules/` directory.

1. Start the stack:
```bash
cd ignition
docker-compose up -d --build
cd ..
```

2. Log in at [http://localhost:8088/](http://localhost:8088/).
3. Open the [Demo Project](http://localhost:8088/data/perspective/client/DemoProject) via `Home > Perspective Session Launcher > View Projects > DemoProject > Launch Project`.

4. Stop the stack:
```bash
cd ignition
docker-copose down
cd ..
```

### 3. MES

This stack contains a [MariaDB](https://mariadb.org/) database which stores MES data, and python application which ingests MES change data capture events and stores them in the database. The reconstructed MES database can be viewed using a utility such as [DBeaver](https://dbeaver.io/) via `localhost:3307`

1. Clear/reset the database (optional):
```bash
docker volume rm rtmd-mes
```

2. Start the stack:
```bash
cd mes
docker-compose up -d --build
cd ..
```

3. Connect using a viewer via `localhost:3307`

4. Stop the stack:
```bash
cd mes
docker-copose down
cd ..
```

### 4. Influx

This stack contains an instance of [InfluxDB](https://www.influxdata.com/) to store time series data, and an instance of [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/) to consume MQTT data and store it in the influx database. By default, telegraf is configured to ignore video topics to reduce storage size and improve performance.

1. Start the stack:
```bash
cd influx
docker-compose up -d --build
cd ..
```

2. Open the influx data explorer at [http://localhost:8086](http://localhost:8086)

3. Stop the stack:
```bash
cd influx
docker-copose down
cd ..
```

### 5. Player

This stack contains a python application which replays `*.jsonl` datasets into the MQTT broker. The application will loop through all datasets in the `player/datasets/` directory and play them sequentially. After all datasets have been replayed, it will loop back through all the datasets indefinitely. To disable indefinite playback, remove `restart: unless-stopped` from `docker-compose.yml`.

1. Download datasets (`*.jsonl`) and place them in the `player/datasets/` directory.

2. Start the stack:
```bash
cd player
docker-compose up -d --build
cd ..
```

3. Stop the stack:
```bash
cd player
docker-copose down
cd ..
```

Examples for consuming data using python can be found [here](player/build/examples).

# Dataset Capture Instructions

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
cd broker
docker-compose up -d --build
cd ..
cd player
docker-compose up -d --build
cd ..
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
cd player
docker-compose up -d --build
cd ..
```

### Captured Datasets

Captured datasets will be saved to the `player/datasets/` directory with the capture start time as the file name.

On linux, captured datasets will be owned by root. To change dataset ownership to the current user after capturing, run:
```bash
sudo chown $USER:$USER player/datasets/*.jsonl
```

