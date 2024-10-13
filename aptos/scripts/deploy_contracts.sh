#!/bin/bash

# Exit on any error
set -e

# Set variables
APTOS_HOME=~/aptos-core
PROJECT_DIR=$(pwd)/../
CONTRACTS_DIR=${PROJECT_DIR}/contracts

# Function to extract address from TOML file
get_address_from_toml() {
    local toml_file=$1
    local address_name=$2
    local address=$(grep "$address_name =" "$toml_file" | cut -d '"' -f 2)
    echo $address
}

# Navigate to VPort Management contract
echo "Navigating to VPort Management contract..."
cd ${CONTRACTS_DIR}/vport_management
aptos move compile

# Get address from VPort Management TOML file
VPORT_ADDRESS=$(get_address_from_toml "Move.toml" "VPORT_MANAGEMENT")
echo "Publishing VPort Management contract with address: $VPORT_ADDRESS"
aptos move publish --package-dir . --named-addresses VPORT_MANAGEMENT=$VPORT_ADDRESS

# Navigate to MAC Table contract
echo "Navigating to MAC Table contract..."
cd ${CONTRACTS_DIR}/mac_table
aptos move compile

# Get address from MAC Table TOML file
MAC_TABLE_ADDRESS=$(get_address_from_toml "Move.toml" "MAC_TABLE")
echo "Publishing MAC Table contract with address: $MAC_TABLE_ADDRESS"
aptos move publish --package-dir . --named-addresses MAC_TABLE=$MAC_TABLE_ADDRESS

echo "Contracts deployed successfully."