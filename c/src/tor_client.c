/**
 * tor_client.c - PQ-Tor Client Implementation
 */

#define _POSIX_C_SOURCE 200112L
#define _DEFAULT_SOURCE

#include "tor_client.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>

/* Helper: Parse JSON node list (simplified parser) */
static int parse_node_list(const char *json, tor_node_t **nodes, int *count, int type) {
    *nodes = NULL;
    *count = 0;

    // Very simplified JSON parsing - counts nodes first
    const char *ptr = json;
    int num = 0;
    while ((ptr = strstr(ptr, "\"type\":")) != NULL) {
        ptr += 7;
        while (*ptr == ' ') ptr++;
        if (*ptr == '\"') ptr++;

        bool matches = false;
        if (type == 1 && strncmp(ptr, "guard", 5) == 0) matches = true;
        else if (type == 2 && strncmp(ptr, "middle", 6) == 0) matches = true;
        else if (type == 3 && strncmp(ptr, "exit", 4) == 0) matches = true;

        if (matches) num++;
    }

    if (num == 0) return 0;

    *nodes = calloc(num, sizeof(tor_node_t));
    if (!*nodes) return -1;

    // Parse nodes
    ptr = json;
    int idx = 0;
    while ((ptr = strstr(ptr, "\"hostname\":")) != NULL && idx < num) {
        ptr += 11;
        while (*ptr == ' ' || *ptr == '\"') ptr++;

        // Get hostname
        char *end = strchr(ptr, '\"');
        if (!end) break;
        size_t len = end - ptr;
        if (len >= sizeof((*nodes)[idx].hostname)) len = sizeof((*nodes)[idx].hostname) - 1;
        memcpy((*nodes)[idx].hostname, ptr, len);
        (*nodes)[idx].hostname[len] = '\0';
        ptr = end + 1;

        // Get port
        if ((ptr = strstr(ptr, "\"port\":")) != NULL) {
            ptr += 7;
            (*nodes)[idx].port = atoi(ptr);
        }

        // Get type
        if ((ptr = strstr(ptr, "\"type\":")) != NULL) {
            ptr += 7;
            while (*ptr == ' ' || *ptr == '\"') ptr++;

            if (strncmp(ptr, "guard", 5) == 0) (*nodes)[idx].type = 1;
            else if (strncmp(ptr, "middle", 6) == 0) (*nodes)[idx].type = 2;
            else if (strncmp(ptr, "exit", 4) == 0) (*nodes)[idx].type = 3;
        }

        // Get identity
        if ((ptr = strstr(ptr, "\"identity\":")) != NULL) {
            ptr += 11;
            while (*ptr == ' ' || *ptr == '\"') ptr++;
            for (int i = 0; i < 20 && *ptr; i++) {
                unsigned int byte;
                if (sscanf(ptr, "%02x", &byte) == 1) {
                    (*nodes)[idx].identity[i] = byte;
                    ptr += 2;
                }
            }
        }

        if ((*nodes)[idx].type == type) {
            idx++;
        }
    }

    *count = idx;
    return idx;
}

/**
 * Initialize client
 */
int tor_client_init(tor_client_t *client, const tor_client_config_t *config) {
    memset(client, 0, sizeof(tor_client_t));
    memcpy(&client->config, config, sizeof(tor_client_config_t));

    printf("[Client] Initialized with directory %s:%u\n",
           config->directory_host, config->directory_port);

    return 0;
}

/**
 * Fetch node list from directory server
 */
