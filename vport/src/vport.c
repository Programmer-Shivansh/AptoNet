#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/sys_domain.h>
#include <sys/kern_control.h>
#include <net/if_utun.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <errno.h>
#include <stdint.h>

static char encoding_table[] = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                                'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
                                'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
                                'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f',
                                'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
                                'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
                                'w', 'x', 'y', 'z', '0', '1', '2', '3',
                                '4', '5', '6', '7', '8', '9', '+', '/'};

void base64_encode(const unsigned char *data,
                   size_t input_length,
                   char *encoded_data,
                   size_t *output_length) {
    *output_length = 4 * ((input_length + 2) / 3);

    for (size_t i = 0, j = 0; i < input_length;) {
        uint32_t octet_a = i < input_length ? data[i++] : 0;
        uint32_t octet_b = i < input_length ? data[i++] : 0;
        uint32_t octet_c = i < input_length ? data[i++] : 0;

        uint32_t triple = (octet_a << 16) + (octet_b << 8) + octet_c;

        encoded_data[j++] = encoding_table[(triple >> 18) & 0x3F];
        encoded_data[j++] = encoding_table[(triple >> 12) & 0x3F];
        encoded_data[j++] = encoding_table[(triple >> 6) & 0x3F];
        encoded_data[j++] = encoding_table[triple & 0x3F];
    }

    for (int i = 0; i < *output_length % 4; i++)
        encoded_data[*output_length - 1 - i] = '=';

    encoded_data[*output_length] = 0;
}
static int base64_decode(const char *data, unsigned char *output, int *output_length) {
    static const unsigned char d[] = {
        62, -1, -1, -1, 63, 52, 53, 54, 55, 56, 57, 58,
        59, 60, 61, -1, -1, -1, -2, -1, -1, -1,  0,  1,  2,  3,  4,  5,
         6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
        22, 23, 24, 25, -1, -1, -1, -1, -1, -1, 26, 27, 28, 29, 30, 31,
        32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47,
        48, 49, 50, 51
    };

    const unsigned char *src = (const unsigned char *)data;
    unsigned char *dst = output;
    *output_length = 0;

    while (*src) {
        int a = src[0];
        int b = src[1];
        int c = src[2];
        int val_d = src[3]; // Renamed variable

        if (a > 127 || b > 127 || c > 127 || val_d > 127)
            return -1;
        a = d[a - 43];
        b = d[b - 43];
        c = d[c - 43];
        val_d = d[val_d - 43];
        if (a == -1 || b == -1)
            return -1;

        *dst++ = (a << 2) | ((b & 0x30) >> 4);
        if (c != -2) {
            *dst++ = ((b & 0x0f) << 4) | ((c & 0x3c) >> 2);
            if (val_d != -2)
                *dst++ = ((c & 0x03) << 6) | val_d;
        }
        src += 4;
        while (*src == ' ' || *src == '\t' || *src == '\n' || *src == '\r')
            src++;
    }

    *output_length = dst - output;
    return 0;
}


