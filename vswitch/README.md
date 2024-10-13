# VSwitch Server

## Overview

The VSwitch server simulates a physical network switch, managing Ethernet frame exchanges between connected VPorts. It interacts with the Aptos blockchain to maintain a decentralized MAC address table and handle VPort authentication.

## Setup

1. **Install Dependencies**

    ```bash
    cd vswitch
    pip install -r requirements.txt
    ```

2. **Configure Aptos Client**

    - Update `vswitch.py` with your Aptos node URL, VPort Management contract address, and MAC Table contract address.

3. **Run the VSwitch Server**

    ```bash
    python3 vswitch.py <SERVER_PORT>
    ```

    Replace `<SERVER_PORT>` with the desired port number (e.g., `8000`).

## Usage

The VSwitch server listens for incoming connections from VPort clients, handles authentication via the Aptos blockchain, and manages Ethernet frame forwarding based on the decentralized MAC address table.

---
