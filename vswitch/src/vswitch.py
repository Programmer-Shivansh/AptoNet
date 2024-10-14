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
# import asyncio
# import logging
# import struct
# from typing import Dict
# from aptos_client import AptosBlockchain
# from aptos_sdk.account import Account
# import base64
# import json
# import binascii

# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger("VSwitch")

# class VPort:
#     def __init__(self, address: str):
#         self.address = address

# class VSwitch:
#     def __init__(self, server_port: int, aptos_client: AptosBlockchain, account: Account):
#         self.server_port = server_port
#         self.aptos_client = aptos_client
#         self.account = account
#         self.vports: Dict[str, VPort] = {}
#         self.ip_to_vport: Dict[str, str] = {}

#     class UDPServerProtocol(asyncio.DatagramProtocol):
#         def __init__(self, vswitch):
#             self.vswitch = vswitch

#         def connection_made(self, transport):
#             self.transport = transport

#         def datagram_received(self, data, addr):
#             asyncio.create_task(self.vswitch.handle_packet(data, addr))

#     # async def handle_packet(self, data: bytes, addr):
#     #     vport_address = f"0x{addr[0].replace('.', '')}"
#     #     logger.info(f"Received {len(data)} bytes from {vport_address}")

#     #     if vport_address not in self.vports:
#     #         self.vports[vport_address] = VPort(vport_address)
#     #         logger.info(f"New VPort connected: {vport_address}")

#     #     # Extract IP addresses from the packet
#     #     version = (data[0] >> 4) & 0xF
#     #     if version == 4:  # IPv4
#     #         src_ip = '.'.join(map(str, data[12:16]))
#     #         dest_ip = '.'.join(map(str, data[16:20]))
#     #     elif version == 6:  # IPv6
#     #         src_ip = ':'.join([f"{data[i]:02x}{data[i+1]:02x}" for i in range(8, 24, 2)])
#     #         dest_ip = ':'.join([f"{data[i]:02x}{data[i+1]:02x}" for i in range(24, 40, 2)])
#     #     else:
#     #         logger.warning(f"Unsupported IP version: {version}")
#     #         return

#     #     logger.debug(f"Processing packet: src_ip={src_ip}, dest_ip={dest_ip}")

#     #     # Update IP table
#     #     self.ip_to_vport[src_ip] = vport_address
#     #     logger.debug(f"Updated IP table: {self.ip_to_vport}")

#     #     # Lookup destination IP
#     #     dest_vport_address = self.ip_to_vport.get(dest_ip)
#     #     if dest_vport_address:
#     #         logger.debug(f"Forwarding to {dest_vport_address}")
#     #         await self.forward_payload(dest_vport_address, data)
#     #     else:
#     #         logger.debug(f"Broadcasting to all except {vport_address}")
#     #         await self.broadcast(data, exclude=vport_address)
#     async def handle_packet(self, data: bytes, addr):
#         vport_address = f"{addr[0]}:{addr[1]}"
#         logger.info(f"Received {len(data)} bytes from {vport_address}")

#         if vport_address not in self.vports:
#             self.vports[vport_address] = VPort(vport_address)
#             logger.info(f"New VPort connected: {vport_address}")

#         try:
#             json_data = json.loads(data.decode())
#             payload = base64.b64decode(json_data['payload'])
#         except (json.JSONDecodeError, KeyError, binascii.Error) as e:
#             logger.error(f"Error decoding packet: {e}")
#             return

#         # Extract IP addresses from the packet
#         version = (payload[0] >> 4) & 0xF
#         if version == 4:  # IPv4
#             src_ip = '.'.join(map(str, payload[12:16]))
#             dest_ip = '.'.join(map(str, payload[16:20]))
#         elif version == 6:  # IPv6
#             src_ip = ':'.join([f"{payload[i]:02x}{payload[i+1]:02x}" for i in range(8, 24, 2)])
#             dest_ip = ':'.join([f"{payload[i]:02x}{payload[i+1]:02x}" for i in range(24, 40, 2)])
#         else:
#             logger.warning(f"Unsupported IP version: {version}")
#             return

