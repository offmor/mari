# Mosquitto MQTT Broker

This folder contains a Docker configuration to run a local Mosquitto MQTT broker for development purposes.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed on your system

### Starting the Broker

```bash
# Start the MQTT broker in the background
docker-compose up -d

# Or start with logs visible
docker-compose up
```

### Stopping the Broker

```bash
# Stop the broker
docker-compose down

# Stop and remove volumes (clean reset)
docker-compose down -v
```

### Checking Status

```bash
# View running containers
docker-compose ps

# View broker logs
docker-compose logs mosquitto

# Follow logs in real-time
docker-compose logs -f mosquitto
```

## Testing the Connection

You can test the broker using any MQTT client:

```bash
# Using mosquitto_pub/mosquitto_sub (if installed locally)
mosquitto_sub -h localhost -p 1883 -t test/topic
mosquitto_pub -h localhost -p 1883 -t test/topic -m "Hello MQTT"
```

## Troubleshooting

### Port Already in Use
If ports 1883 or 1884 are already in use, modify the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "18830:1883"  # Change local port
  - "18840:1884"  # Change local port
```

### Checking if Broker is Running
```bash
# Check if ports are open
netstat -an | grep 1883
netstat -an | grep 1884
```