int tor_client_fetch_directory(tor_client_t *client) {
    printf("[Client] Fetching node list from directory...\n");

    // Resolve directory hostname
    struct addrinfo hints, *result;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;

    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%u", client->config.directory_port);

    if (getaddrinfo(client->config.directory_host, port_str, &hints, &result) != 0) {
        fprintf(stderr, "[Client] Failed to resolve directory host\n");
        return -1;
    }

    // Connect to directory
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("socket");
        freeaddrinfo(result);
        return -1;
    }

    if (connect(sockfd, result->ai_addr, result->ai_addrlen) < 0) {
        perror("connect");
        close(sockfd);
        freeaddrinfo(result);
        return -1;
    }

    freeaddrinfo(result);

    // Send HTTP GET request
    char request[512];
    snprintf(request, sizeof(request),
             "GET /nodes HTTP/1.1\r\n"
             "Host: %s\r\n"
             "Connection: close\r\n"
             "\r\n",
             client->config.directory_host);

    if (send(sockfd, request, strlen(request), 0) < 0) {
        perror("send");
        close(sockfd);
        return -1;
    }

    // Receive response
    char response[8192];
    ssize_t total = 0;
    ssize_t n;
    while ((n = recv(sockfd, response + total, sizeof(response) - total - 1, 0)) > 0) {
        total += n;
        if (total >= (ssize_t)sizeof(response) - 1) break;
    }
    response[total] = '\0';
    close(sockfd);

    // Find JSON body (after headers)
    char *json = strstr(response, "\r\n\r\n");
    if (!json) {
        json = strstr(response, "\n\n");
        if (!json) {
            fprintf(stderr, "[Client] Invalid HTTP response\n");
            return -1;
        }
        json += 2;
    } else {
        json += 4;
    }

    // Parse node lists
    parse_node_list(json, &client->guards, &client->num_guards, 1);
    parse_node_list(json, &client->middles, &client->num_middles, 2);
    parse_node_list(json, &client->exits, &client->num_exits, 3);

    printf("[Client] Found %d guards, %d middles, %d exits\n",
           client->num_guards, client->num_middles, client->num_exits);

    return (client->num_guards > 0 && client->num_middles > 0 && client->num_exits > 0) ? 0 : -1;
}

/**
 * Create first hop (connect to Guard and do PQ-Ntor handshake)
 */
