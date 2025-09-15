# WOL Proxy - Home Assistant Add-on

A sophisticated proxy service that automatically wakes up sleeping devices using Wake-on-LAN (WOL) when network requests are made to them. Perfect for gaming PCs, media servers, or any device you want to keep sleeping until needed.

## Features

- **Generic WOL Proxy**: Works with any TCP or UDP service
- **Automatic Wake-up**: Sends WOL packets when target devices are sleeping
- **Multi-service Support**: Proxy multiple services/ports simultaneously
- **Health Monitoring**: Continuously monitors target device availability
- **Configurable Timeouts**: Customize wake-up timeouts and health check intervals
- **Low Resource Usage**: Lightweight proxy with minimal overhead

## Use Cases

- **Ollama Server**: Keep your gaming PC sleeping until Home Assistant needs to use Ollama
- **Media Servers**: Wake up Plex, Jellyfin, or other media servers on demand
- **Development Servers**: Wake up development machines when accessing services
- **Gaming Servers**: Start game servers only when players connect

## Configuration

### Basic Configuration

```yaml
log_level: info
services:
  - target_host: "192.168.1.100"     # IP of your gaming PC
    target_port: 11434               # Ollama port
    proxy_port: 11434                # Port this add-on will listen on
    mac_address: "aa:bb:cc:dd:ee:ff" # MAC address of gaming PC
    wake_timeout: 60                 # How long to wait for wake-up
    health_check_interval: 10        # How often to check if target is alive
    protocol: "tcp"                  # tcp or udp
```

### Multiple Services Example

```yaml
log_level: info
services:
  # Ollama AI Service
  - target_host: "192.168.1.100"
    target_port: 11434
    proxy_port: 11434
    mac_address: "aa:bb:cc:dd:ee:ff"
    protocol: "tcp"
  
  # Plex Media Server
  - target_host: "192.168.1.100"
    target_port: 32400
    proxy_port: 32400
    mac_address: "aa:bb:cc:dd:ee:ff"
    protocol: "tcp"
  
  # Custom UDP Service
  - target_host: "192.168.1.101"
    target_port: 9999
    proxy_port: 9999
    mac_address: "11:22:33:44:55:66"
    protocol: "udp"
    wake_timeout: 90
    health_check_interval: 15
```

## Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `log_level` | No | `info` | Logging level: trace, debug, info, notice, warning, error, fatal |
| `services` | Yes | `[]` | List of services to proxy |

### Service Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `target_host` | Yes | - | IP address or hostname of the target device |
| `target_port` | Yes | - | Port number on the target device |
| `proxy_port` | Yes | - | Port this add-on will listen on |
| `mac_address` | Yes | - | MAC address of target device (for WOL) |
| `wake_timeout` | No | `60` | Seconds to wait for device to wake up (30-300) |
| `health_check_interval` | No | `10` | Seconds between health checks (5-60) |
| `protocol` | No | `tcp` | Protocol to proxy: `tcp` or `udp` |

## How It Works

1. **Proxy Listening**: The add-on listens on the configured proxy ports
2. **Client Connection**: When a client connects to a proxy port
3. **Health Check**: The add-on checks if the target device is awake
4. **Wake-on-LAN**: If the device is sleeping, sends a WOL packet
5. **Wait for Wake**: Waits for the device to become available
6. **Proxy Traffic**: Once awake, proxies all traffic transparently
7. **Continuous Monitoring**: Monitors device status in the background

## Setup Instructions

### 1. Enable Wake-on-LAN on Target Device

**Windows:**
1. Open Device Manager
2. Find your network adapter
3. Right-click → Properties → Advanced
4. Enable "Wake on Magic Packet"
5. Power Management → "Allow this device to wake the computer"

**Linux:**
```bash
sudo ethtool -s eth0 wol g
```

### 2. Find MAC Address

**Windows:**
```cmd
ipconfig /all
```

**Linux:**
```bash
ip link show
```

### 3. Configure Home Assistant

Update your Home Assistant configuration to point to the proxy instead of the target device directly.

**For Ollama Integration:**
```yaml
# configuration.yaml
ollama:
  base_url: "http://homeassistant.local:11434"  # Point to proxy
```

### 4. Install and Configure Add-on

1. Add this repository to HACS
2. Install the "WOL Proxy" add-on
3. Configure the services as shown above
4. Start the add-on

## Troubleshooting

### Device Won't Wake Up

1. **Check WOL Settings**: Ensure WOL is enabled in BIOS and OS
2. **Test WOL Manually**: Use `wakeonlan` command to test
3. **Check MAC Address**: Verify the MAC address is correct
4. **Network Issues**: Ensure the device is on the same network
5. **Power Settings**: Check Windows power settings allow wake-up

### Connection Issues

1. **Check Logs**: Review add-on logs for errors
2. **Firewall**: Ensure target ports are not blocked
3. **Port Conflicts**: Make sure proxy ports are not in use
4. **Network Routing**: Verify Home Assistant can reach target IPs

### Performance Issues

1. **Adjust Timeouts**: Increase `wake_timeout` for slow devices
2. **Health Check Frequency**: Adjust `health_check_interval`
3. **Resource Monitoring**: Check add-on resource usage

## Advanced Usage

### Custom Health Checks

The add-on performs simple TCP/UDP connectivity checks. For more sophisticated health checks, you can:

1. Use shorter timeouts for faster response
2. Configure multiple services on the same device
3. Implement application-specific health endpoints

### Integration with Automations

Create automations to:
- Notify when devices wake up/go to sleep
- Schedule wake-up times
- Force devices to sleep after inactivity

### Monitoring

Monitor the add-on through:
- Home Assistant logs
- Add-on logs
- Network monitoring tools

## Support

- **Issues**: [GitHub Issues](https://github.com/malbert911/ha-wol-proxy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/malbert911/ha-wol-proxy/discussions)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.