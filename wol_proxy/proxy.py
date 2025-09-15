"""
TCP Proxy implementation
"""

import asyncio
import logging
import socket
from typing import Optional

logger = logging.getLogger(__name__)

class TCPProxy:
    """TCP proxy that forwards connections between client and target"""
    
    def __init__(self, target_host: str, target_port: int):
        self.target_host = target_host
        self.target_port = target_port
        self.active_connections = 0
        self.connection_timeout = 10  # Default timeout
    
    async def handle_client(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter):
        """Handle a client connection"""
        client_addr = client_writer.get_extra_info('peername')
        logger.debug(f"New TCP client connection from {client_addr}")
        
        target_reader = None
        target_writer = None
        
        try:
            self.active_connections += 1
            
            # Connect to target with timeout
            try:
                target_reader, target_writer = await asyncio.wait_for(
                    asyncio.open_connection(self.target_host, self.target_port),
                    timeout=self.connection_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout connecting to target {self.target_host}:{self.target_port}")
                return
            
            logger.debug(f"Connected to target {self.target_host}:{self.target_port}")
            
            # Start bidirectional forwarding
            await asyncio.gather(
                self._forward_data(client_reader, target_writer, "client->target"),
                self._forward_data(target_reader, client_writer, "target->client"),
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"Error handling TCP client {client_addr}: {e}")
        finally:
            self.active_connections -= 1
            
            # Close connections
            if target_writer:
                try:
                    target_writer.close()
                    await target_writer.wait_closed()
                except Exception as e:
                    logger.debug(f"Error closing target connection: {e}")
            
            try:
                client_writer.close()
                await client_writer.wait_closed()
            except Exception as e:
                logger.debug(f"Error closing client connection: {e}")
            
            logger.debug(f"Closed TCP connection from {client_addr}")
    
    async def _forward_data(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, direction: str):
        """Forward data from reader to writer"""
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                
                writer.write(data)
                await writer.drain()
                
                logger.debug(f"Forwarded {len(data)} bytes ({direction})")
                
        except Exception as e:
            logger.debug(f"Connection closed during forwarding ({direction}): {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                logger.debug(f"Error closing writer in {direction}: {e}")

class UDPProxy:
    """UDP proxy that forwards packets between client and target"""
    
    def __init__(self, target_host: str, target_port: int):
        self.target_host = target_host
        self.target_port = target_port
        self.client_map = {}  # Maps client addresses to target sockets
        self.cleanup_task = None
        self.max_connections = 100  # Limit concurrent UDP connections
    
    async def start(self, bind_port: int):
        """Start the UDP proxy server"""
        self.transport, self.protocol = await asyncio.get_event_loop().create_datagram_endpoint(
            lambda: UDPProxyProtocol(self),
            local_addr=('0.0.0.0', bind_port)
        )
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_stale_connections())
        
        logger.info(f"UDP proxy listening on port {bind_port}")
    
    async def stop(self):
        """Stop the UDP proxy server"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        for client_addr, (sock, _) in self.client_map.items():
            sock.close()
        
        self.client_map.clear()
        
        if hasattr(self, 'transport'):
            self.transport.close()
    
    async def handle_client_packet(self, data: bytes, client_addr: tuple):
        """Handle a packet from a client"""
        logger.debug(f"Received UDP packet from {client_addr}, {len(data)} bytes")
        
        try:
            # Check connection limit
            if len(self.client_map) >= self.max_connections:
                logger.warning(f"UDP connection limit reached ({self.max_connections}), dropping packet from {client_addr}")
                return
            
            # Get or create target socket for this client
            if client_addr not in self.client_map:
                target_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.client_map[client_addr] = (target_sock, asyncio.get_event_loop().time())
                
                # Start listening for responses from target
                asyncio.create_task(self._listen_target_responses(target_sock, client_addr))
            
            target_sock, _ = self.client_map[client_addr]
            self.client_map[client_addr] = (target_sock, asyncio.get_event_loop().time())  # Update timestamp
            
            # Forward packet to target
            target_sock.sendto(data, (self.target_host, self.target_port))
            logger.debug(f"Forwarded UDP packet to {self.target_host}:{self.target_port}")
            
        except Exception as e:
            logger.error(f"Error handling UDP packet from {client_addr}: {e}")
    
    async def _listen_target_responses(self, target_sock, client_addr):
        """Listen for responses from target and forward to client"""
        try:
            # Set socket to non-blocking mode for async operations
            target_sock.setblocking(False)
            
            while True:
                try:
                    data, _ = await asyncio.get_event_loop().sock_recv(target_sock, 8192)
                    
                    # Forward response back to client
                    self.transport.sendto(data, client_addr)
                    logger.debug(f"Forwarded UDP response to {client_addr}, {len(data)} bytes")
                except asyncio.TimeoutError:
                    # No data received, continue listening
                    continue
                except (ConnectionResetError, OSError):
                    # Target closed connection
                    break
                
        except Exception as e:
            logger.debug(f"Target response listener closed for {client_addr}: {e}")
        finally:
            if client_addr in self.client_map:
                del self.client_map[client_addr]
            target_sock.close()
    
    async def _cleanup_stale_connections(self):
        """Cleanup stale UDP connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                current_time = asyncio.get_event_loop().time()
                stale_timeout = 300  # 5 minutes
                
                stale_clients = []
                for client_addr, (sock, timestamp) in self.client_map.items():
                    if current_time - timestamp > stale_timeout:
                        stale_clients.append(client_addr)
                
                for client_addr in stale_clients:
                    sock, _ = self.client_map[client_addr]
                    sock.close()
                    del self.client_map[client_addr]
                    logger.debug(f"Cleaned up stale UDP connection for {client_addr}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in UDP cleanup task: {e}")

class UDPProxyProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler for the proxy"""
    
    def __init__(self, proxy: UDPProxy):
        self.proxy = proxy
    
    def datagram_received(self, data: bytes, addr: tuple):
        """Handle received UDP datagram"""
        asyncio.create_task(self.proxy.handle_client_packet(data, addr))
