#!/bin/bash

# Exit on any error
set -e

# Install Aptos CLI if not installed
if ! command -v aptos &> /dev/null
then
    echo "Aptos CLI not found. Installing..."
    curl https://aptos.dev/install.sh | bash
fi

# Initialize Aptos
aptos init

# Create a new account for contracts
echo "Creating new account for VPort Management and MAC Table contracts..."
aptos account generate --profile vport_admin
VPORT_ADMIN_ADDRESS=$(aptos account list --profile vport_admin | awk 'NR==2 {print $1}')
echo "VPort Admin Address: $VPORT_ADMIN_ADDRESS"

# Fund the account if on testnet/devnet
# Replace with faucet URL if necessary
echo "FUNDING THE ACCOUNT IS REQUIRED ON TESTNET/DEVNET"

echo "Blockchain setup completed."


### chmod +x scripts/setup_blockchain.sh
