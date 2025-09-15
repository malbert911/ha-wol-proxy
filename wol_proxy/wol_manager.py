"""
Wake-on-LAN functionality
"""

import asyncio
import logging
import socket
from wakeonlan import send_magic_packet

logger = logging.getLogger(__name__)

class WOLManager:
    """Manages Wake-on-LAN operations"""
    
    def __init__(self):
        self._waking_hosts = set()
    
    async def wake_host(self, mac_address: str, target_host: str, target_port: int, timeout: int = 60) -> bool:
        """
        Wake up a host using WOL and wait for it to be available
        
        Args:
            mac_address: MAC address of the target host
            target_host: IP address or hostname of the target
            target_port: Port to check for availability
            timeout: Maximum time to wait for host to wake up
            
        Returns:
            True if host woke up successfully, False otherwise
        """
        host_key = f"{target_host}:{target_port}"
        
        # Check if we're already trying to wake this host
        if host_key in self._waking_hosts:
            logger.info(f"Already attempting to wake {target_host}, waiting...")
            return await self._wait_for_host(target_host, target_port, timeout)
        
        # Check if host is already awake
        if await self._check_host_availability(target_host, target_port):
            logger.debug(f"Host {target_host}:{target_port} is already awake")
            return True
        
        try:
            self._waking_hosts.add(host_key)
            logger.info(f"Sending WOL packet to {mac_address} for host {target_host}")
            
            # Send WOL packet
            send_magic_packet(mac_address)
            
            # Wait for host to wake up
            logger.info(f"Waiting for {target_host}:{target_port} to become available (timeout: {timeout}s)")
            success = await self._wait_for_host(target_host, target_port, timeout)
            
            if success:
                logger.info(f"Successfully woke up {target_host}:{target_port}")
            else:
                logger.warning(f"Failed to wake up {target_host}:{target_port} within {timeout} seconds")
            
            return success
            
        except Exception as e:
            logger.error(f"Error waking host {target_host}: {e}")
            return False
        finally:
            self._waking_hosts.discard(host_key)
    
    async def _wait_for_host(self, host: str, port: int, timeout: int) -> bool:
        """Wait for a host to become available"""
        start_time = asyncio.get_event_loop().time()
        check_interval = 2  # Check every 2 seconds
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            if await self._check_host_availability(host, port):
                return True
            await asyncio.sleep(check_interval)
        
        return False
    
    async def _check_host_availability(self, host: str, port: int) -> bool:
        """Check if a host is available on the specified port"""
        try:
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=5)
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False
        except Exception as e:
            logger.debug(f"Unexpected error checking {host}:{port}: {e}")
            return False