int tor_client_create_first_hop(tor_client_t *client, const tor_node_t *guard) {
    printf("[Client] Creating first hop to Guard %s:%u\n", guard->hostname, guard->port);

    // Connect to Guard
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(guard->port);

    if (inet_pton(AF_INET, guard->hostname, &addr.sin_addr) <= 0) {
        fprintf(stderr, "[Client] Invalid Guard address\n");
        return -1;
    }

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("socket");
        return -1;
    }

    // Set receive timeout to avoid hanging indefinitely
    struct timeval timeout;
    timeout.tv_sec = 5;  // 5 second timeout
    timeout.tv_usec = 0;
    if (setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) < 0) {
        perror("setsockopt SO_RCVTIMEO");
    }

    if (connect(sockfd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("connect");
        close(sockfd);
        return -1;
    }

    printf("[Client] Connected to Guard\n");

    // Perform PQ-Ntor handshake
    pq_ntor_client_state client_state;
    uint8_t onionskin[PQ_NTOR_ONIONSKIN_LEN];

    printf("[Client] Creating PQ-Ntor onionskin...\n");
    if (pq_ntor_client_create_onionskin(&client_state, onionskin, guard->identity) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "[Client] Failed to create onionskin\n");
        close(sockfd);
        return -1;
    }
    printf("[Client] Onionskin created (%d bytes)\n", PQ_NTOR_ONIONSKIN_LEN);

    // Generate circuit ID
    circuit_id_t circ_id = (circuit_id_t)((rand() << 16) | rand()) & 0x7FFFFFFF;
    printf("[Client] Generated circuit ID: %u\n", circ_id);

    // Create CREATE2 cell
    printf("[Client] Creating CREATE2 cell...\n");
    cell_t *create2 = cell_create_create2(circ_id, 0x0002, onionskin, PQ_NTOR_ONIONSKIN_LEN);
    if (!create2) {
        fprintf(stderr, "[Client] Failed to create CREATE2 cell\n");
        close(sockfd);
        return -1;
    }
    printf("[Client] CREATE2 cell created\n");

    // Send CREATE2
    printf("[Client] Sending CREATE2 cell (circ_id=%u, size=%d bytes)...\n", circ_id, CELL_LEN);
    if (cell_send(sockfd, create2) != 0) {
        fprintf(stderr, "[Client] Failed to send CREATE2\n");
        cell_free(create2);
        close(sockfd);
        return -1;
    }
    cell_free(create2);

    printf("[Client] CREATE2 sent successfully, waiting for CREATED2...\n");

    // Receive CREATED2
    cell_t *created2 = cell_recv(sockfd);
    if (!created2 || created2->command != CELL_CREATED2) {
        fprintf(stderr, "[Client] Failed to receive CREATED2\n");
        if (created2) cell_free(created2);
        close(sockfd);
        return -1;
    }

    printf("[Client] Received CREATED2\n");

    // Parse reply
    uint8_t reply[PQ_NTOR_REPLY_LEN];
    uint16_t reply_len;
    cell_parse_created2(created2, reply, &reply_len);
    cell_free(created2);

    // Finish handshake
    if (pq_ntor_client_finish_handshake(&client_state, reply) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "[Client] Handshake failed\n");
        close(sockfd);
        return -1;
    }

    // Extract key material
    uint8_t key_material[PQ_NTOR_KEY_ENC_LEN];
    pq_ntor_client_get_key(key_material, &client_state);
    pq_ntor_client_state_cleanup(&client_state);

    // Initialize circuit
    client->circuit = calloc(1, sizeof(tor_circuit_t));
    client->circuit->circ_id = circ_id;
    client->circuit->guard_fd = sockfd;
    memcpy(&client->circuit->guard, guard, sizeof(tor_node_t));

    // Initialize crypto with first layer
    onion_crypto_init(&client->circuit->crypto);
    onion_crypto_add_layer(&client->circuit->crypto, 0, key_material);

    printf("[Client] First hop established\n");
    return 0;
}

/**
 * Extend circuit to another node
 */