#         logger.debug(f"Processing packet: src_ip={src_ip}, dest_ip={dest_ip}")

#         # Update IP table
#         self.ip_to_vport[src_ip] = vport_address
#         logger.debug(f"Updated IP table: {self.ip_to_vport}")

#         # Lookup destination IP
#         dest_vport_address = self.ip_to_vport.get(dest_ip)
#         if dest_vport_address:
#             logger.debug(f"Forwarding to {dest_vport_address}")
#             await self.forward_payload(dest_vport_address, payload)
#         else:
#             logger.debug(f"Destination not found, sending back to source")
#             await self.forward_payload(vport_address, payload)

#     async def forward_payload(self, dest_vport_address: str, payload: bytes):
#         dest_ip, dest_port = dest_vport_address.split(':')
#         dest_port = int(dest_port)
        
#         # Wrap payload in JSON
#         json_payload = json.dumps({
#             "payload": base64.b64encode(payload).decode()
#         })
        
#         self.transport.sendto(json_payload.encode(), (dest_ip, dest_port))
#         logger.info(f"Forwarded {len(payload)} bytes to {dest_vport_address}")

#     # async def forward_payload(self, dest_vport_address: str, payload: bytes):
#     #     dest_vport = self.vports.get(dest_vport_address)
#     #     if dest_vport:
#     #         self.transport.sendto(payload, (dest_vport.address.split('x')[1], self.server_port))
#     #         logger.info(f"Forwarded {len(payload)} bytes to {dest_vport_address}")
#     #     else:
#     #         logger.warning(f"Destination VPort {dest_vport_address} not found")

#     async def broadcast(self, payload: bytes, exclude: str):
#         for vport_address, vport in self.vports.items():
#             if vport_address != exclude:
#                 self.transport.sendto(payload, (vport.address.split('x')[1], self.server_port))
#         logger.info(f"Broadcasted {len(payload)} bytes to all VPorts except {exclude}")

#     async def start_server(self):
#         loop = asyncio.get_running_loop()
#         transport, protocol = await loop.create_datagram_endpoint(
#             lambda: self.UDPServerProtocol(self),
#             local_addr=('0.0.0.0', self.server_port)
#         )
#         self.transport = transport

#         logger.info(f"VSwitch UDP server started on 0.0.0.0:{self.server_port}")

#         try:
#             await asyncio.Future()  # Run forever
#         finally:
#             transport.close()

# if __name__ == "__main__":
#     import sys
#     from aptos_sdk.async_client import RestClient

#     if len(sys.argv) != 2:
#         print("Usage: python3 vswitch.py <SERVER_PORT>")
#         sys.exit(1)

#     SERVER_PORT = int(sys.argv[1])

#     # Initialize Aptos blockchain client (simplified for debugging)
#     NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
#     VPORT_MANAGEMENT_ADDRESS = "0x5f6f6140fc53d3e6951a85ae4358f7f3646232a7a0fa347fbceb39b93194e5ba"
#     MAC_TABLE_ADDRESS = "0x125a3d5f49675dd952cac71c50fd2cdaa6a3c53e2816428573b06af6e18dd564"

#     aptos_client = AptosBlockchain(
#         node_url=NODE_URL,
#         vport_management_address=VPORT_MANAGEMENT_ADDRESS,
#         mac_table_address=MAC_TABLE_ADDRESS
#     )

#     # Create an Account instance (simplified for debugging)
#     private_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
#     account = Account.load_key(private_key)

#     vswitch = VSwitch(SERVER_PORT, aptos_client, account)
#     asyncio.run(vswitch.start_server())
# import asyncio
# import json
# import logging
# from typing import Dict, Set
# from aptos_client import AptosBlockchain
# from aptos_sdk.account import Account

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger("VSwitch")

# class VPort:
#     def __init__(self, address: str):
#         self.address = address
# class VSwitch:
#     def __init__(self, server_port: int, aptos_client: AptosBlockchain, account: Account):
#         self.server_port = server_port
#         self.aptos_client = aptos_client
#         self.account = account
#         self.vports: Dict[str, VPort] = {}
#         self.mac_to_vport: Dict[str, str] = {}

