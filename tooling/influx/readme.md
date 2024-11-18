# Influx

This stack contains an instance of [InfluxDB](https://www.influxdata.com/) to store time series data, and an instance of [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/) to consume MQTT data and store it in the influx database. By default, telegraf is configured to ignore video topics to reduce storage size and improve performance.

1. Start the stack:
```bash
docker-compose up -d --build
```

2. Open the influx data explorer at [http://localhost:8086](http://localhost:8086)

3. Stop the stack:
```bash
docker-compose down
```