static int extend_circuit(tor_client_t *client, const tor_node_t *next_node, int layer_idx) {
    printf("[Client] Extending circuit to %s:%u\n", next_node->hostname, next_node->port);

    // Create onionskin for next hop
    pq_ntor_client_state client_state;
    uint8_t onionskin[PQ_NTOR_ONIONSKIN_LEN];

    if (pq_ntor_client_create_onionskin(&client_state, onionskin, next_node->identity) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "[Client] Failed to create onionskin\n");
        return -1;
    }

    // Build EXTEND2 payload: [256:hostname][2:port][2:htype][2:hlen][hlen:hdata]
    uint8_t extend_data[1200];  // Increased size to accommodate full onionskin
    memset(extend_data, 0, 256);
    strncpy((char*)extend_data, next_node->hostname, 255);
    extend_data[256] = (next_node->port >> 8) & 0xFF;
    extend_data[257] = next_node->port & 0xFF;
    extend_data[258] = 0x00;  // htype = 0x0002
    extend_data[259] = 0x02;
    uint16_t hlen = PQ_NTOR_ONIONSKIN_LEN;
    extend_data[260] = (hlen >> 8) & 0xFF;
    extend_data[261] = hlen & 0xFF;
    memcpy(extend_data + 262, onionskin, PQ_NTOR_ONIONSKIN_LEN);

    uint16_t extend_len = 262 + PQ_NTOR_ONIONSKIN_LEN;

    // Create RELAY_EXTEND2 cell
    printf("[Client] Creating RELAY_EXTEND2 cell (extend_len=%u)...\n", extend_len);
    cell_t *relay_cell = cell_create_relay_early(client->circuit->circ_id, RELAY_EXTEND2, 0, extend_data, extend_len);
    if (!relay_cell) {
        fprintf(stderr, "[Client] Failed to create RELAY_EXTEND2 cell\n");
        return -1;
    }

    // Encrypt with all layers so far
    printf("[Client] Encrypting RELAY_EXTEND2 through %d layers...\n", client->circuit->crypto.num_layers);
    onion_crypto_encrypt(&client->circuit->crypto, relay_cell->payload);

    // Send RELAY_EARLY cell
    printf("[Client] Sending RELAY_EARLY cell...\n");
    if (cell_send(client->circuit->guard_fd, relay_cell) != 0) {
        fprintf(stderr, "[Client] Failed to send EXTEND2\n");
        cell_free(relay_cell);
        return -1;
    }
    cell_free(relay_cell);

    printf("[Client] EXTEND2 sent, waiting for EXTENDED2...\n");

    // Wait for EXTENDED2
    cell_t *response = cell_recv(client->circuit->guard_fd);
    if (!response || response->command != CELL_RELAY) {
        fprintf(stderr, "[Client] Failed to receive EXTENDED2\n");
        if (response) cell_free(response);
        return -1;
    }

    // Decrypt response
    onion_crypto_decrypt(&client->circuit->crypto, response->payload);

    // Parse RELAY cell
    relay_cell_t relay;
    cell_parse_relay(response, &relay);
    cell_free(response);

    if (relay.relay_command != RELAY_EXTENDED2) {
        fprintf(stderr, "[Client] Expected EXTENDED2, got %u\n", relay.relay_command);
        return -1;
    }

    printf("[Client] Received EXTENDED2\n");

    // Finish handshake
    if (pq_ntor_client_finish_handshake(&client_state, relay.data) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "[Client] Extension handshake failed\n");
        return -1;
    }

    // Add new crypto layer
    uint8_t key_material[PQ_NTOR_KEY_ENC_LEN];
    pq_ntor_client_get_key(key_material, &client_state);
    pq_ntor_client_state_cleanup(&client_state);

    onion_crypto_add_layer(&client->circuit->crypto, layer_idx, key_material);

    printf("[Client] Circuit extended (layer %d added)\n", layer_idx);
    return 0;
}

int tor_client_extend_to_middle(tor_client_t *client, const tor_node_t *middle) {
    memcpy(&client->circuit->middle, middle, sizeof(tor_node_t));
    return extend_circuit(client, middle, 1);
}

int tor_client_extend_to_exit(tor_client_t *client, const tor_node_t *exit) {
    memcpy(&client->circuit->exit, exit, sizeof(tor_node_t));
    int ret = extend_circuit(client, exit, 2);
    if (ret == 0) {
        client->circuit->established = true;
    }
    return ret;
}

/**
 * Build complete 3-hop circuit
 */
int tor_client_build_circuit(tor_client_t *client) {
    if (client->num_guards == 0 || client->num_middles == 0 || client->num_exits == 0) {
        fprintf(stderr, "[Client] No nodes available\n");
        return -1;
    }

    printf("[Client] Building 3-hop circuit...\n");

    // Select nodes (just use first one of each type)
    tor_node_t *guard = &client->guards[0];
    tor_node_t *middle = &client->middles[0];
    tor_node_t *exit_node = &client->exits[0];

    // Create circuit
    if (tor_client_create_first_hop(client, guard) != 0) {
        return -1;
    }

    if (tor_client_extend_to_middle(client, middle) != 0) {
        tor_client_destroy_circuit(client);
        return -1;
    }

    if (tor_client_extend_to_exit(client, exit_node) != 0) {
        tor_client_destroy_circuit(client);
        return -1;
    }

    printf("[Client] 3-hop circuit established!\n");
    printf("[Client]   Guard:  %s:%u\n", guard->hostname, guard->port);
    printf("[Client]   Middle: %s:%u\n", middle->hostname, middle->port);
    printf("[Client]   Exit:   %s:%u\n", exit_node->hostname, exit_node->port);

    return 0;
}

