"""
Configuration management for WOL Proxy
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """Configuration for a single proxied service"""
    target_host: str
    target_port: int
    proxy_port: int
    mac_address: str
    wake_timeout: int = 60
    health_check_interval: int = 10
    protocol: str = "tcp"
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.target_host:
            raise ValueError("target_host is required")
        
        if not (1 <= self.target_port <= 65535):
            raise ValueError("target_port must be between 1 and 65535")
        
        if not (1 <= self.proxy_port <= 65535):
            raise ValueError("proxy_port must be between 1 and 65535")
        
        if not self.mac_address:
            raise ValueError("mac_address is required")
        
        # Validate MAC address format
        mac_parts = self.mac_address.replace(":", "").replace("-", "")
        if len(mac_parts) != 12 or not all(c in "0123456789abcdefABCDEF" for c in mac_parts):
            raise ValueError("Invalid MAC address format")
        
        if self.protocol not in ["tcp", "udp"]:
            raise ValueError("protocol must be 'tcp' or 'udp'")
        
        if not (30 <= self.wake_timeout <= 300):
            raise ValueError("wake_timeout must be between 30 and 300 seconds")
        
        if not (5 <= self.health_check_interval <= 60):
            raise ValueError("health_check_interval must be between 5 and 60 seconds")

class Config:
    """Main configuration class"""
    
    def __init__(self, config_data: dict):
        self.log_level = config_data.get("log_level", "info")
        self.services: List[ServiceConfig] = []
        
        # Parse services configuration
        services_data = config_data.get("services", [])
        for service_data in services_data:
            try:
                service = ServiceConfig(**service_data)
                self.services.append(service)
                logger.info(f"Configured service: {service.target_host}:{service.target_port} -> proxy port {service.proxy_port}")
            except Exception as e:
                logger.error(f"Invalid service configuration: {e}")
                raise
        
        if not self.services:
            logger.warning("No services configured")
    
    def get_service_by_port(self, port: int) -> Optional[ServiceConfig]:
        """Get service configuration by proxy port"""
        for service in self.services:
            if service.proxy_port == port:
                return service
        return None
