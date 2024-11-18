# Ignition

This stack contains an [Ignition](https://inductiveautomation.com/) gateway and [MariaDB](https://mariadb.org/) historian. Both are pre-configured via a gateway backup (`base.gwbk`). The Ignition gateway provides real-time visualization of data visible in a [Demo Project](http://localhost:8088/data/perspective/client/DemoProject). The MariaDB historian is utilized by the Ignition gateway and is not intended to be used by the end user.

1. Download the gateway backup (`base.gwbk`) and place it in the `ignition/restore/` directory.
    - Gateway backups are provided by the author of datasets, or on the [Releases](https://github.com/m-r-mccormick/Real-Time-Manufacturing-Datasets/releases) page.
2. Download the [Hydra-MQTT](https://github.com/m-r-mccormick/Hydra-MQTT/releases) module (`*.modl`) and place it in the `ignition/build/modules/` directory.

1. Start the stack:
```bash
docker-compose up -d --build
```

2. Log in at [http://localhost:8088/](http://localhost:8088/).
3. Open the [Demo Project](http://localhost:8088/data/perspective/client/DemoProject) via `Home > Perspective Session Launcher > View Projects > DemoProject > Launch Project`.

4. Stop the stack:
```bash
docker-compose down
```