/**
 * Begin stream to target
 */
int tor_client_begin_stream(tor_client_t *client, const char *target_host, uint16_t target_port) {
    if (!client->circuit || !client->circuit->established) {
        fprintf(stderr, "[Client] Circuit not established\n");
        return -1;
    }

    printf("[Client] Beginning stream to %s:%u\n", target_host, target_port);

    // Create "host:port" string
    char target[272];
    snprintf(target, sizeof(target), "%s:%u", target_host, target_port);

    // Create RELAY_BEGIN cell
    cell_t *relay_cell = cell_create_relay(client->circuit->circ_id, RELAY_BEGIN, 0,
                                           (uint8_t*)target, strlen(target));

    // Encrypt through all layers
    onion_crypto_encrypt(&client->circuit->crypto, relay_cell->payload);

    // Send
    if (cell_send(client->circuit->guard_fd, relay_cell) != 0) {
        fprintf(stderr, "[Client] Failed to send RELAY_BEGIN\n");
        cell_free(relay_cell);
        return -1;
    }
    cell_free(relay_cell);

    printf("[Client] Sent RELAY_BEGIN\n");

    // Wait for RELAY_CONNECTED
    cell_t *response = cell_recv(client->circuit->guard_fd);
    if (!response) {
        fprintf(stderr, "[Client] Failed to receive RELAY_CONNECTED\n");
        return -1;
    }

    // Decrypt
    onion_crypto_decrypt(&client->circuit->crypto, response->payload);

    relay_cell_t relay;
    cell_parse_relay(response, &relay);
    cell_free(response);

    if (relay.relay_command != RELAY_CONNECTED) {
        fprintf(stderr, "[Client] Expected RELAY_CONNECTED, got %u\n", relay.relay_command);
        return -1;
    }

    printf("[Client] Stream connected\n");
    return 0;
}

/**
 * Send data through circuit
 */
int tor_client_send_data(tor_client_t *client, const uint8_t *data, size_t len) {
    if (!client->circuit || !client->circuit->established) {
        return -1;
    }

    size_t sent = 0;
    while (sent < len) {
        size_t chunk_size = len - sent;
        if (chunk_size > CELL_PAYLOAD_LEN - 11) chunk_size = CELL_PAYLOAD_LEN - 11;

        cell_t *relay_cell = cell_create_relay(client->circuit->circ_id, RELAY_DATA, 0,
                                               data + sent, chunk_size);
        onion_crypto_encrypt(&client->circuit->crypto, relay_cell->payload);

        if (cell_send(client->circuit->guard_fd, relay_cell) != 0) {
            cell_free(relay_cell);
            return -1;
        }
        cell_free(relay_cell);

        sent += chunk_size;
    }

    printf("[Client] Sent %zu bytes\n", sent);
    return sent;
}

/**
 * Receive data from circuit
 */
int tor_client_recv_data(tor_client_t *client, uint8_t *buffer, size_t max_len) {
    if (!client->circuit || !client->circuit->established) {
        return -1;
    }

    cell_t *response = cell_recv(client->circuit->guard_fd);
    if (!response) {
        // Timeout or connection closed - this is normal after all data is received
        return -1;
    }

    printf("[Client] Received cell, command=%u\n", response->command);

    onion_crypto_decrypt(&client->circuit->crypto, response->payload);

    relay_cell_t relay;
    if (cell_parse_relay(response, &relay) != 0) {
        printf("[Client] Failed to parse RELAY cell\n");
        cell_free(response);
        return -1;
    }
    cell_free(response);

    printf("[Client] RELAY cell: cmd=%u, len=%u\n", relay.relay_command, relay.length);

    if (relay.relay_command != RELAY_DATA) {
        return 0;  // Not data, ignore
    }

    size_t copy_len = relay.length;
    if (copy_len > max_len) copy_len = max_len;
    memcpy(buffer, relay.data, copy_len);

    printf("[Client] Received %zu bytes of data\n", copy_len);
    return copy_len;
}