#     class UDPServerProtocol(asyncio.DatagramProtocol):
#         def __init__(self, vswitch):
#             self.vswitch = vswitch

#         def connection_made(self, transport):
#             self.transport = transport

#         def datagram_received(self, data, addr):
#             asyncio.create_task(self.vswitch.handle_packet(data, addr))

#     async def handle_packet(self, data: bytes, addr):
#         vport_address = f"0x{addr[0].replace('.', '')}"
#         logger.info(f"Received {len(data)} bytes from {vport_address}")

#         if vport_address not in self.vports:
#             self.vports[vport_address] = VPort(vport_address)
#             logger.info(f"New VPort connected: {vport_address}")

#         # Extract Ethernet frame details (simplified)
#         dest_mac = data[0:6].hex()
#         src_mac = data[6:12].hex()

#         logger.debug(f"Processing frame: dest_mac={dest_mac}, src_mac={src_mac}")

#         # Update MAC table (simplified for debugging)
#         self.mac_to_vport[src_mac] = vport_address
#         logger.debug(f"Updated MAC table: {self.mac_to_vport}")

#         # Lookup destination MAC
#         dest_vport_address = self.mac_to_vport.get(dest_mac)
#         if dest_vport_address:
#             logger.debug(f"Forwarding to {dest_vport_address}")
#             await self.forward_payload(dest_vport_address, data)
#         else:
#             logger.debug(f"Broadcasting to all except {vport_address}")
#             await self.broadcast(data, exclude=vport_address)

#     async def forward_payload(self, dest_vport_address: str, payload: bytes):
#         dest_vport = self.vports.get(dest_vport_address)
#         if dest_vport:
#             self.transport.sendto(payload, (dest_vport.address, self.server_port))
#             logger.info(f"Forwarded {len(payload)} bytes to {dest_vport_address}")
#         else:
#             logger.warning(f"Destination VPort {dest_vport_address} not found")

#     async def broadcast(self, payload: bytes, exclude: str):
#         for vport_address, vport in self.vports.items():
#             if vport_address != exclude:
#                 self.transport.sendto(payload, (vport.address, self.server_port))
#         logger.info(f"Broadcasted {len(payload)} bytes to all VPorts except {exclude}")

#     async def start_server(self):
#         loop = asyncio.get_running_loop()
#         transport, protocol = await loop.create_datagram_endpoint(
#             lambda: self.UDPServerProtocol(self),
#             local_addr=('0.0.0.0', self.server_port)
#         )
#         self.transport = transport

#         logger.info(f"VSwitch UDP server started on 0.0.0.0:{self.server_port}")

#         try:
#             await asyncio.Future()  # Run forever
#         finally:
#             transport.close()

# if __name__ == "__main__":
#     import sys
#     from aptos_sdk.async_client import RestClient

#     if len(sys.argv) != 2:
#         print("Usage: python3 vswitch.py <SERVER_PORT>")
#         sys.exit(1)

#     SERVER_PORT = int(sys.argv[1])

#     # Initialize Aptos blockchain client (simplified for debugging)
#     NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
#     VPORT_MANAGEMENT_ADDRESS = "0x5f6f6140fc53d3e6951a85ae4358f7f3646232a7a0fa347fbceb39b93194e5ba"
#     MAC_TABLE_ADDRESS = "0x125a3d5f49675dd952cac71c50fd2cdaa6a3c53e2816428573b06af6e18dd564"

#     aptos_client = AptosBlockchain(
#         node_url=NODE_URL,
#         vport_management_address=VPORT_MANAGEMENT_ADDRESS,
#         mac_table_address=MAC_TABLE_ADDRESS
#     )

#     # Create an Account instance (simplified for debugging)
#     private_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
#     account = Account.load_key(private_key)

#     vswitch = VSwitch(SERVER_PORT, aptos_client, account)
#     asyncio.run(vswitch.start_server())

# class VSwitch:
#     def __init__(self, server_port: int, aptos_client: AptosBlockchain, account: Account):
#         self.server_port = server_port
#         self.aptos_client = aptos_client
#         self.account = account
#         self.vports: Dict[str, VPort] = {}
#         self.mac_to_vport: Dict[str, str] = {}

