#!/bin/bash

# Exit on any error
set -e

# Run blockchain setup
./setup_blockchain.sh

# Deploy smart contracts
cd aptos/scripts
./deploy_contracts.sh

echo "Deployment completed."


### chmod +x scripts/deploy.sh
