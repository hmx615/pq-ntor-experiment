/**
 * directory_server.c - PQ-Tor Directory Server Implementation
 * Modified version with LOCAL_MODE support for 12-topology testing
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

/* Configuration: Use local mode or SAGIN mode */
#ifndef USE_LOCAL_MODE
#define USE_LOCAL_MODE 1  // Set to 1 for local testing, 0 for SAGIN deployment
#endif

#if USE_LOCAL_MODE
/* Dynamic node list for local testing */
#define MAX_NODES 10
static node_info_t nodes[MAX_NODES];
static int num_nodes = 0;

/**
 * Register a node dynamically (for local mode)
 */
int dir_server_register_node(const char* hostname, uint16_t port, node_type_t type) {
    if (num_nodes >= MAX_NODES) {
        fprintf(stderr, "[Directory] Cannot register node: maximum capacity reached\n");
        return -1;
    }

    strncpy(nodes[num_nodes].hostname, hostname, sizeof(nodes[num_nodes].hostname) - 1);
    nodes[num_nodes].hostname[sizeof(nodes[num_nodes].hostname) - 1] = '\0';
    nodes[num_nodes].port = port;
    nodes[num_nodes].type = type;

    // Generate simple identity based on type and index
    memset(nodes[num_nodes].identity, (type + 1) * 0x10 + num_nodes, 20);
    nodes[num_nodes].active = true;

    printf("[Directory] Registered node: %s:%u (type=%d, id=%d)\n",
           hostname, port, type, num_nodes);

    num_nodes++;
    return num_nodes - 1;
}

/**
 * Get current number of registered nodes
 */
int dir_server_get_node_count(void) {
    return num_nodes;
}

#else
/* Hardcoded node list (for SAGIN network deployment) */
static node_info_t nodes[] = {
    {
        .hostname = "172.20.1.11",  // Sat-1 (Guard)
        .port = 9001,
        .type = NODE_TYPE_GUARD,
        .identity = {0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
                     0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01},
        .active = true
    },
    {
        .hostname = "172.20.2.21",  // Aircraft-1 (Middle)
        .port = 9003,
        .type = NODE_TYPE_MIDDLE,
        .identity = {0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02,
                     0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02},
        .active = true
    },
    {
        .hostname = "172.20.3.32",  // GS-London (Exit)
        .port = 9005,
        .type = NODE_TYPE_EXIT,
        .identity = {0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03,
                     0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03},
        .active = true
    }
};
static const int num_nodes = sizeof(nodes) / sizeof(nodes[0]);
#endif

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

#if USE_LOCAL_MODE
    printf("[Directory] Server initialized on port %u (LOCAL MODE - dynamic registration)\n", server_port);
#else
    printf("[Directory] Server initialized on port %u (SAGIN MODE - hardcoded nodes)\n", server_port);
#endif
    return 0;
}

/**
 * Get list of nodes by type
 */
