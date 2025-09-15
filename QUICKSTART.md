# Quick Start Guide - WOL Proxy

This guide will help you set up the WOL Proxy add-on for your Ollama gaming PC setup.

## Prerequisites

1. **Gaming PC with Ollama** - Your Windows gaming PC running Ollama server
2. **Home Assistant** - Running and accessible
3. **Network Access** - Both devices on the same network
4. **Wake-on-LAN Enabled** - On your gaming PC

## Step 1: Enable Wake-on-LAN on Gaming PC

### Windows Setup:
1. Open **Device Manager** (Win + X, then M)
2. Expand **Network adapters**
3. Right-click your network adapter → **Properties**
4. Go to **Advanced** tab
5. Find **Wake on Magic Packet** → Set to **Enabled**
6. Go to **Power Management** tab
7. Check **Allow this device to wake the computer**
8. Click **OK**

### BIOS Setup (if needed):
1. Restart PC and enter BIOS (usually F2, F12, or Delete during boot)
2. Look for **Power Management** or **Advanced** settings
3. Enable **Wake on LAN** or **PME Event Wake Up**
4. Save and exit BIOS

## Step 2: Find Your Gaming PC's Information

### Get IP Address:
```cmd
ipconfig
```
Look for "IPv4 Address" (e.g., 192.168.1.100)

### Get MAC Address:
```cmd
ipconfig /all
```
Look for "Physical Address" (e.g., AA-BB-CC-DD-EE-FF)

## Step 3: Install the Add-on

### Add Repository to HACS:
1. In Home Assistant, go to **HACS**
2. Click **Integrations**
3. Click the three dots (⋮) → **Custom repositories**
4. Add: `https://github.com/malbert911/ha-wol-proxy`
5. Category: **Add-on**
6. Click **Add**

### Install Add-on:
1. Search for "WOL Proxy"
2. Click **Install**
3. Wait for installation to complete

## Step 4: Configure the Add-on

### Basic Configuration:
```yaml
log_level: info
services:
  - target_host: "192.168.1.100"        # Your gaming PC IP
    target_port: 11434                  # Ollama port
    proxy_port: 11434                   # Same port for proxy
    mac_address: "aa:bb:cc:dd:ee:ff"    # Your PC's MAC address
    wake_timeout: 60                    # Wait 60s for wake-up
    health_check_interval: 10           # Check every 10s
    protocol: "tcp"                     # TCP for Ollama
```

### Replace the values:
- `target_host`: Your gaming PC's IP address
- `mac_address`: Your gaming PC's MAC address (remove dashes, use colons)

## Step 5: Start the Add-on

1. Click **Start** on the add-on
2. Check the **Log** tab for any errors
3. You should see: "Started TCP proxy on port 11434"

## Step 6: Update Ollama Integration

### Edit Home Assistant Configuration:
```yaml
# configuration.yaml
ollama:
  base_url: "http://homeassistant.local:11434"
```

Or if using a custom integration, update the URL to point to your Home Assistant IP instead of the gaming PC.

## Step 7: Test the Setup

1. **Put Gaming PC to Sleep** - Let it go to sleep naturally or manually sleep it
2. **Trigger Ollama** - Use a Home Assistant automation or service that calls Ollama
3. **Check Logs** - Watch the add-on logs to see:
   - "Target not available, attempting WOL"
   - "Sending WOL packet to [MAC]"
   - "Successfully woke up [IP]:11434"
   - Traffic forwarding

## Troubleshooting

### Gaming PC Won't Wake Up:
- ✅ Check WOL is enabled in Device Manager
- ✅ Check BIOS settings for Wake on LAN
- ✅ Verify MAC address is correct
- ✅ Test manually: `wakeonlan aa:bb:cc:dd:ee:ff`

### Connection Issues:
- ✅ Check firewall isn't blocking port 11434
- ✅ Verify IP address is correct
- ✅ Ensure gaming PC is on same network as HA

### Ollama Not Responding:
- ✅ Check Ollama is running on gaming PC
- ✅ Test direct connection when PC is awake
- ✅ Verify Ollama binds to 0.0.0.0, not just localhost

## Advanced Configuration

### Multiple Services:
```yaml
log_level: info
services:
  # Ollama
  - target_host: "192.168.1.100"
    target_port: 11434
    proxy_port: 11434
    mac_address: "aa:bb:cc:dd:ee:ff"
    protocol: "tcp"
  
  # Plex (example)
  - target_host: "192.168.1.100"
    target_port: 32400
    proxy_port: 32400
    mac_address: "aa:bb:cc:dd:ee:ff"
    protocol: "tcp"
```

### Fine-tuning:
- `wake_timeout`: Increase if PC takes longer to boot
- `health_check_interval`: Decrease for faster detection
- `log_level`: Set to "debug" for detailed troubleshooting

## Success!

Once configured, your gaming PC will:
- ✅ Sleep when not in use
- ✅ Automatically wake when Home Assistant needs Ollama
- ✅ Provide seamless AI functionality
- ✅ Save power and reduce noise

The proxy is transparent - Home Assistant won't know the difference!