#define UTUN_CONTROL_NAME "com.apple.net.utun_control"
#define MAX_DEVICE_NAME_LEN 32
void print_hex_dump(const unsigned char *buffer, size_t length) {
    for (size_t i = 0; i < length; i++) {
        printf("%02x ", buffer[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    if (length % 16 != 0) printf("\n");
}
int create_utun_device(char *dev, size_t dev_size) {
    struct ctl_info ctlInfo;
    struct sockaddr_ctl sc;
    int fd;

    memset(&ctlInfo, 0, sizeof(ctlInfo));
    if (strlcpy(ctlInfo.ctl_name, UTUN_CONTROL_NAME, sizeof(ctlInfo.ctl_name)) >= sizeof(ctlInfo.ctl_name)) {
        fprintf(stderr, "UTUN control name too long");
        return -1;
    }

    fd = socket(PF_SYSTEM, SOCK_DGRAM, SYSPROTO_CONTROL);
    if (fd == -1) {
        perror("socket(SYSPROTO_CONTROL)");
        return -1;
    }

    if (ioctl(fd, CTLIOCGINFO, &ctlInfo) == -1) {
        perror("ioctl(CTLIOCGINFO)");
        close(fd);
        return -1;
    }

    sc.sc_id = ctlInfo.ctl_id;
    sc.sc_len = sizeof(sc);
    sc.sc_family = AF_SYSTEM;
    sc.ss_sysaddr = AF_SYS_CONTROL;
    sc.sc_unit = 0; // Let the kernel assign the unit number

    if (connect(fd, (struct sockaddr *)&sc, sizeof(sc)) == -1) {
        perror("connect(AF_SYS_CONTROL)");
        close(fd);
        return -1;
    }

    // Get the assigned utun device name
    char utunname[MAX_DEVICE_NAME_LEN];
    socklen_t utunname_len = sizeof(utunname);
    if (getsockopt(fd, SYSPROTO_CONTROL, UTUN_OPT_IFNAME, utunname, &utunname_len) == -1) {
        perror("getsockopt(UTUN_OPT_IFNAME)");
        close(fd);
        return -1;
    }

    if (dev_size > 0) {
        strlcpy(dev, utunname, dev_size);
    }

    return fd;
}
int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: sudo ./vport <SERVER_IP> <SERVER_PORT>\n");
        exit(1);
    }
    
    char *SERVER_IP = argv[1];
    int SERVER_PORT = atoi(argv[2]);

    char utun_name[MAX_DEVICE_NAME_LEN];
    int utun_fd = create_utun_device(utun_name, sizeof(utun_name));
    if (utun_fd < 0) {
        fprintf(stderr, "Error creating utun device\n");
        exit(1);
    }

    printf("utun device %s created\n", utun_name);

    // Configure utun device (should be done externally or via scripts)
    // e.g., sudo ifconfig utun0 10.1.1.101 10.1.1.102 up

    // Create UDP socket
    int sockfd;
    struct sockaddr_in servaddr;

    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }

    memset(&servaddr, 0, sizeof(servaddr));
      
    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(SERVER_PORT);
    servaddr.sin_addr.s_addr = inet_addr(SERVER_IP);
    printf("Connecting to server %s:%d\n", SERVER_IP, SERVER_PORT);

    // Main loop: read from utun and send to server, read from server and write to utun
    fd_set read_fds;
    int maxfd = (utun_fd > sockfd) ? utun_fd : sockfd;

        while (1) {
        FD_ZERO(&read_fds);
        FD_SET(utun_fd, &read_fds);
        FD_SET(sockfd, &read_fds);
        printf("Waiting for data...\n");

        int ret = select(maxfd + 1, &read_fds, NULL, NULL, NULL);
        if (ret < 0 && errno == EINTR) continue;
        if (ret < 0) {
            perror("select");
            break;
        }

        // if (FD_ISSET(utun_fd, &read_fds)) {
        //     char buffer[2048];
        //     int nread = read(utun_fd, buffer, sizeof(buffer));
        //     if (nread < 0) {
        //         perror("Reading from utun");
        //         break;
        //     }

        //     printf("Read %d bytes from utun\n", nread);

        //     // Skip the first 4 bytes (utun header)
        //     char *packet = buffer + 4;
        //     nread -= 4;

        //     // Wrap packet in JSON
        //     char json_packet[4096];
        //     snprintf(json_packet, sizeof(json_packet), 
        //              "{\"source_ip\":\"10.1.1.101\",\"destination_ip\":\"10.1.1.102\",\"payload\":\"%.*s\"}", 
        //              nread, packet);

        //     printf("Sending to server: %s\n", json_packet);

        //     int sent = sendto(sockfd, json_packet, strlen(json_packet), 0, 
        //            (struct sockaddr *)&servaddr, sizeof(servaddr));
            
        //     if (sent < 0) {
        //         perror("sendto");
        //     } else {
        //         printf("Sent %d bytes to server\n", sent);
        //     }
        // }
        if (FD_ISSET(utun_fd, &read_fds)) {
            char buffer[2048];
            int nread = read(utun_fd, buffer, sizeof(buffer));
            if (nread < 0) {
                perror("Reading from utun");
                break;
            }

            printf("Read %d bytes from utun\n", nread);

            // Skip the first 4 bytes (utun header)
            char *packet = buffer + 4;
            nread -= 4;

            // Create a base64 encoded version of the packet
            char base64_packet[4096];
            size_t base64_len = 0;
            base64_encode((unsigned char*)packet, nread, base64_packet, &base64_len);

            // Wrap packet in JSON
            char json_packet[8192];
            snprintf(json_packet, sizeof(json_packet), 
                    "{\"source_ip\":\"10.1.1.101\",\"destination_ip\":\"10.1.1.102\",\"payload\":\"%s\"}", 
                    base64_packet);

            printf("Sending to server: %s\n", json_packet);

            int sent = sendto(sockfd, json_packet, strlen(json_packet), 0, 
                (struct sockaddr *)&servaddr, sizeof(servaddr));
            
            if (sent < 0) {
                perror("sendto");
            } else {
                printf("Sent %d bytes to server\n", sent);
            }
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

            printf("Received from server: %s\n", buffer);

            // Parse JSON and write to utun
            char *payload_start = strstr(buffer, "\"payload\":\"");
            if (payload_start) {
                payload_start += strlen("\"payload\":\"");
                char *payload_end = strstr(payload_start, "\"");
                if (payload_end) {
                    *payload_end = '\0';
                    int payload_len = 0;
                    unsigned char decoded_payload[2048];
                    base64_decode(payload_start, decoded_payload, &payload_len);

                    // Prepend 4-byte header for utun
                    char utun_packet[2048];
                    *(uint32_t *)utun_packet = htonl(AF_INET);  // IPv4
                    memcpy(utun_packet + 4, decoded_payload, payload_len);

                    int written = write(utun_fd, utun_packet, payload_len + 4);
                    if (written < 0) {
                        perror("write to utun");
                    } else {
                        printf("Wrote %d bytes to utun\n", written);
                    }
                }
    }
}
    }
    close(utun_fd);
    close(sockfd);
    return 0;
}
