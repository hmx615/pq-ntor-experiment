/**
 * relay_registration.c - Helper for relay nodes to register with directory in local mode
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

/**
 * Register this relay with the directory server
 *
 * @param dir_host Directory server hostname
 * @param dir_port Directory server port (typically 5000)
 * @param relay_port This relay's listening port
 * @param relay_type Node type: 1=guard, 2=middle, 3=exit
 * @return 0 on success, -1 on failure
 */
int register_with_directory(const char *dir_host, int dir_port, int relay_port, int relay_type) {
    int sock;
    struct sockaddr_in server_addr;
    char request[512];
    char response[1024];

    // Create socket
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("socket");
        return -1;
    }

    // Setup server address
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(dir_port);

    if (inet_pton(AF_INET, dir_host, &server_addr.sin_addr) <= 0) {
        fprintf(stderr, "Invalid directory address: %s\n", dir_host);
        close(sock);
        return -1;
    }

    // Connect to directory
    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        perror("connect to directory");
        close(sock);
        return -1;
    }

    // Build registration request
    char json_body[256];
    snprintf(json_body, sizeof(json_body),
             "{\"hostname\": \"127.0.0.1\", \"port\": %d, \"type\": %d}",
             relay_port, relay_type);

    snprintf(request, sizeof(request),
             "POST /register HTTP/1.1\r\n"
             "Host: %s:%d\r\n"
             "Content-Type: application/json\r\n"
             "Content-Length: %zu\r\n"
             "Connection: close\r\n"
             "\r\n"
             "%s",
             dir_host, dir_port, strlen(json_body), json_body);

    // Send request
    if (send(sock, request, strlen(request), 0) < 0) {
        perror("send registration");
        close(sock);
        return -1;
    }

    // Receive response
    ssize_t bytes = recv(sock, response, sizeof(response) - 1, 0);
    if (bytes > 0) {
        response[bytes] = '\0';

        // Check for 200 OK
        if (strstr(response, "HTTP/1.1 200 OK") != NULL) {
            printf("[Relay] Successfully registered with directory (port=%d, type=%d)\n",
                   relay_port, relay_type);
            close(sock);
            return 0;
        } else {
            fprintf(stderr, "[Relay] Registration failed: %s\n", response);
        }
    } else {
        fprintf(stderr, "[Relay] No response from directory\n");
    }

    close(sock);
    return -1;
}
