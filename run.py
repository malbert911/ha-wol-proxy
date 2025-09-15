#!/usr/bin/env python3
"""
WOL Proxy Add-on for Home Assistant
Main entry point
"""

import asyncio
import logging
import sys
import signal
import yaml
import json
from pathlib import Path

from wol_proxy.proxy_server import ProxyServer
from wol_proxy.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from Home Assistant add-on options"""
    try:
        # Try to load from Home Assistant add-on options
        options_file = Path('/data/options.json')
        if options_file.exists():
            with open(options_file, 'r') as f:
                config_data = json.load(f)
            logger.info("Loaded configuration from Home Assistant add-on options")
        else:
            # Fallback for development/testing
            config_file = Path('config.yaml')
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                config_data = config_data.get('options', {})
                logger.info("Loaded configuration from config.yaml (development mode)")
            else:
                logger.error("No configuration file found")
                return None
        
        return Config(config_data)
    
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return None

async def main():
    """Main application entry point"""
    logger.info("Starting WOL Proxy Add-on")
    
    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration, exiting")
        sys.exit(1)
    
    # Set log level
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(log_level)
    logger.info(f"Log level set to {config.log_level}")
    
    # Validate configuration
    if not config.services:
        logger.error("No services configured")
        sys.exit(1)
    
    logger.info(f"Configured {len(config.services)} services")
    
    # Create and start proxy server
    proxy_server = ProxyServer(config)
    
    # Setup signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        shutdown_event.set()
    
    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        asyncio.get_event_loop().add_signal_handler(sig, signal_handler)
    
    try:
        await proxy_server.start()
        logger.info("WOL Proxy started successfully")
        
        # Wait for shutdown signal
        await shutdown_event.wait()
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Shutting down gracefully...")
        await proxy_server.stop()
        logger.info("WOL Proxy stopped")

if __name__ == "__main__":
    asyncio.run(main())
