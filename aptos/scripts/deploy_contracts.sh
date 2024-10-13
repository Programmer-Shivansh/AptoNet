#!/bin/bash

# Exit on any error
set -e

# Set variables
APTOS_HOME=~/aptos-core
PROJECT_DIR=$(pwd)/../
CONTRACTS_DIR=${PROJECT_DIR}/contracts

# Navigate to VPort Management contract
cd ${CONTRACTS_DIR}/vport_management
aptos move compile

# Publish VPort Management contract
VPORT_ADDRESS=$(aptos account list | awk 'NR==2 {print $1}')
echo "Publishing VPort Management contract with address: $VPORT_ADDRESS"
aptos move publish --package-dir . --named-addresses VPORT_MANAGEMENT=${VPORT_ADDRESS}

# Navigate to MAC Table contract
cd ${CONTRACTS_DIR}/mac_table
aptos move compile

# Publish MAC Table contract
MAC_TABLE_ADDRESS=$(aptos account list | awk 'NR==2 {print $1}')
echo "Publishing MAC Table contract with address: $MAC_TABLE_ADDRESS"
aptos move publish --package-dir . --named-addresses MAC_TABLE=${MAC_TABLE_ADDRESS}

echo "Contracts deployed successfully."


### chmod +x aptos/scripts/deploy_contracts.sh
