from aptos_sdk.async_client import RestClient
from aptos_sdk.account import Account
from aptos_sdk.transactions import (
    EntryFunction,
    TransactionArgument,
    TransactionPayload
)
from aptos_sdk.type_tag import TypeTag, StructTag
from aptos_sdk.bcs import Serializer

import asyncio

class AptosBlockchain:
    def __init__(self, node_url, vport_management_address, mac_table_address):
        self.client = RestClient(node_url)
        self.vport_management_address = vport_management_address
        self.mac_table_address = mac_table_address

    async def register_vport(self, account: Account, name: str):
        payload = EntryFunction.natural(
            f"{self.vport_management_address}::VPortManagement",
            "register_vport",
            [],
            [TransactionArgument(name.encode('utf-8'), Serializer.str)]
        )
        signed_txn = await self.client.create_bcs_signed_transaction(account, TransactionPayload(payload))
        txn_hash = await self.client.submit_bcs_transaction(signed_txn)
        await self.client.wait_for_transaction(txn_hash)
        return txn_hash

    async def authenticate_vport(self, vport_address: str, account: Account):
        payload = EntryFunction.natural(
            f"{self.vport_management_address}::VPortManagement",
            "authenticate_vport",
            [],
            [TransactionArgument(vport_address, Serializer.struct)]
        )
        signed_txn = await self.client.create_bcs_signed_transaction(account, TransactionPayload(payload))
        txn_hash = await self.client.submit_bcs_transaction(signed_txn)
        await self.client.wait_for_transaction(txn_hash)
        return txn_hash

    async def upsert_mac(self, account: Account, mac: str, vport_address: str):
        payload = EntryFunction.natural(
            f"{self.mac_table_address}::MACTable",
            "upsert_mac",
            [],
            [
                TransactionArgument(mac.encode('utf-8'), Serializer.str),
                TransactionArgument(vport_address, Serializer.struct)
            ]
        )
        signed_txn = await self.client.create_bcs_signed_transaction(account, TransactionPayload(payload))
        txn_hash = await self.client.submit_bcs_transaction(signed_txn)
        await self.client.wait_for_transaction(txn_hash)
        return txn_hash

    async def lookup_mac(self, mac: str):
        module = f"{self.mac_table_address}::MACTable"
        function = "lookup_mac"
        return await self.client.view_bcs_payload(
            module=module,
            function=function,
            ty_args=[],  # Empty list for ty_args
            args=[TransactionArgument(mac.encode('utf-8'), Serializer.str)]
        )

    async def get_vport_info(self, vport_address: str):
        module = f"{self.vport_management_address}::VPortManagement"
        function = "get_vport_info"
        return await self.client.view_bcs_payload(
            module=module,
            function=function,
            ty_args=[],  # Empty list for ty_args
            args=[TransactionArgument(vport_address, Serializer.struct)]
        )


    async def list_vports(self):
        module = f"{self.vport_management_address}::VPortManagement"
        function = "list_vports"
        return await self.client.view_bcs_payload(
            module=module,
            function=function,
            ty_args=[],  # Empty list for ty_args
            args=[]  # Empty list for arguments
        )
