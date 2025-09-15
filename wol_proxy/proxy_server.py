"""
Main proxy server that coordinates WOL and proxy functionality
"""

import asyncio
import logging
import socket
from typing import Dict, List

from .config import Config, ServiceConfig
from .wol_manager import WOLManager
from .proxy import TCPProxy, UDPProxy

logger = logging.getLogger(__name__)

class ProxyServer:
    """Main proxy server that manages all services"""
    
    def __init__(self, config: Config):
        self.config = config
        self.wol_manager = WOLManager()
        self.tcp_servers: Dict[int, asyncio.Server] = {}
        self.udp_proxies: Dict[int, UDPProxy] = {}
        self.health_check_tasks: List[asyncio.Task] = []
        self.service_status: Dict[int, bool] = {}  # port -> is_available
    
    async def start(self):
        """Start all proxy services"""
        logger.info("Starting proxy server")
        
        for service in self.config.services:
            try:
                await self._start_service(service)
                
                # Start health check task
                task = asyncio.create_task(self._health_check_loop(service))
                self.health_check_tasks.append(task)
                
            except Exception as e:
                logger.error(f"Failed to start service {service.proxy_port}: {e}")
        
        logger.info(f"Started {len(self.config.services)} proxy services")
    
    async def stop(self):
        """Stop all proxy services"""
        logger.info("Stopping proxy server")
        
        # Cancel health check tasks
        for task in self.health_check_tasks:
            task.cancel()
        
        # Stop TCP servers
        for port, server in self.tcp_servers.items():
            server.close()
            await server.wait_closed()
            logger.info(f"Stopped TCP server on port {port}")
        
        # Stop UDP proxies
        for port, proxy in self.udp_proxies.items():
            await proxy.stop()
            logger.info(f"Stopped UDP proxy on port {port}")
        
        self.tcp_servers.clear()
        self.udp_proxies.clear()
        self.health_check_tasks.clear()
    
    async def _start_service(self, service: ServiceConfig):
        """Start a single proxy service"""
        logger.info(f"Starting {service.protocol.upper()} proxy on port {service.proxy_port} -> {service.target_host}:{service.target_port}")
        
        if service.protocol == "tcp":
            await self._start_tcp_service(service)
        elif service.protocol == "udp":
            await self._start_udp_service(service)
    
    async def _start_tcp_service(self, service: ServiceConfig):
        """Start a TCP proxy service"""
        async def handle_client(reader, writer):
            await self._handle_tcp_client(service, reader, writer)
        
        server = await asyncio.start_server(
            handle_client,
            '0.0.0.0',
            service.proxy_port
        )
        
        self.tcp_servers[service.proxy_port] = server
        logger.info(f"TCP proxy listening on port {service.proxy_port}")
    
    async def _start_udp_service(self, service: ServiceConfig):
        """Start a UDP proxy service"""
        proxy = UDPProxy(service.target_host, service.target_port)
        await proxy.start(service.proxy_port)
        self.udp_proxies[service.proxy_port] = proxy
    
    async def _handle_tcp_client(self, service: ServiceConfig, client_reader, client_writer):
        """Handle a TCP client connection"""
        client_addr = client_writer.get_extra_info('peername')
        logger.info(f"New TCP connection from {client_addr} to {service.target_host}:{service.target_port}")
        
        try:
            # Check if target is available
            if not await self._ensure_target_available(service):
                logger.warning(f"Target {service.target_host}:{service.target_port} is not available")
                client_writer.close()
                await client_writer.wait_closed()
                return
            
            # Create proxy and handle connection
            proxy = TCPProxy(service.target_host, service.target_port)
            proxy.connection_timeout = service.connection_timeout
            await proxy.handle_client(client_reader, client_writer)
            
        except Exception as e:
            logger.error(f"Error handling TCP client from {client_addr}: {e}")
            try:
                client_writer.close()
                await client_writer.wait_closed()
            except:
                pass
    
    async def _ensure_target_available(self, service: ServiceConfig) -> bool:
        """Ensure the target service is available, waking it up if necessary"""
        # First check if target is already available
        if await self._check_target_availability(service.target_host, service.target_port, service.connection_timeout):
            return True
        
        logger.info(f"Target {service.target_host}:{service.target_port} is not available, attempting WOL")
        
        # Try to wake up the target
        success = await self.wol_manager.wake_host(
            service.mac_address,
            service.target_host,
            service.target_port,
            service.wake_timeout
        )
        
        return success
    
    async def _check_target_availability(self, host: str, port: int, timeout: int = 5) -> bool:
        """Check if target service is available"""
        try:
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False
        except Exception as e:
            logger.debug(f"Unexpected error checking {host}:{port}: {e}")
            return False
    
    async def _health_check_loop(self, service: ServiceConfig):
        """Continuously monitor target service health"""
        logger.info(f"Starting health check for {service.target_host}:{service.target_port}")
        
        while True:
            try:
                is_available = await self._check_target_availability(
                    service.target_host, 
                    service.target_port,
                    service.connection_timeout
                )
                
                # Update status
                prev_status = self.service_status.get(service.proxy_port, None)
                self.service_status[service.proxy_port] = is_available
                
                # Log status changes
                if prev_status is not None and prev_status != is_available:
                    status_str = "available" if is_available else "unavailable"
                    logger.info(f"Target {service.target_host}:{service.target_port} is now {status_str}")
                
                await asyncio.sleep(service.health_check_interval)
                
            except asyncio.CancelledError:
                logger.info(f"Health check cancelled for {service.target_host}:{service.target_port}")
                break
            except Exception as e:
                logger.error(f"Error in health check for {service.target_host}:{service.target_port}: {e}")
                await asyncio.sleep(service.health_check_interval)