int dir_server_get_nodes(node_type_t type, node_info_t *output, int max_nodes) {
    int count = 0;

#if USE_LOCAL_MODE
    int total_nodes = num_nodes;
#else
    int total_nodes = num_nodes;
#endif

    for (int i = 0; i < total_nodes && count < max_nodes; i++) {
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

#if USE_LOCAL_MODE
    int total_nodes = num_nodes;
#else
    int total_nodes = num_nodes;
#endif

    // Nodes array
    bool first = true;
    for (int i = 0; i < total_nodes; i++) {
        if (!nodes[i].active || (type != 0 && nodes[i].type != type)) {
            continue;
        }

        if (!first) {
            offset += snprintf(buffer + offset, buffer_size - offset, ",\n");
        }
        first = false;

        // Convert identity to hex
        char identity_hex[41];
        identity_to_hex(nodes[i].identity, identity_hex);

        // Node JSON object
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
static void handle_request(int client_fd) {
    char buffer[4096];
    ssize_t bytes_read = recv(client_fd, buffer, sizeof(buffer) - 1, 0);

    if (bytes_read <= 0) {
        close(client_fd);
        return;
    }

    buffer[bytes_read] = '\0';

    // Parse request line
    char method[16], path[256], version[16];
    if (sscanf(buffer, "%15s %255s %15s", method, path, version) != 3) {
        close(client_fd);
        return;
    }

#if USE_LOCAL_MODE
    // Handle POST /register for relay registration
    if (strcmp(method, "POST") == 0 && strcmp(path, "/register") == 0) {
        // Parse JSON body to get hostname, port, type
        char *body = strstr(buffer, "\r\n\r\n");
        if (body) {
            body += 4; // Skip "\r\n\r\n"

            // Simple JSON parsing (just for this specific format)
            char hostname[256] = "127.0.0.1";
            int port = 0;
            int type = 0;

            char *h = strstr(body, "\"hostname\"");
            char *p = strstr(body, "\"port\"");
            char *t = strstr(body, "\"type\"");

            if (h && p && t) {
                sscanf(h, "\"hostname\": \"%255[^\"]\"", hostname);
                sscanf(p, "\"port\": %d", &port);
                sscanf(t, "\"type\": %d", &type);

                int node_id = dir_server_register_node(hostname, (uint16_t)port, (node_type_t)type);

                if (node_id >= 0) {
                    const char *response =
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/json\r\n"
                        "Connection: close\r\n"
                        "\r\n"
                        "{\"status\": \"registered\", \"node_id\": %d}\n";

                    char resp_buf[512];
                    snprintf(resp_buf, sizeof(resp_buf), response, node_id);
                    send(client_fd, resp_buf, strlen(resp_buf), 0);
                } else {
                    const char *error_response =
                        "HTTP/1.1 500 Internal Server Error\r\n"
                        "Content-Type: application/json\r\n"
                        "Connection: close\r\n"
                        "\r\n"
                        "{\"status\": \"error\", \"message\": \"registration failed\"}\n";
                    send(client_fd, error_response, strlen(error_response), 0);
                }
            }
        }
        close(client_fd);
        return;
    }
#endif

    // Handle GET /nodes or GET /nodes?type=X
    if (strcmp(method, "GET") == 0) {
        // Parse query parameters
        node_type_t filter_type = 0;
        char *query = strchr(path, '?');
        if (query) {
            *query = '\0';
            query++;

            // Parse type parameter
            if (strncmp(query, "type=", 5) == 0) {
                query += 5;
                if (strcmp(query, "guard") == 0) filter_type = NODE_TYPE_GUARD;
                else if (strcmp(query, "middle") == 0) filter_type = NODE_TYPE_MIDDLE;
                else if (strcmp(query, "exit") == 0) filter_type = NODE_TYPE_EXIT;
            }
        }

        // Generate JSON response
        char json_buffer[8192];
        int json_len = dir_server_generate_json(json_buffer, sizeof(json_buffer), filter_type);

        // Send HTTP response
        char response[128];
        snprintf(response, sizeof(response),
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Content-Length: %d\r\n"
                "Connection: close\r\n"
                "\r\n", json_len);

        send(client_fd, response, strlen(response), 0);
        send(client_fd, json_buffer, json_len, 0);
    }

    close(client_fd);
}

/**
 * Run directory server
 */
int dir_server_run(void) {
    if (server_fd < 0) {
        fprintf(stderr, "[Directory] Server not initialized\n");
        return -1;
    }

    server_running = true;
    printf("[Directory] Server running, waiting for connections...\n");

    while (server_running) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);

        int client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &client_len);
        if (client_fd < 0) {
            if (errno == EINTR) continue;
            perror("accept");
            continue;
        }

        // Handle request (simple single-threaded for now)
        handle_request(client_fd);
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

/**
 * Cleanup directory server
 */
void dir_server_cleanup(void) {
    dir_server_stop();
}