#     async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
#         addr = writer.get_extra_info('peername')
#         logger.info(f"Connected to {addr}")

#         # Authenticate the VPort (simplified for debugging)
#         vport_address = f"0x{addr[0].replace('.', '')}"
#         logger.debug(f"Authenticated VPort: {vport_address}")

#         # Create and store VPort object
#         vport = VPort(vport_address, reader, writer)
#         self.vports[vport_address] = vport

#         try:
#             while True:
#                 data = await reader.read(2048)
#                 if not data:
#                     break
#                 message = data.decode()
#                 logger.debug(f"Received raw data: {message}")

#                 try:
#                     eth_frame = json.loads(message)
#                     logger.info(f"Received {eth_frame} from {vport_address}")

#                     dest_mac = eth_frame.get("destination_mac")
#                     src_mac = eth_frame.get("source_mac")
#                     payload = eth_frame.get("payload")

#                     logger.debug(f"Processing frame: dest_mac={dest_mac}, src_mac={src_mac}, payload={payload}")

#                     # Update MAC table (simplified for debugging)
#                     self.mac_to_vport[src_mac] = vport_address
#                     logger.debug(f"Updated MAC table: {self.mac_to_vport}")

#                     # Lookup destination MAC
#                     dest_vport_address = self.mac_to_vport.get(dest_mac)
#                     if dest_vport_address:
#                         logger.debug(f"Forwarding to {dest_vport_address}")
#                         await self.forward_payload(dest_vport_address, payload)
#                     else:
#                         logger.debug(f"Broadcasting to all except {vport_address}")
#                         await self.broadcast(payload, exclude=vport_address)

#                 except json.JSONDecodeError:
#                     logger.error(f"Invalid JSON received: {message}")

#         except asyncio.CancelledError:
#             pass
#         finally:
#             del self.vports[vport_address]
#             writer.close()
#             await writer.wait_closed()
#             logger.info(f"Connection closed {vport_address}")

#     async def forward_payload(self, dest_vport_address: str, payload: dict):
#         dest_vport = self.vports.get(dest_vport_address)
#         if dest_vport:
#             message = json.dumps(payload)
#             dest_vport.writer.write(message.encode())
#             await dest_vport.writer.drain()
#             logger.info(f"Forwarded payload to {dest_vport_address}")
#         else:
#             logger.warning(f"Destination VPort {dest_vport_address} not found")

#     async def broadcast(self, payload: dict, exclude: str):
#         message = json.dumps(payload)
#         for vport_address, vport in self.vports.items():
#             if vport_address != exclude:
#                 vport.writer.write(message.encode())
#                 await vport.writer.drain()
#         logger.info(f"Broadcasted payload to all VPorts except {exclude}")

#     async def start_server(self):
#         server = await asyncio.start_server(
#             self.handle_client, '0.0.0.0', self.server_port
#         )
#         addr = server.sockets[0].getsockname()
#         logger.info(f"VSwitch server started on {addr}")

#         async with server:
#             print("Waiting for connections...")

#             await server.serve_forever()

# if __name__ == "__main__":
#     import sys
#     from aptos_sdk.async_client import RestClient

#     if len(sys.argv) != 2:
#         print("Usage: python3 vswitch.py <SERVER_PORT>")
#         sys.exit(1)

#     SERVER_PORT = int(sys.argv[1])

#     # Initialize Aptos blockchain client (simplified for debugging)
#     NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
#     VPORT_MANAGEMENT_ADDRESS = "0x5f6f6140fc53d3e6951a85ae4358f7f3646232a7a0fa347fbceb39b93194e5ba"
#     MAC_TABLE_ADDRESS = "0x125a3d5f49675dd952cac71c50fd2cdaa6a3c53e2816428573b06af6e18dd564"

#     aptos_client = AptosBlockchain(
#         node_url=NODE_URL,
#         vport_management_address=VPORT_MANAGEMENT_ADDRESS,
#         mac_table_address=MAC_TABLE_ADDRESS
#     )

#     # Create an Account instance (simplified for debugging)
#     private_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
#     account = Account.load_key(private_key)

