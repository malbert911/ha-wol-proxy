#!/usr/bin/env python3
"""
Development/testing script for WOL Proxy
Run this locally to test the proxy functionality
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the wol_proxy module to path
sys.path.insert(0, str(Path(__file__).parent))

from wol_proxy.proxy_server import ProxyServer
from wol_proxy.config import Config

# Configure logging for development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def load_dev_config():
    """Load configuration for development"""
    config_file = Path('config-example.yaml')
    if not config_file.exists():
        logger.error("config-example.yaml not found")
        return None
    
    import yaml
    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Extract options
    options = config_data.get('options', {})
    return Config(options)

async def main():
    """Main development entry point"""
    print("WOL Proxy - Development Mode")
    print("============================")
    
    # Load configuration
    config = load_dev_config()
    if not config:
        print("Failed to load configuration")
        return
    
    print(f"Loaded {len(config.services)} services:")
    for service in config.services:
        print(f"  - {service.target_host}:{service.target_port} -> proxy port {service.proxy_port} ({service.protocol.upper()})")
    
    print("\nStarting proxy server...")
    
    # Create and start proxy server
    proxy_server = ProxyServer(config)
    
    try:
        await proxy_server.start()
        print("✅ WOL Proxy started successfully")
        print("\nPress Ctrl+C to stop")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping proxy server...")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Unexpected error")
    finally:
        await proxy_server.stop()
        print("✅ Proxy server stopped")

if __name__ == "__main__":
    asyncio.run(main())
