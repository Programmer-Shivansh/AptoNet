# Decentralized VSwitch with Aptos Blockchain

## Introduction

This project transforms a traditional virtual network switch (similar to ZeroTier) into a decentralized network stack by integrating the Aptos blockchain. Leveraging blockchain's security and transparency, the system ensures resilient and secure Ethernet frame exchanges across distributed nodes.

## Project Structure

- **aptos/**: Contains Aptos smart contracts for VPort management and MAC address table.
- **vswitch/**: The VSwitch server that interacts with the Aptos blockchain.
- **vport/**: The VPort client responsible for connecting to the VSwitch server.
- **scripts/**: Deployment and setup scripts.
- **diagrams/**: Architecture diagrams and visual aids.

## Getting Started

### Prerequisites

- **Aptos CLI**: Install from [Aptos Installation Guide](https://aptos.dev/).
- **Python 3.7+**: For running the VSwitch server.
- **C Compiler (gcc)**: For building the VPort client.
- **Root Privileges**: Required for configuring TAP devices.

### Setup and Deployment

1. **Clone the Repository**

    ```bash
    git clone https://github.com/yourusername/decentralized-vswitch.git
    cd decentralized-vswitch
    ```

2. **Setup Blockchain**

    ```bash
    cd scripts
    ./setup_blockchain.sh
    ```

    - Follow the prompts to initialize Aptos and generate accounts.
    - Ensure your Aptos account is funded if deploying on testnet/devnet.

3. **Deploy Smart Contracts**

    ```bash
    ./deploy.sh
    ```

    - This will compile and publish the VPort Management and MAC Table contracts to the Aptos blockchain.

4. **Configure and Run VSwitch Server**

    ```bash
    cd ../vswitch
    pip install -r requirements.txt
    python3 src/vswitch.py <SERVER_PORT>
    ```

    - Replace `<SERVER_PORT>` with your desired port number (e.g., `8000`).

5. **Build and Run VPort Clients**

    ```bash
    cd ../../vport
    make
    sudo ./vport <SERVER_IP> <SERVER_PORT>
    ```

    - Replace `<SERVER_IP>` with the VSwitch server's IP address and `<SERVER_PORT>` with the port number.

6. **Configure TAP Devices**

    On each client machine:

    ```bash
    sudo ip addr add 10.1.1.101/24 dev tapyuan
    sudo ip link set tapyuan up
    ```

    - Adjust the IP address as needed for each client.

7. **Test Connectivity**

    - Ping between clients to ensure connectivity:

    ```bash
    ping 10.1.1.102  # From Client-1 to Client-2
    ping 10.1.1.101  # From Client-2 to Client-1
    ```

## Architecture

![Architecture Diagram](diagrams/architecture_diagram.png)

*Refer to the `diagrams/architecture_diagram.png` for a visual representation of the system architecture.*

## How It Works

1. **VPort Registration and Authentication**

    - VPorts register with the VSwitch server via the Aptos blockchain.
    - Smart contracts handle authentication, ensuring only authorized VPorts can connect.

2. **Decentralized MAC Address Management**

    - The MAC address table is stored on the Aptos blockchain.
    - VSwitch nodes read from and write to the blockchain to maintain a consistent view of the network.

3. **Ethernet Frame Forwarding**

    - VSwitch nodes manage Ethernet frame exchanges based on the decentralized MAC table.
    - Frames are forwarded to the appropriate VPort clients or broadcasted as needed.

## Additional Information

- **Smart Contracts**: Located in `aptos/contracts/`.
- **VSwitch Server Code**: Located in `vswitch/src/`.
- **VPort Client Code**: Located in `vport/src/`.

## Contributing

Contributions are welcome! Please open issues or submit pull requests for enhancements and bug fixes.




terminal 1 - 
gcc -o vport src/vport.c
sudo ./vport 127.0.0.1 8005

temrinal 2 - 
python3 src/vswitch.py 8005

terminal 3 - 
sudo ifconfig utun4 10.1.1.101 10.1.1.102 up
ping 10.1.1.102