#     vswitch = VSwitch(SERVER_PORT, aptos_client, account)
#     asyncio.run(vswitch.start_server())

# import asyncio
# import json
# import logging
# from typing import Dict, Set
# from aptos_client import AptosBlockchain
# from aptos_sdk.account import Account

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("VSwitch")

# class VPort:
#     def __init__(self, address: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
#         self.address = address
#         self.reader = reader
#         self.writer = writer

# class VSwitch:
#     def __init__(self, server_port: int, aptos_client: AptosBlockchain, account: Account):
#         self.server_port = server_port
#         self.aptos_client = aptos_client
#         self.account = account
#         self.vports: Dict[str, VPort] = {}  # Map of VPort addresses to VPort objects
#         self.mac_to_vport: Dict[str, str] = {}  # Map of MAC addresses to VPort addresses

#     async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
#         addr = writer.get_extra_info('peername')
#         logger.info(f"Connected to {addr}")

#         # Authenticate the VPort
#         vport_address = await self.authenticate_vport(addr)
#         if not vport_address:
#             logger.error(f"Failed to authenticate VPort {addr}")
#             writer.close()
#             await writer.wait_closed()
#             return

#         # Create and store VPort object
#         vport = VPort(vport_address, reader, writer)
#         self.vports[vport_address] = vport

#         try:
#             while True:
#                 data = await reader.read(1024)
#                 if not data:
#                     break
#                 message = data.decode()
#                 logger.info(f"Received {message} from {vport_address}")

#                 # Process Ethernet frame
#                 eth_frame = json.loads(message)
#                 dest_mac = eth_frame.get("destination_mac")
#                 src_mac = eth_frame.get("source_mac")
#                 payload = eth_frame.get("payload")

#                 # Update MAC table on blockchain
#                 await self.aptos_client.upsert_mac(self.account, src_mac, vport_address)
#                 self.mac_to_vport[src_mac] = vport_address

#                 # Lookup destination MAC
#                 dest_vport_address = await self.aptos_client.lookup_mac(dest_mac)
#                 if dest_vport_address:
#                     # Forward payload to destination VPort
#                     await self.forward_payload(dest_vport_address, payload)
#                 else:
#                     # Broadcast to all except source
#                     await self.broadcast(payload, exclude=vport_address)

#         except asyncio.CancelledError:
#             pass
#         finally:
#             del self.vports[vport_address]
#             writer.close()
#             await writer.wait_closed()
#             logger.info(f"Connection closed {vport_address}")

#     async def authenticate_vport(self, addr: str) -> str:
#         # Here you would implement the logic to authenticate the VPort
#         # For now, we'll just use the address as the VPort address
#         vport_address = f"0x{addr[0].replace('.', '')}"
#         await self.aptos_client.authenticate_vport(vport_address, self.account)
#         return vport_address

#     async def forward_payload(self, dest_vport_address: str, payload: dict):
#         dest_vport = self.vports.get(dest_vport_address)
#         if dest_vport:
#             message = json.dumps(payload)
#             dest_vport.writer.write(message.encode())
#             await dest_vport.writer.drain()
#             logger.info(f"Forwarded payload to {dest_vport_address}")
#         else:
#             logger.warning(f"Destination VPort {dest_vport_address} not found")

#     async def broadcast(self, payload: dict, exclude: str):
#         message = json.dumps(payload)
#         for vport_address, vport in self.vports.items():
#             if vport_address != exclude:
#                 vport.writer.write(message.encode())
#                 await vport.writer.drain()
#         logger.info(f"Broadcasted payload to all VPorts except {exclude}")

#     async def start_server(self):
#         server = await asyncio.start_server(
#             self.handle_client, '0.0.0.0', self.server_port
#         )
#         addr = server.sockets[0].getsockname()
#         logger.info(f"VSwitch server started on {addr}")

#         async with server:
#             await server.serve_forever()

# if __name__ == "__main__":
#     import sys
#     from aptos_sdk.async_client import RestClient

#     if len(sys.argv) != 2:
#         print("Usage: python3 vswitch.py <SERVER_PORT>")
#         sys.exit(1)

#     SERVER_PORT = int(sys.argv[1])

