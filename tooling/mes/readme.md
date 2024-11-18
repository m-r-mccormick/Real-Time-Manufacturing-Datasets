# MES

This stack contains a [MariaDB](https://mariadb.org/) database which stores MES data, and python application which ingests MES change data capture events and stores them in the database. The reconstructed MES database can be viewed using a utility such as [DBeaver](https://dbeaver.io/) via `localhost:3307`

1. Clear/reset the database (optional):
```bash
docker volume rm rtmd-mes
```

2. Start the stack:
```bash
docker-compose up -d --build
```

3. Connect using a viewer via `localhost:3307`

4. Stop the stack:
```bash
docker-compose down
```
