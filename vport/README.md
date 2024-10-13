# VPort Client

## Overview

The VPort client simulates a physical switch port, responsible for relaying Ethernet frames between the TAP device and the VSwitch server via UDP sockets. It handles authentication and communication with the decentralized VSwitch.

## Setup

1. **Build the VPort Client**

    ```bash
    cd vport
    make
    ```

2. **Configure TAP Device**

    After building, run the VPort client with the server IP and port. In another terminal, configure the TAP device:

    ```bash
    sudo ip addr add 10.1.1.101/24 dev tapyuan
    sudo ip link set tapyuan up
    ```

3. **Run the VPort Client**

    ```bash
    sudo ./vport <SERVER_IP> <SERVER_PORT>
    ```

    Replace `<SERVER_IP>` with your VSwitch server's IP address and `<SERVER_PORT>` with the port number the VSwitch server is listening on.

## Usage

The VPort client establishes a UDP connection with the VSwitch server, handling the sending and receiving of Ethernet frames encapsulated in JSON format. It reads from the TAP device, sends frames to the server, and writes received frames back to the TAP device.

---
