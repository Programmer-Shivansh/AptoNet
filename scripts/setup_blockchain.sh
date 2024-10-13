#!/bin/bash

# Exit on any error
set -e

# Hardcoded current account address
CURRENT_ACCOUNT="0x7384fc7adb9991b4a6dc90b40f354d20a42428a94148865ed8dc9650f5ecfa82"

# Install Aptos CLI if not installed
if ! command -v aptos &> /dev/null
then
    echo "Aptos CLI not found. Installing..."
    curl https://aptos.dev/install.sh | bash
fi

# Initialize Aptos (only if not already initialized)
if [ ! -f ~/.aptos/config.yaml ]; then
    echo "Initializing Aptos..."
    aptos init
else
    echo "Aptos already initialized, skipping initialization step."
fi

# Output the current account address
echo "Current account address: $CURRENT_ACCOUNT"

# Generate a new account address
echo "Generating new account address..."
VPORT_ACCOUNT=$(aptos account derive-resource-account-address --address $CURRENT_ACCOUNT --seed vport_management | jq -r '.Result')

if [[ -z "$VPORT_ACCOUNT" || "$VPORT_ACCOUNT" == "}" ]]; then
    echo "Error: Failed to generate a new account address."
    exit 1
fi

echo "Generated account address: $VPORT_ACCOUNT"

# Create the account
echo "Creating new account for VPort Management and MAC Table contracts..."
aptos account create --account "$VPORT_ACCOUNT"

# Fund the account using faucet
echo "Funding the account using faucet..."
aptos account fund-with-faucet --account "$VPORT_ACCOUNT"

echo "Blockchain setup completed."
echo "VPort Admin Address: $VPORT_ACCOUNT"