/**
 * HTTP GET request through Tor
 */
int tor_client_http_get(tor_client_t *client, const char *url, char *response, size_t response_size) {
    // Parse URL: http://host:port/path
    char host[256];
    uint16_t port = 80;
    char path[512] = "/";

    const char *ptr = url;
    if (strncmp(ptr, "http://", 7) == 0) {
        ptr += 7;
    }

    const char *slash = strchr(ptr, '/');
    const char *colon = strchr(ptr, ':');

    if (colon && (!slash || colon < slash)) {
        size_t host_len = colon - ptr;
        if (host_len >= sizeof(host)) host_len = sizeof(host) - 1;
        memcpy(host, ptr, host_len);
        host[host_len] = '\0';
        port = atoi(colon + 1);
        if (slash) {
            strncpy(path, slash, sizeof(path) - 1);
        }
    } else if (slash) {
        size_t host_len = slash - ptr;
        if (host_len >= sizeof(host)) host_len = sizeof(host) - 1;
        memcpy(host, ptr, host_len);
        host[host_len] = '\0';
        strncpy(path, slash, sizeof(path) - 1);
    } else {
        strncpy(host, ptr, sizeof(host) - 1);
    }

    printf("[Client] HTTP GET %s (host=%s, port=%u, path=%s)\n", url, host, port, path);

    // Begin stream
    if (tor_client_begin_stream(client, host, port) != 0) {
        return -1;
    }

    // Send HTTP request
    char request[1024];
    int req_len = snprintf(request, sizeof(request),
                          "GET %s HTTP/1.0\r\n"
                          "Host: %s\r\n"
                          "Connection: close\r\n"
                          "\r\n",
                          path, host);

    if (tor_client_send_data(client, (uint8_t*)request, req_len) < 0) {
        return -1;
    }

    // Receive response (with timeout handling)
    size_t total = 0;
    while (total < response_size - 1) {
        int n = tor_client_recv_data(client, (uint8_t*)response + total, response_size - total - 1);
        if (n < 0) {
            // Connection closed or timeout - if we got some data, consider it success
            if (total > 0) {
                printf("[Client] Connection closed after receiving %zu bytes\n", total);
                break;
            }
            fprintf(stderr, "[Client] Failed to receive any data\n");
            return -1;
        } else if (n == 0) {
            // Not a DATA cell (could be END, CONNECTED, etc.) - ignore and continue
            continue;
        } else {
            total += n;
        }
    }
    response[total] = '\0';

    printf("\n[4/4] Response received (%zu bytes):\n", total);
    return total;
}

/**
 * Destroy circuit
 */
void tor_client_destroy_circuit(tor_client_t *client) {
    if (!client->circuit) return;

    if (client->circuit->guard_fd >= 0) {
        close(client->circuit->guard_fd);
    }

    onion_crypto_free(&client->circuit->crypto);
    free(client->circuit);
    client->circuit = NULL;

    printf("[Client] Circuit destroyed\n");
}

/**
 * Cleanup client
 */
void tor_client_cleanup(tor_client_t *client) {
    tor_client_destroy_circuit(client);

    if (client->guards) free(client->guards);
    if (client->middles) free(client->middles);
    if (client->exits) free(client->exits);

    memset(client, 0, sizeof(tor_client_t));
}

/**
 * Print statistics
 */
void tor_client_print_stats(const tor_client_t *client) {
    printf("\n=== Client Statistics ===\n");
    printf("Directory: %s:%u\n", client->config.directory_host, client->config.directory_port);
    printf("Available nodes: %d guards, %d middles, %d exits\n",
           client->num_guards, client->num_middles, client->num_exits);
    printf("Circuit: %s\n", client->circuit && client->circuit->established ? "Established" : "Not established");
    printf("========================\n\n");
}