#     # Initialize Aptos blockchain client
#     NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
#     VPORT_MANAGEMENT_ADDRESS = "0x5f6f6140fc53d3e6951a85ae4358f7f3646232a7a0fa347fbceb39b93194e5ba"  # Replace with actual address after deployment
#     MAC_TABLE_ADDRESS = "0x125a3d5f49675dd952cac71c50fd2cdaa6a3c53e2816428573b06af6e18dd564"  # Replace with actual address after deployment

#     aptos_client = AptosBlockchain(
#         node_url=NODE_URL,
#         vport_management_address=VPORT_MANAGEMENT_ADDRESS,
#         mac_table_address=MAC_TABLE_ADDRESS
#     )

#     # Create an Account instance
#     # In a real-world scenario, you'd want to use a more secure method to handle private keys
#     private_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
#     account = Account.load_key(private_key)

#     vswitch = VSwitch(SERVER_PORT, aptos_client, account)
#     asyncio.run(vswitch.start_server())
# import asyncio
# import socket
# import json
# import logging
# from aptos_client import AptosBlockchain
# from aptos_sdk.account import Account

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("VSwitch")

# class VSwitch:
#     def __init__(self, server_port, aptos_client: AptosBlockchain, account: Account):
#         self.server_port = server_port
#         self.aptos_client = aptos_client
#         self.account = account
#         self.mac_table = {}  # In decentralized setup, this will be fetched from blockchain

#     async def handle_client(self, reader, writer):
#         addr = writer.get_extra_info('peername')
#         logger.info(f"Connected to {addr}")

#         while True:
#             data = await reader.read(1024)
#             if not data:
#                 break
#             message = data.decode()
#             logger.info(f"Received {message} from {addr}")

#             # Process Ethernet frame (simplified)
#             eth_frame = json.loads(message)
#             dest_mac = eth_frame.get("destination_mac")
#             src_mac = eth_frame.get("source_mac")
#             payload = eth_frame.get("payload")

#             # Update MAC table on blockchain
#             # Assuming src_mac is already authenticated and mapped to VPort
#             await self.aptos_client.upsert_mac(self.account, src_mac, addr)

#             # Lookup destination MAC
#             dest_vport = await self.aptos_client.lookup_mac(dest_mac)
#             if dest_vport:
#                 # Forward payload to destination VPort
#                 await self.forward_payload(dest_vport, payload)
#             else:
#                 # Broadcast to all except source
#                 await self.broadcast(payload, exclude=addr)

#         writer.close()
#         await writer.wait_closed()
#         logger.info(f"Connection closed {addr}")

#     async def forward_payload(self, dest_vport, payload):
#         # Implement forwarding logic to specific VPort
#         pass

#     async def broadcast(self, payload, exclude=None):
#         # Implement broadcasting to all VPorts except 'exclude'
#         pass

#     async def start_server(self):
#         server = await asyncio.start_server(
#             self.handle_client, '0.0.0.0', self.server_port
#         )
#         addr = server.sockets[0].getsockname()
#         logger.info(f"VSwitch server started on {addr}")

#         async with server:
#             await server.serve_forever()

# if __name__ == "__main__":
#     import sys

#     if len(sys.argv) != 2:
#         print("Usage: python3 vswitch.py <SERVER_PORT>")
#         sys.exit(1)

#     SERVER_PORT = int(sys.argv[1])

#     # Initialize Aptos blockchain client
#     NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"  # Replace with your node URL
#     VPORT_MANAGEMENT_ADDRESS = "0xVPORT"  # Replace with actual address after deployment
#     MAC_TABLE_ADDRESS = "0xMACTABLE"  # Replace with actual address after deployment

#     aptos_client = AptosBlockchain(
#         node_url=NODE_URL,
#         vport_management_address=VPORT_MANAGEMENT_ADDRESS,
#         mac_table_address=MAC_TABLE_ADDRESS
#     )

#     # Create an Account instance (you'll need to implement this)
#     account = Account.load_key("path/to/your/private_key")  # Replace with actual key loading logic

#     vswitch = VSwitch(SERVER_PORT, aptos_client, account)
#     asyncio.run(vswitch.start_server())