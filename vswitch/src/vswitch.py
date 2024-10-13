import asyncio
import socket
import json
import logging
from aptos_client import AptosBlockchain
from aptos_sdk.account import Account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VSwitch")

class VSwitch:
    def __init__(self, server_port, aptos_client: AptosBlockchain):
        self.server_port = server_port
        self.aptos_client = aptos_client
        self.mac_table = {}  # In decentralized setup, this will be fetched from blockchain

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        logger.info(f"Connected to {addr}")

        while True:
            data = await reader.read(1024)
            if not data:
                break
            message = data.decode()
            logger.info(f"Received {message} from {addr}")

            # Process Ethernet frame (simplified)
            eth_frame = json.loads(message)
            dest_mac = eth_frame.get("destination_mac")
            src_mac = eth_frame.get("source_mac")
            payload = eth_frame.get("payload")

            # Update MAC table on blockchain
            # Assuming src_mac is already authenticated and mapped to VPort
            self.aptos_client.upsert_mac(self.aptos_client.account, src_mac, addr)

            # Lookup destination MAC
            dest_vport = self.aptos_client.lookup_mac(dest_mac)
            if dest_vport:
                # Forward payload to destination VPort
                await self.forward_payload(dest_vport, payload)
            else:
                # Broadcast to all except source
                await self.broadcast(payload, exclude=addr)

        writer.close()
        await writer.wait_closed()
        logger.info(f"Connection closed {addr}")

    async def forward_payload(self, dest_vport, payload):
        # Implement forwarding logic to specific VPort
        pass

    async def broadcast(self, payload, exclude=None):
        # Implement broadcasting to all VPorts except 'exclude'
        pass

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

    if len(sys.argv) != 2:
        print("Usage: python3 vswitch.py <SERVER_PORT>")
        sys.exit(1)

    SERVER_PORT = int(sys.argv[1])

    # Initialize Aptos blockchain client
    NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"  # Replace with your node URL
    VPORT_MANAGEMENT_ADDRESS = "0xVPORT"  # Replace with actual address after deployment
    MAC_TABLE_ADDRESS = "0xMACTABLE"  # Replace with actual address after deployment

    aptos_client = AptosBlockchain(
        node_url=NODE_URL,
        vport_management_address=VPORT_MANAGEMENT_ADDRESS,
        mac_table_address=MAC_TABLE_ADDRESS
    )

    vswitch = VSwitch(SERVER_PORT, aptos_client)
    asyncio.run(vswitch.start_server())
