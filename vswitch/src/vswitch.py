import asyncio
import json
import logging
from typing import Dict, Set
from aptos_client import AptosBlockchain
from aptos_sdk.account import Account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VSwitch")

class VPort:
    def __init__(self, address: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.address = address
        self.reader = reader
        self.writer = writer

class VSwitch:
    def __init__(self, server_port: int, aptos_client: AptosBlockchain, account: Account):
        self.server_port = server_port
        self.aptos_client = aptos_client
        self.account = account
        self.vports: Dict[str, VPort] = {}  # Map of VPort addresses to VPort objects
        self.mac_to_vport: Dict[str, str] = {}  # Map of MAC addresses to VPort addresses

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        logger.info(f"Connected to {addr}")

        # Authenticate the VPort
        vport_address = await self.authenticate_vport(addr)
        if not vport_address:
            logger.error(f"Failed to authenticate VPort {addr}")
            writer.close()
            await writer.wait_closed()
            return

        # Create and store VPort object
        vport = VPort(vport_address, reader, writer)
        self.vports[vport_address] = vport

        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                message = data.decode()
                logger.info(f"Received {message} from {vport_address}")

                # Process Ethernet frame
                eth_frame = json.loads(message)
                dest_mac = eth_frame.get("destination_mac")
                src_mac = eth_frame.get("source_mac")
                payload = eth_frame.get("payload")

                # Update MAC table on blockchain
                await self.aptos_client.upsert_mac(self.account, src_mac, vport_address)
                self.mac_to_vport[src_mac] = vport_address

                # Lookup destination MAC
                dest_vport_address = await self.aptos_client.lookup_mac(dest_mac)
                if dest_vport_address:
                    # Forward payload to destination VPort
                    await self.forward_payload(dest_vport_address, payload)
                else:
                    # Broadcast to all except source
                    await self.broadcast(payload, exclude=vport_address)

        except asyncio.CancelledError:
            pass
        finally:
            del self.vports[vport_address]
            writer.close()
            await writer.wait_closed()
            logger.info(f"Connection closed {vport_address}")

    async def authenticate_vport(self, addr: str) -> str:
        # Here you would implement the logic to authenticate the VPort
        # For now, we'll just use the address as the VPort address
        vport_address = f"0x{addr[0].replace('.', '')}"
        await self.aptos_client.authenticate_vport(vport_address, self.account)
        return vport_address

    async def forward_payload(self, dest_vport_address: str, payload: dict):
        dest_vport = self.vports.get(dest_vport_address)
        if dest_vport:
            message = json.dumps(payload)
            dest_vport.writer.write(message.encode())
            await dest_vport.writer.drain()
            logger.info(f"Forwarded payload to {dest_vport_address}")
        else:
            logger.warning(f"Destination VPort {dest_vport_address} not found")

    async def broadcast(self, payload: dict, exclude: str):
        message = json.dumps(payload)
        for vport_address, vport in self.vports.items():
            if vport_address != exclude:
                vport.writer.write(message.encode())
                await vport.writer.drain()
        logger.info(f"Broadcasted payload to all VPorts except {exclude}")

    async def start_server(self):
        server = await asyncio.start_server(
            self.handle_client, '0.0.0.0', self.server_port
        )
        addr = server.sockets[0].getsockname()
        logger.info(f"VSwitch server started on {addr}")

        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    import sys
    from aptos_sdk.async_client import RestClient

    if len(sys.argv) != 2:
        print("Usage: python3 vswitch.py <SERVER_PORT>")
        sys.exit(1)

    SERVER_PORT = int(sys.argv[1])

    # Initialize Aptos blockchain client
    NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
    VPORT_MANAGEMENT_ADDRESS = "0x74acd9749ab643f8dc4f85b704ac9bd1ed832e21520cc3088da35a8f9a363ebe"  # Replace with actual address after deployment
    MAC_TABLE_ADDRESS = "0xa993640cb5471ff4a950aaa7ea14e1e05a9722ecd6c4ff5af267474806c8208f"  # Replace with actual address after deployment

    aptos_client = AptosBlockchain(
        node_url=NODE_URL,
        vport_management_address=VPORT_MANAGEMENT_ADDRESS,
        mac_table_address=MAC_TABLE_ADDRESS
    )

    # Create an Account instance
    # In a real-world scenario, you'd want to use a more secure method to handle private keys
    private_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    account = Account.load_key(private_key)

    vswitch = VSwitch(SERVER_PORT, aptos_client, account)
    asyncio.run(vswitch.start_server())
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