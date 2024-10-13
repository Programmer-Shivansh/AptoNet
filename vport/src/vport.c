#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <linux/if_tun.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <errno.h>

// Function to create a TAP device
int create_tap_device(char *dev) {
    struct ifreq ifr;
    int fd, err;

    if ((fd = open("/dev/net/tun", O_RDWR)) < 0 ) {
        perror("Opening /dev/net/tun");
        return fd;
    }

    memset(&ifr, 0, sizeof(ifr));

    ifr.ifr_flags = IFF_TAP | IFF_NO_PI; 
    if (*dev) {
        strncpy(ifr.ifr_name, dev, IFNAMSIZ);
    }

    if ((err = ioctl(fd, TUNSETIFF, (void *)&ifr)) < 0 ) {
        perror("ioctl(TUNSETIFF)");
        close(fd);
        return err;
    }

    strcpy(dev, ifr.ifr_name);
    return fd;
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: sudo ./vport <SERVER_IP> <SERVER_PORT>\n");
        exit(1);
    }

    char *SERVER_IP = argv[1];
    int SERVER_PORT = atoi(argv[2]);

    char tap_name[IFNAMSIZ] = "tapyuan";
    int tap_fd = create_tap_device(tap_name);
    if (tap_fd < 0) {
        fprintf(stderr, "Error creating TAP device\n");
        exit(1);
    }

    printf("TAP device %s created\n", tap_name);

    // Configure TAP device (should be done externally or via scripts)
    // e.g., sudo ip addr add 10.1.1.101/24 dev tapyuan
    // sudo ip link set tapyuan up

    // Create UDP socket
    int sockfd;
    struct sockaddr_in servaddr;

    if ( (sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0 ) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }

    memset(&servaddr, 0, sizeof(servaddr));
      
    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(SERVER_PORT);
    servaddr.sin_addr.s_addr = inet_addr(SERVER_IP);

    // Main loop: read from TAP and send to server, read from server and write to TAP
    fd_set read_fds;
    int maxfd = (tap_fd > sockfd) ? tap_fd : sockfd;

    while (1) {
        FD_ZERO(&read_fds);
        FD_SET(tap_fd, &read_fds);
        FD_SET(sockfd, &read_fds);

        int ret = select(maxfd + 1, &read_fds, NULL, NULL, NULL);
        if (ret < 0 && errno == EINTR) continue;
        if (ret < 0) {
            perror("select");
            break;
        }

        if (FD_ISSET(tap_fd, &read_fds)) {
            char buffer[2048];
            int nread = read(tap_fd, buffer, sizeof(buffer));
            if (nread < 0) {
                perror("Reading from TAP");
                break;
            }

            // Wrap Ethernet frame in JSON
            // Simplified for example
            // In production, use proper serialization
            // Extract MAC addresses and payload
            // Placeholder values
            char json_frame[4096];
            snprintf(json_frame, sizeof(json_frame), 
                     "{\"source_mac\":\"11:11:11:11:11:11\",\"destination_mac\":\"aa:aa:aa:aa:aa:aa\",\"payload\":\"%s\"}", 
                     buffer);

            sendto(sockfd, json_frame, strlen(json_frame), 0, 
                   (struct sockaddr *)&servaddr, sizeof(servaddr));
        }

        if (FD_ISSET(sockfd, &read_fds)) {
            char buffer[4096];
            socklen_t len = sizeof(servaddr);
            int n = recvfrom(sockfd, buffer, sizeof(buffer)-1, 0, 
                             (struct sockaddr *)&servaddr, &len);
            if (n < 0) {
                perror("recvfrom");
                break;
            }
            buffer[n] = '\0';

            // Parse JSON and write to TAP
            // Simplified for example
            // In production, use proper JSON parsing
            // Extract payload
            char *payload_start = strstr(buffer, "\"payload\":\"");
            if (payload_start) {
                payload_start += strlen("\"payload\":\"");
                char *payload_end = strstr(payload_start, "\"");
                if (payload_end) {
                    *payload_end = '\0';
                    write(tap_fd, payload_start, strlen(payload_start));
                }
            }
        }
    }

    close(tap_fd);
    close(sockfd);
    return 0;
}
