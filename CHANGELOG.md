## What's Changed
- Initial release of WOL Proxy Home Assistant Add-on
- Generic Wake-on-LAN proxy for any TCP/UDP service
- Multi-service support with individual configuration
- Automatic device wake-up and health monitoring
- Configurable timeouts and health check intervals
- Perfect for Ollama servers, media servers, and development machines

## Installation

1. Add this repository to HACS as a custom repository
2. Install the "WOL Proxy" add-on
3. Configure your services in the add-on configuration
4. Start the add-on

## Example Configuration

```yaml
log_level: info
services:
  - target_host: "192.168.1.100"
    target_port: 11434
    proxy_port: 11434
    mac_address: "aa:bb:cc:dd:ee:ff"
    protocol: "tcp"
```

See the README for detailed configuration options and setup instructions.
