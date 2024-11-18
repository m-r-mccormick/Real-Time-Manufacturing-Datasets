# Broker

This stack contains a MQTT broker running on port `1883`. You can view real-time data passing through the broker by connecting to `mqtt://localhost:1883` with no username and no password using [MQTT Explorer](http://mqtt-explorer.com/).

1. Start the stack:
```bash
docker-compose up -d --build
```

2. Stop the stack:
```bash
docker-compose down
```

