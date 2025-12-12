/**
 * directory_server.c - PQ-Tor Directory Server Implementation
 */

#include "directory_server.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <errno.h>

/* Hardcoded node list (for 7π Physical Cluster) */
static node_info_t nodes[] = {
    {
        .hostname = "192.168.5.186",  // Pi #3 (Guard)
        .port = 6000,
        .type = NODE_TYPE_GUARD,
        .identity = {0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
                     0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01},
        .active = true
    },
    {
        .hostname = "192.168.5.187",  // Pi #4 (Middle)
        .port = 6001,
        .type = NODE_TYPE_MIDDLE,
        .identity = {0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02,
                     0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02},
        .active = true
    },
    {
        .hostname = "192.168.5.188",  // Pi #5 (Exit)
        .port = 6002,
        .type = NODE_TYPE_EXIT,
        .identity = {0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03,
                     0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03},
        .active = true
    }
};
static const int num_nodes = sizeof(nodes) / sizeof(nodes[0]);

/* Server state */
static int server_fd = -1;
static uint16_t server_port = DIR_SERVER_PORT;
static bool server_running = false;

/**
 * Helper: Convert node type to string
 */
static const char* node_type_to_string(node_type_t type) {
    switch (type) {
        case NODE_TYPE_GUARD: return "guard";
        case NODE_TYPE_MIDDLE: return "middle";
        case NODE_TYPE_EXIT: return "exit";
        default: return "unknown";
    }
}

/**
 * Helper: Convert identity to hex string
 */
static void identity_to_hex(const uint8_t *identity, char *hex_str) {
    for (int i = 0; i < 20; i++) {
        sprintf(hex_str + i * 2, "%02x", identity[i]);
    }
    hex_str[40] = '\0';
}

/**
 * Initialize directory server
 */
int dir_server_init(uint16_t port) {
    server_port = port;

    // Create socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return -1;
    }

    // Set socket options
    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("setsockopt");
        close(server_fd);
        return -1;
    }

    // Bind to port
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(server_port);

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(server_fd);
        return -1;
    }

    // Listen
    if (listen(server_fd, DIR_SERVER_MAX_CLIENTS) < 0) {
        perror("listen");
        close(server_fd);
        return -1;
    }

    printf("[Directory] Server initialized on port %u\n", server_port);
    return 0;
}

/**
 * Get list of nodes by type
 */
int dir_server_get_nodes(node_type_t type, node_info_t *output, int max_nodes) {
    int count = 0;

    for (int i = 0; i < num_nodes && count < max_nodes; i++) {
        if (nodes[i].active && (type == 0 || nodes[i].type == type)) {
            memcpy(&output[count], &nodes[i], sizeof(node_info_t));
            count++;
        }
    }

    return count;
}

/**
 * Generate JSON response for /nodes endpoint
 */
int dir_server_generate_json(char *buffer, size_t buffer_size, node_type_t type) {
    int offset = 0;

    // JSON header
    offset += snprintf(buffer + offset, buffer_size - offset,
                      "{\n  \"version\": \"1.0\",\n  \"nodes\": [\n");

    // Nodes array
    bool first = true;
    for (int i = 0; i < num_nodes; i++) {
        if (!nodes[i].active || (type != 0 && nodes[i].type != type)) {
            continue;
        }

        if (!first) {
            offset += snprintf(buffer + offset, buffer_size - offset, ",\n");
        }
        first = false;

        char identity_hex[41];
        identity_to_hex(nodes[i].identity, identity_hex);

        offset += snprintf(buffer + offset, buffer_size - offset,
                          "    {\n"
                          "      \"hostname\": \"%s\",\n"
                          "      \"port\": %u,\n"
                          "      \"type\": \"%s\",\n"
                          "      \"identity\": \"%s\"\n"
                          "    }",
                          nodes[i].hostname,
                          nodes[i].port,
                          node_type_to_string(nodes[i].type),
                          identity_hex);
    }

    // JSON footer
    offset += snprintf(buffer + offset, buffer_size - offset,
                      "\n  ]\n}\n");

    return offset;
}

/**
 * Handle HTTP request
 */
static void handle_http_request(int client_fd) {
    char buffer[DIR_SERVER_BUFFER_SIZE];
    char response[DIR_SERVER_BUFFER_SIZE];

    // Read request
    ssize_t n = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
    if (n <= 0) {
        return;
    }
    buffer[n] = '\0';

    // Parse request line
    char method[16], path[256], version[16];
    if (sscanf(buffer, "%15s %255s %15s", method, path, version) != 3) {
        const char *bad_request = "HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n";
        send(client_fd, bad_request, strlen(bad_request), 0);
        return;
    }

    printf("[Directory] %s %s\n", method, path);

    // Only support GET
    if (strcmp(method, "GET") != 0) {
        const char *method_not_allowed = "HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n";
        send(client_fd, method_not_allowed, strlen(method_not_allowed), 0);
        return;
    }

    // Handle /nodes endpoint
    if (strcmp(path, "/nodes") == 0 || strcmp(path, "/") == 0) {
        char json[DIR_SERVER_BUFFER_SIZE];
        int json_len = dir_server_generate_json(json, sizeof(json), 0);

        if (json_len < 0) {
            const char *error = "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n";
            send(client_fd, error, strlen(error), 0);
            return;
        }

        // Send HTTP response
        int header_len = snprintf(response, sizeof(response),
                                 "HTTP/1.1 200 OK\r\n"
                                 "Content-Type: application/json\r\n"
                                 "Content-Length: %d\r\n"
                                 "Connection: close\r\n"
                                 "\r\n",
                                 json_len);

        send(client_fd, response, header_len, 0);
        send(client_fd, json, json_len, 0);
        return;
    }

    // 404 Not Found
    const char *not_found = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n";
    send(client_fd, not_found, strlen(not_found), 0);
}

/**
 * Start directory server (blocking)
 */
int dir_server_run(void) {
    if (server_fd < 0) {
        fprintf(stderr, "[Directory] Server not initialized\n");
        return -1;
    }

    server_running = true;
    printf("[Directory] Server running on port %u\n", server_port);
    printf("[Directory] Endpoints:\n");
    printf("[Directory]   GET /nodes - List all nodes\n");
    printf("[Directory]   GET /      - List all nodes\n");

    while (server_running) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);

        int client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &client_len);
        if (client_fd < 0) {
            if (errno == EINTR) continue;
            perror("accept");
            break;
        }

        printf("[Directory] Connection from %s:%d\n",
               inet_ntoa(client_addr.sin_addr),
               ntohs(client_addr.sin_port));

        handle_http_request(client_fd);
        close(client_fd);
    }

    return 0;
}

/**
 * Stop directory server
 */
void dir_server_stop(void) {
    server_running = false;
    if (server_fd >= 0) {
        close(server_fd);
        server_fd = -1;
    }
    printf("[Directory] Server stopped\n");
}
