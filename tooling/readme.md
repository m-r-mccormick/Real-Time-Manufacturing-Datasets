# Real-Time Manufacturing Datasets Tooling

This directory contains pre-configured tooling which is intended to jump-start the consumption of [Real-Time Manufacturing Datasets](https://github.com/m-r-mccormick/Real-Time-Manufacturing-Datasets) (RTMD).

## Operating System Support

The provided tooling has been developed and tested on [Debian](https://www.debian.org/). Other operating systems (e.g., Windows and MacOS) are not officially supported at this time, but the tooling has been confirmed to operate successfully on Windows 10. Likewise, [Debian](https://www.debian.org/) derivatives (e.g., [Ubuntu](https://ubuntu.com/), [Linux Mint](https://linuxmint.com/)) are likely to operate successfully.

## Dependencies

The provided tooling is dependent on `make` and `docker` to operate. Both must be installed before utilizing the provided tooling:

1. Install Make

    | OS | Instructions |
    |----|--------------|
    | Debian | 1. Install Make:<pre>sudo apt-get install make</pre>2. Verify that `make` is installed by opening a terminal and running:<pre>make --version</pre> |
    | Windows | 1. Download and install [Make for Windows](https://gnuwin32.sourceforge.net/packages/make.htm) ([Setup](https://gnuwin32.sourceforge.net/downlinks/make.php) next to `Complete package, except sources`)<br>2. Add `C:\Program Files (x86)\GnuWin32\bin` to the `Path` environment variable: `Start Menu > Search > Edit environment variables for your account > Path > Edit... > New`<br>3. Verify that `make` is in the `Path` environment variable by opening the command prompt or powershell and executing:<pre>make --version</pre> |

2. Install Docker

    | OS | Instructions |
    |----|--------------|
    | Debian | 1. Install Docker:<pre>sudo apt-get install docker docker.io docker-compose</pre>2. Add the current user to the docker group so the user can execute docker commands without `sudo`:<br><pre>sudo groupadd docker<br>sudo usermod -aG docker $USER</pre>3. Restart the machine:<br><pre>sudo reboot</pre> |
    | Windows | 1. Install Windows Subsystem for Linux (WSL) using command prompt or powershell as administrator via:<pre>Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform<br>wsl --install<br>wsl --update</pre>2. Download and install [Docker Desktop on Windows](https://docs.docker.com/desktop/install/windows-install/).<br>3. Reboot<br>4. Start `Docker Desktop`.<br>4. Verify that `docker` is operational by opening the command prompt or powershell and executing:<pre>docker run --rm -it hello-world</pre> |

3. Install Git

    | OS | Instructions |
    |----|--------------|
    | Debian | 1. Install Git:<pre>sudo apt-get install git</pre>2. Verify that `git` is installed by opening a terminal and running:<pre>git --version</pre> |
    | Windows | 1. Download and install [Git for Windows Setup](https://git-scm.com/downloads/win).<br>2. Verify that `git` is installed by opening a terminal and running:<pre>git --version</pre> |

## Repository Cloning

This repository can be cloned (i.e., downloaded) via:
```bash
git clone https://github.com/m-r-mccormick/Real-Time-Manufacturing-Datasets.git
```

There are two types of text file line endings:

- `CRLF`: Carriage Return and Line Feed `\r\n` (Windows)
- `LF`: Line Feed `\n` (OSX, Linux)

Files inside this repository are used to build tooling inside of Linux docker containers. Since Linux expects `LF` line endings, tooling files must use `LF` line endings and not `CRLF` line endings. `* text eol=lf` inside the `.gitattributes` file should configure git to automatically use `LF` line endings. After cloning the RTMD repository, you can check the line endings of cloned files using:
```bash
git ls-files --eol
```

This will output similar to:
```text
i/lf    w/lf    attr/text eol=lf      	readme.md
```

If line endings are not `LF` (i.e., `eol=lf`), line endings can be globally configured to `LF` using the following command, then the repository must be deleted and re-cloned:
```bash
git config --global core.autocrlf input
git clone https://github.com/m-r-mccormick/Real-Time-Manufacturing-Datasets.git
```

## Docker-Compose Stacks

The provided tooling consists of multiple docker-compose stacks:

| Stack | Description | Endpoints |
|-------|-------------|-------|
| [broker](broker/) | A MQTT broker. | `mqtt://localhost:1883` |
| [ignition](ignition/) | An [Inductive Automation Ignition](https://inductiveautomation.com/) Gateway. | [Gateway Web UI](http://localhost:8088/), [Demo Project](http://localhost:8088/data/perspective/client/DemoProject) |
| [influx](influx/) | An [InfluxDB](https://www.influxdata.com/) time-series historian. | [InfluxDB Web UI](http://localhost:8086) |
| [mes](mes/) | A [MariaDB](https://mariadb.org/) cache database for MES data. | `localhost:3307` |
| [player](player/) | An application for capturing and replaying RTMD datasets. | |

All services in all stacks use the following credentials:
- Username: `admin`
- Password: `password`

If manually starting the stacks, they should be started in the order listed below, and stopped in the reverse order. Since some stacks are dependent on other stacks, this ensures that stack dependencies are met when starting stacks. For example, since the `player` publishes data into the `broker`, the `broker` must be started before the `player`. Stopping stacks in reverse order ensures that stacks will not crash due to a dependency being stopped, which may cause an issue when re-starting stacks.

## Makefile

To make operating all stacks seamless, a `makefile` is included. In this directory, run `make` to see available commands:

  ```text
  Available Commands:
    make up    - Start All Stacks
    make down  - Stop All Stacks
    make clear - Stop All Stacks and Remove All RTMD Volumes/Data
    make size  - Display the Size of Docker Volumes
  ```

To get up and running quickly:

1. Place the Ignition Gateway Backup (`base.gwbk`, download from dataset release) in the `ignition/restore/` directory.
2. Place the Ignition [Hydra-MQTT](https://github.com/m-r-mccormick/Hydra-MQTT/releases) module (`Hydra-MQTT.modl`) in the `ignition/build/modules/` directory.
3. Place RTMD datasets (`*.jsonl`, download from dataset release) in the `player/datasets/` directory.
4. Run `make up` to build and start all stacks.
5. Start the Ignition Gateway at [http://localhost:8088](http://localhost:8088).
6. Open the Ignition Perspective demo project at [http://localhost:8088/data/perspective/client/DemoProject](http://localhost:8088/data/perspective/client/DemoProject).
7. Open the InfluxDB explorer at [http://localhost:8086](http://localhost:8086) and query data in the `telegraf` bucket.
8. Run:
  - `make down` to stop all stacks, or
  - `make clear` to stop all stacks and remove all RTMD data. (This will remove RTMD docker volumes. This will not delete datasets in the `player/datasets/` directory, and will not remove non-RTMD docker volumes.)

