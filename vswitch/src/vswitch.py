import asyncio
import logging
import json
import base64
from typing import Dict
import binascii
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("VSwitch")

class VPort:
    def __init__(self, address: str):
        self.address = address

class VSwitch:
    def __init__(self, server_port: int):
        self.server_port = server_port
        self.vports: Dict[str, VPort] = {}
        self.ip_to_vport: Dict[str, str] = {}

    class UDPServerProtocol(asyncio.DatagramProtocol):
        def __init__(self, vswitch):
            self.vswitch = vswitch

        def connection_made(self, transport):
            self.transport = transport

        def datagram_received(self, data, addr):
            asyncio.create_task(self.vswitch.handle_packet(data, addr))

    async def handle_packet(self, data: bytes, addr):
        vport_address = f"{addr[0]}:{addr[1]}"
        logger.info(f"Received {len(data)} bytes from {vport_address}")

        if vport_address not in self.vports:
            self.vports[vport_address] = VPort(vport_address)
            logger.info(f"New VPort connected: {vport_address}")

        try:
            json_data = json.loads(data.decode())
            payload = base64.b64decode(json_data['payload'])
        except (json.JSONDecodeError, KeyError, binascii.Error) as e:
            logger.error(f"Error decoding packet: {e}")
            return

        # Extract IP addresses from the packet
        version = (payload[0] >> 4) & 0xF
        if version == 4:  # IPv4
            src_ip = '.'.join(map(str, payload[12:16]))
            dest_ip = '.'.join(map(str, payload[16:20]))
        elif version == 6:  # IPv6
            src_ip = ':'.join([f"{payload[i]:02x}{payload[i+1]:02x}" for i in range(8, 24, 2)])
            dest_ip = ':'.join([f"{payload[i]:02x}{payload[i+1]:02x}" for i in range(24, 40, 2)])
        else:
            logger.warning(f"Unsupported IP version: {version}")
            return

        logger.debug(f"Processing packet: src_ip={src_ip}, dest_ip={dest_ip}")

        # Update IP table
        self.ip_to_vport[src_ip] = vport_address
        logger.debug(f"Updated IP table: {self.ip_to_vport}")

        # Lookup destination IP
        dest_vport_address = self.ip_to_vport.get(dest_ip)
        if dest_vport_address:
            logger.debug(f"Forwarding to {dest_vport_address}")
            await self.forward_payload(dest_vport_address, payload)
        else:
            logger.debug(f"Destination not found, broadcasting")
            await self.broadcast(payload, exclude=vport_address)

    async def forward_payload(self, dest_vport_address: str, payload: bytes):
        dest_ip, dest_port = dest_vport_address.split(':')
        dest_port = int(dest_port)
        
        # Wrap payload in JSON
        json_payload = json.dumps({
            "payload": base64.b64encode(payload).decode()
        })
        
        self.transport.sendto(json_payload.encode(), (dest_ip, dest_port))
        logger.info(f"Forwarded {len(payload)} bytes to {dest_vport_address}")

    async def broadcast(self, payload: bytes, exclude: str):
        json_payload = json.dumps({
            "payload": base64.b64encode(payload).decode()
        })
        for vport_address, vport in self.vports.items():
            if vport_address != exclude:
                dest_ip, dest_port = vport_address.split(':')
                dest_port = int(dest_port)
                self.transport.sendto(json_payload.encode(), (dest_ip, dest_port))
        logger.info(f"Broadcasted {len(payload)} bytes to all VPorts except {exclude}")

    async def start_server(self):
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: self.UDPServerProtocol(self),
            local_addr=('0.0.0.0', self.server_port)
        )
        self.transport = transport

        logger.info(f"VSwitch UDP server started on 0.0.0.0:{self.server_port}")

        try:
            await asyncio.Future()  # Run forever
        finally:
            transport.close()

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 vswitch.py <SERVER_PORT>")
        sys.exit(1)

    SERVER_PORT = int(sys.argv[1])

    vswitch = VSwitch(SERVER_PORT)
    asyncio.run(vswitch.start_server())
