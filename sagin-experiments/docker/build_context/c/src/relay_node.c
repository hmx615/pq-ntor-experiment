/**
 * relay_node.c - PQ-Tor Relay Node Implementation
 */

#define _POSIX_C_SOURCE 200112L
#define _DEFAULT_SOURCE

#include "relay_node.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <openssl/evp.h>

/* Helper: Get role name */
const char* relay_role_to_string(relay_role_t role) {
    switch (role) {
        case RELAY_ROLE_GUARD: return "Guard";
        case RELAY_ROLE_MIDDLE: return "Middle";
        case RELAY_ROLE_EXIT: return "Exit";
        default: return "Unknown";
    }
}

/* Helper: Generate random circuit ID */
static circuit_id_t generate_circuit_id(void) {
    circuit_id_t id;
    int fd = open("/dev/urandom", O_RDONLY);
    if (fd < 0) {
        return (circuit_id_t)rand();
    }
    ssize_t n = read(fd, &id, sizeof(id));
    close(fd);
    if (n != sizeof(id)) {
        return (circuit_id_t)rand();
    }
    return id & 0x7FFFFFFF;  // Ensure positive
}

/**
 * Initialize relay node
 */
int relay_node_init(relay_node_t *node, const relay_config_t *config) {
    memset(node, 0, sizeof(relay_node_t));
    memcpy(&node->config, config, sizeof(relay_config_t));

    // Create listening socket
    node->listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (node->listen_fd < 0) {
        perror("socket");
        return -1;
    }

    // Set socket options
    int opt = 1;
    if (setsockopt(node->listen_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("setsockopt");
        close(node->listen_fd);
        return -1;
    }

    // Bind to port
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(config->port);

    if (bind(node->listen_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(node->listen_fd);
        return -1;
    }

    // Listen
    if (listen(node->listen_fd, 10) < 0) {
        perror("listen");
        close(node->listen_fd);
        return -1;
    }

    printf("[%s] Relay node initialized on port %u\n",
           relay_role_to_string(config->role), config->port);

    return 0;
}

/**
 * Create new circuit
 */
circuit_t* relay_node_create_circuit(relay_node_t *node,
                                     circuit_id_t circ_id,
                                     int prev_conn_fd) {
    circuit_t *circuit = calloc(1, sizeof(circuit_t));
    if (!circuit) return NULL;

    circuit->circ_id = circ_id;
    circuit->state = CIRCUIT_STATE_IDLE;
    circuit->prev_conn_fd = prev_conn_fd;
    circuit->next_conn_fd = -1;
    circuit->target_fd = -1;
    circuit->active = true;

    // Initialize crypto layer
    circuit->crypto_layer.active = false;

    // Add to linked list
    circuit->next = node->circuits;
    node->circuits = circuit;
    node->num_circuits++;

    printf("[%s] Created circuit %u (total: %d)\n",
           relay_role_to_string(node->config.role), circ_id, node->num_circuits);

    return circuit;
}

/**
 * Find circuit by ID and connection
 */
circuit_t* relay_node_find_circuit(relay_node_t *node,
                                   circuit_id_t circ_id,
                                   int conn_fd) {
    for (circuit_t *c = node->circuits; c != NULL; c = c->next) {
        if (!c->active) continue;

        // Check if this is from previous hop (forward direction)
        if (c->circ_id == circ_id && c->prev_conn_fd == conn_fd) {
            return c;
        }

        // Check if this is from next hop (backward direction)
        if (c->next_circ_id == circ_id && c->next_conn_fd == conn_fd) {
            return c;
        }
    }
    return NULL;
}

/**
 * Destroy circuit
 */
void relay_node_destroy_circuit(relay_node_t *node, circuit_t *circuit) {
    if (!circuit) return;

    printf("[%s] Destroying circuit %u\n",
           relay_role_to_string(node->config.role), circuit->circ_id);

    // Close connections
    if (circuit->next_conn_fd >= 0) {
        close(circuit->next_conn_fd);
    }
    if (circuit->target_fd >= 0) {
        close(circuit->target_fd);
    }

    // Free crypto context
    if (circuit->crypto_layer.forward_ctx) {
        EVP_CIPHER_CTX_free(circuit->crypto_layer.forward_ctx);
    }
    if (circuit->crypto_layer.backward_ctx) {
        EVP_CIPHER_CTX_free(circuit->crypto_layer.backward_ctx);
    }

    // Remove from linked list
    circuit_t **ptr = &node->circuits;
    while (*ptr) {
        if (*ptr == circuit) {
            *ptr = circuit->next;
            node->num_circuits--;
            break;
        }
        ptr = &(*ptr)->next;
    }

    free(circuit);
}

/**
 * Handle CREATE2 cell (establish circuit with Hybrid Ntor)
 */
int relay_node_handle_create2(relay_node_t *node, cell_t *cell, int conn_fd) {
    printf("[%s] Handling CREATE2 for circuit %u\n",
           relay_role_to_string(node->config.role), cell->circ_id);

    // Parse CREATE2 payload
    uint16_t handshake_type, handshake_len;
    uint8_t handshake_data[HYBRID_NTOR_ONIONSKIN_LEN];

    if (cell_parse_create2(cell, &handshake_type, handshake_data, &handshake_len) != 0) {
        fprintf(stderr, "[%s] Failed to parse CREATE2 cell\n",
                relay_role_to_string(node->config.role));
        return -1;
    }

    printf("[%s] Handshake type: 0x%04x, len: %u\n",
           relay_role_to_string(node->config.role), handshake_type, handshake_len);

    // Find or create circuit
    circuit_t *circuit = relay_node_find_circuit(node, cell->circ_id, conn_fd);
    if (!circuit) {
        circuit = relay_node_create_circuit(node, cell->circ_id, conn_fd);
        if (!circuit) {
            fprintf(stderr, "[%s] Failed to create circuit\n",
                    relay_role_to_string(node->config.role));
            return -1;
        }
    }

    circuit->state = CIRCUIT_STATE_HANDSHAKE;

    // Perform Hybrid Ntor server handshake (Kyber-512 + X25519)
    hybrid_ntor_server_state server_state;
    uint8_t reply[HYBRID_NTOR_REPLY_LEN];

    int ret = hybrid_ntor_server_create_reply(&server_state, reply,
                                              handshake_data, node->config.identity);
    if (ret != HYBRID_NTOR_SUCCESS) {
        fprintf(stderr, "[%s] Hybrid Ntor handshake failed\n",
                relay_role_to_string(node->config.role));
        relay_node_destroy_circuit(node, circuit);
        return -1;
    }

    // Extract encryption key material (K_enc)
    uint8_t key_material[HYBRID_NTOR_KEY_ENC_LEN];
    hybrid_ntor_server_get_key(key_material, &server_state);

    // Initialize crypto layer for this circuit
    if (onion_layer_init(&circuit->crypto_layer, key_material) != 0) {
        fprintf(stderr, "[%s] Failed to initialize crypto layer\n",
                relay_role_to_string(node->config.role));
        hybrid_ntor_server_state_cleanup(&server_state);
        relay_node_destroy_circuit(node, circuit);
        return -1;
    }

    // Send CREATED2 reply
    cell_t *created2 = cell_create_created2(cell->circ_id, reply, HYBRID_NTOR_REPLY_LEN);
    if (!created2) {
        fprintf(stderr, "[%s] Failed to create CREATED2 cell\n",
                relay_role_to_string(node->config.role));
        hybrid_ntor_server_state_cleanup(&server_state);
        relay_node_destroy_circuit(node, circuit);
        return -1;
    }

    if (cell_send(conn_fd, created2) != 0) {
        fprintf(stderr, "[%s] Failed to send CREATED2 cell\n",
                relay_role_to_string(node->config.role));
        cell_free(created2);
        hybrid_ntor_server_state_cleanup(&server_state);
        relay_node_destroy_circuit(node, circuit);
        return -1;
    }

    cell_free(created2);
    hybrid_ntor_server_state_cleanup(&server_state);

    circuit->state = CIRCUIT_STATE_OPEN;
    printf("[%s] Circuit %u established (Hybrid Kyber+X25519)\n",
           relay_role_to_string(node->config.role), cell->circ_id);

    return 0;
}

/**
 * Handle RELAY_EXTEND2 (extend circuit to next hop)
 */
int relay_node_handle_extend2(relay_node_t *node,
                              circuit_t *circuit,
                              const uint8_t *extend_data,
                              uint16_t extend_len) {
    printf("[%s] Handling EXTEND2 for circuit %u\n",
           relay_role_to_string(node->config.role), circuit->circ_id);

    // Parse EXTEND2 format: [2:nspec][spec...][2:htype][2:hlen][hlen:hdata]
    // Simplified: [256:hostname][2:port][2:htype][2:hlen][hlen:hdata]

    if (extend_len < 260) {
        fprintf(stderr, "[%s] EXTEND2 data too short\n",
                relay_role_to_string(node->config.role));
        return -1;
    }

    char next_host[256];
    memcpy(next_host, extend_data, 256);
    next_host[255] = '\0';

    uint16_t next_port = (extend_data[256] << 8) | extend_data[257];
    uint16_t htype = (extend_data[258] << 8) | extend_data[259];
    uint16_t hlen = (extend_data[260] << 8) | extend_data[261];
    const uint8_t *hdata = extend_data + 262;

    printf("[%s] Extending to %s:%u (htype=0x%04x, hlen=%u)\n",
           relay_role_to_string(node->config.role), next_host, next_port, htype, hlen);

    // Connect to next hop
    struct sockaddr_in next_addr;
    memset(&next_addr, 0, sizeof(next_addr));
    next_addr.sin_family = AF_INET;
    next_addr.sin_port = htons(next_port);

    if (inet_pton(AF_INET, next_host, &next_addr.sin_addr) <= 0) {
        fprintf(stderr, "[%s] Invalid next hop address: %s\n",
                relay_role_to_string(node->config.role), next_host);
        return -1;
    }

    int next_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (next_fd < 0) {
        perror("socket");
        return -1;
    }

    if (connect(next_fd, (struct sockaddr*)&next_addr, sizeof(next_addr)) < 0) {
        perror("connect");
        close(next_fd);
        return -1;
    }

    printf("[%s] Connected to next hop %s:%u\n",
           relay_role_to_string(node->config.role), next_host, next_port);

    // Generate circuit ID for next hop
    circuit_id_t next_circ_id = generate_circuit_id();

    // Create CREATE2 cell for next hop
    cell_t *create2 = cell_create_create2(next_circ_id, htype, hdata, hlen);
    if (!create2) {
        close(next_fd);
        return -1;
    }

    // Send CREATE2 to next hop
    if (cell_send(next_fd, create2) != 0) {
        cell_free(create2);
        close(next_fd);
        return -1;
    }
    cell_free(create2);

    // Wait for CREATED2 from next hop
    cell_t *created2 = cell_recv(next_fd);
    if (!created2 || created2->command != CELL_CREATED2) {
        fprintf(stderr, "[%s] Failed to receive CREATED2 from next hop\n",
                relay_role_to_string(node->config.role));
        if (created2) cell_free(created2);
        close(next_fd);
        return -1;
    }

    printf("[%s] Received CREATED2 from next hop\n",
           relay_role_to_string(node->config.role));

    // Store next hop info
    circuit->next_conn_fd = next_fd;
    circuit->next_circ_id = next_circ_id;

    // Forward EXTENDED2 to previous hop
    relay_cell_t relay;
    memset(&relay, 0, sizeof(relay));
    relay.relay_command = RELAY_EXTENDED2;
    relay.stream_id = 0;

    uint16_t reply_len;
    uint8_t reply_data[HYBRID_NTOR_REPLY_LEN];
    cell_parse_created2(created2, reply_data, &reply_len);
    memcpy(relay.data, reply_data, reply_len);
    relay.length = reply_len;

    cell_free(created2);

    // Create RELAY cell
    cell_t *relay_cell = cell_new(circuit->circ_id, CELL_RELAY);
    cell_pack_relay(relay_cell, &relay);

    // Encrypt for backward direction
    onion_crypto_add_layer_back(&circuit->crypto_layer, relay_cell->payload);

    // Send to previous hop
    if (cell_send(circuit->prev_conn_fd, relay_cell) != 0) {
        fprintf(stderr, "[%s] Failed to send EXTENDED2\n",
                relay_role_to_string(node->config.role));
        cell_free(relay_cell);
        return -1;
    }

    cell_free(relay_cell);
    printf("[%s] Sent EXTENDED2 to previous hop\n",
           relay_role_to_string(node->config.role));

    return 0;
}

/**
 * Handle RELAY_BEGIN (Exit node: connect to target)
 */
int relay_node_handle_relay_begin(relay_node_t *node,
                                  circuit_t *circuit,
                                  const uint8_t *data,
                                  uint16_t data_len) {
    if (node->config.role != RELAY_ROLE_EXIT) {
        fprintf(stderr, "[%s] Received RELAY_BEGIN but not Exit node\n",
                relay_role_to_string(node->config.role));
        return -1;
    }

    printf("[%s] Handling RELAY_BEGIN for circuit %u\n",
           relay_role_to_string(node->config.role), circuit->circ_id);

    // Parse target: "host:port"
    char target[256];
    memcpy(target, data, data_len);
    target[data_len] = '\0';

    char *colon = strchr(target, ':');
    if (!colon) {
        fprintf(stderr, "[%s] Invalid BEGIN target format\n",
                relay_role_to_string(node->config.role));
        return -1;
    }

    *colon = '\0';
    strncpy(circuit->target_host, target, sizeof(circuit->target_host) - 1);
    circuit->target_port = atoi(colon + 1);

    printf("[%s] Connecting to target %s:%u\n",
           relay_role_to_string(node->config.role),
           circuit->target_host, circuit->target_port);

    // Resolve hostname
    struct addrinfo hints, *result;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;

    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%u", circuit->target_port);

    if (getaddrinfo(circuit->target_host, port_str, &hints, &result) != 0) {
        fprintf(stderr, "[%s] Failed to resolve %s\n",
                relay_role_to_string(node->config.role), circuit->target_host);
        return -1;
    }

    // Connect to target
    int target_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (target_fd < 0) {
        perror("socket");
        freeaddrinfo(result);
        return -1;
    }

    if (connect(target_fd, result->ai_addr, result->ai_addrlen) < 0) {
        perror("connect");
        close(target_fd);
        freeaddrinfo(result);
        return -1;
    }

    freeaddrinfo(result);
    circuit->target_fd = target_fd;

    printf("[%s] Connected to target %s:%u\n",
           relay_role_to_string(node->config.role),
           circuit->target_host, circuit->target_port);

    // Send RELAY_CONNECTED back
    relay_cell_t relay;
    memset(&relay, 0, sizeof(relay));
    relay.relay_command = RELAY_CONNECTED;
    relay.stream_id = 0;
    relay.length = 0;

    cell_t *relay_cell = cell_new(circuit->circ_id, CELL_RELAY);
    cell_pack_relay(relay_cell, &relay);

    // Encrypt for backward direction
    onion_crypto_add_layer_back(&circuit->crypto_layer, relay_cell->payload);

    if (cell_send(circuit->prev_conn_fd, relay_cell) != 0) {
        fprintf(stderr, "[%s] Failed to send RELAY_CONNECTED\n",
                relay_role_to_string(node->config.role));
        cell_free(relay_cell);
        return -1;
    }

    cell_free(relay_cell);
    printf("[%s] Sent RELAY_CONNECTED\n", relay_role_to_string(node->config.role));

    return 0;
}

/**
 * Handle RELAY_DATA (forward data)
 */
int relay_node_handle_relay_data(relay_node_t *node,
                                 circuit_t *circuit,
                                 const uint8_t *data,
                                 uint16_t data_len,
                                 bool forward) {
    printf("[%s] Handling RELAY_DATA for circuit %u (len=%u, forward=%d)\n",
           relay_role_to_string(node->config.role), circuit->circ_id, data_len, forward);

    if (forward) {
        // Forward direction: toward exit
        if (circuit->next_conn_fd >= 0) {
            // Forward to next hop (still encrypted)
            relay_cell_t relay;
            memset(&relay, 0, sizeof(relay));
            relay.relay_command = RELAY_DATA;
            relay.stream_id = 0;
            memcpy(relay.data, data, data_len);
            relay.length = data_len;

            cell_t *relay_cell = cell_new(circuit->next_circ_id, CELL_RELAY);
            cell_pack_relay(relay_cell, &relay);

            if (cell_send(circuit->next_conn_fd, relay_cell) != 0) {
                cell_free(relay_cell);
                return -1;
            }
            cell_free(relay_cell);
        } else if (circuit->target_fd >= 0) {
            // Exit node: send to target
            if (send(circuit->target_fd, data, data_len, 0) < 0) {
                perror("send to target");
                return -1;
            }
            printf("[%s] Sent %u bytes to target\n",
                   relay_role_to_string(node->config.role), data_len);
        }
    } else {
        // Backward direction: toward client
        relay_cell_t relay;
        memset(&relay, 0, sizeof(relay));
        relay.relay_command = RELAY_DATA;
        relay.stream_id = 0;
        memcpy(relay.data, data, data_len);
        relay.length = data_len;

        cell_t *relay_cell = cell_new(circuit->circ_id, CELL_RELAY);
        cell_pack_relay(relay_cell, &relay);

        // Encrypt for backward direction
        onion_crypto_add_layer_back(&circuit->crypto_layer, relay_cell->payload);

        if (cell_send(circuit->prev_conn_fd, relay_cell) != 0) {
            cell_free(relay_cell);
            return -1;
        }
        cell_free(relay_cell);
        printf("[%s] Forwarded %u bytes backward\n",
               relay_role_to_string(node->config.role), data_len);
    }

    return 0;
}

/**
 * Handle RELAY cell
 */
int relay_node_handle_relay(relay_node_t *node, cell_t *cell, int conn_fd) {
    // Find circuit
    circuit_t *circuit = relay_node_find_circuit(node, cell->circ_id, conn_fd);
    if (!circuit) {
        fprintf(stderr, "[%s] Circuit %u not found\n",
                relay_role_to_string(node->config.role), cell->circ_id);
        return -1;
    }

    // Determine direction: forward (from prev) or backward (from next)
    bool is_forward = (conn_fd == circuit->prev_conn_fd);

    if (is_forward) {
        // Forward direction: decrypt and process/forward
        bool is_recognized = false;
        onion_crypto_peel_layer(&circuit->crypto_layer, cell->payload, &is_recognized);

        if (is_recognized) {
            // Parse and handle the command
            relay_cell_t relay;
            if (cell_parse_relay(cell, &relay) != 0) {
                fprintf(stderr, "[%s] Failed to parse RELAY cell\n",
                        relay_role_to_string(node->config.role));
                return -1;
            }

            printf("[%s] RELAY cell: cmd=%s, stream=%u, len=%u (recognized)\n",
                   relay_role_to_string(node->config.role),
                   relay_command_to_string(relay.relay_command),
                   relay.stream_id, relay.length);

            switch (relay.relay_command) {
                case RELAY_EXTEND2:
                    return relay_node_handle_extend2(node, circuit, relay.data, relay.length);

                case RELAY_BEGIN:
                    return relay_node_handle_relay_begin(node, circuit, relay.data, relay.length);

                case RELAY_DATA:
                    return relay_node_handle_relay_data(node, circuit, relay.data, relay.length, true);

                default:
                    printf("[%s] Unhandled RELAY command: %u\n",
                           relay_role_to_string(node->config.role), relay.relay_command);
                    return 0;
            }
        } else {
            // Not recognized, forward to next hop
            printf("[%s] Forwarding unrecognized RELAY cell to next hop (circ=%u)\n",
                   relay_role_to_string(node->config.role), circuit->next_circ_id);

            if (circuit->next_conn_fd >= 0) {
                cell_t *forward_cell = cell_new(circuit->next_circ_id, cell->command);
                memcpy(forward_cell->payload, cell->payload, CELL_PAYLOAD_LEN);

                if (cell_send(circuit->next_conn_fd, forward_cell) != 0) {
                    fprintf(stderr, "[%s] Failed to forward RELAY cell\n",
                            relay_role_to_string(node->config.role));
                    cell_free(forward_cell);
                    return -1;
                }
                cell_free(forward_cell);
                printf("[%s] Successfully forwarded RELAY cell\n",
                       relay_role_to_string(node->config.role));
            } else {
                fprintf(stderr, "[%s] No next hop to forward to!\n",
                        relay_role_to_string(node->config.role));
            }
        }
    } else {
        // Backward direction: add encryption layer and forward to previous hop
        printf("[%s] Forwarding backward RELAY cell from next hop (circ=%u)\n",
               relay_role_to_string(node->config.role), circuit->circ_id);

        // Add one layer of encryption
        onion_crypto_add_layer_back(&circuit->crypto_layer, cell->payload);

        // Forward to previous hop
        cell_t *backward_cell = cell_new(circuit->circ_id, cell->command);
        memcpy(backward_cell->payload, cell->payload, CELL_PAYLOAD_LEN);

        if (cell_send(circuit->prev_conn_fd, backward_cell) != 0) {
            fprintf(stderr, "[%s] Failed to forward backward RELAY cell\n",
                    relay_role_to_string(node->config.role));
            cell_free(backward_cell);
            return -1;
        }
        cell_free(backward_cell);
        printf("[%s] Successfully forwarded backward RELAY cell\n",
               relay_role_to_string(node->config.role));
    }

    return 0;
}

/**
 * Handle DESTROY cell
 */
int relay_node_handle_destroy(relay_node_t *node, cell_t *cell, int conn_fd) {
    circuit_t *circuit = relay_node_find_circuit(node, cell->circ_id, conn_fd);
    if (circuit) {
        relay_node_destroy_circuit(node, circuit);
    }
    return 0;
}

/**
 * Process incoming cell
 */
int relay_node_process_cell(relay_node_t *node, cell_t *cell, int conn_fd) {
    printf("[%s] Processing cell: circ=%u, cmd=%s\n",
           relay_role_to_string(node->config.role),
           cell->circ_id,
           cell_command_to_string(cell->command));

    switch (cell->command) {
        case CELL_CREATE2:
            return relay_node_handle_create2(node, cell, conn_fd);

        case CELL_RELAY:
        case CELL_RELAY_EARLY:
            return relay_node_handle_relay(node, cell, conn_fd);

        case CELL_DESTROY:
            return relay_node_handle_destroy(node, cell, conn_fd);

        default:
            printf("[%s] Unhandled cell command: %u\n",
                   relay_role_to_string(node->config.role), cell->command);
            return 0;
    }
}

/**
 * Main event loop (simplified, single-threaded)
 */
int relay_node_run(relay_node_t *node) {
    node->running = true;

    printf("[%s] Node running on port %u\n",
           relay_role_to_string(node->config.role), node->config.port);

    while (node->running) {
        fd_set read_fds;
        FD_ZERO(&read_fds);
        FD_SET(node->listen_fd, &read_fds);
        int max_fd = node->listen_fd;

        // Add all active connections
        for (connection_t *conn = node->connections; conn != NULL; conn = conn->next) {
            if (conn->active && conn->sockfd >= 0) {
                FD_SET(conn->sockfd, &read_fds);
                if (conn->sockfd > max_fd) max_fd = conn->sockfd;
            }
        }

        // Add all next_conn_fd (for receiving backward cells)
        for (circuit_t *c = node->circuits; c != NULL; c = c->next) {
            if (c->active && c->next_conn_fd >= 0) {
                FD_SET(c->next_conn_fd, &read_fds);
                if (c->next_conn_fd > max_fd) max_fd = c->next_conn_fd;
            }
        }

        // Add all target connections (for Exit nodes)
        for (circuit_t *c = node->circuits; c != NULL; c = c->next) {
            if (c->active && c->target_fd >= 0) {
                FD_SET(c->target_fd, &read_fds);
                if (c->target_fd > max_fd) max_fd = c->target_fd;
            }
        }

        struct timeval timeout = {.tv_sec = 1, .tv_usec = 0};
        int ready = select(max_fd + 1, &read_fds, NULL, NULL, &timeout);

        if (ready < 0) {
            if (errno == EINTR) continue;
            perror("select");
            break;
        }

        if (ready == 0) continue;

        // Accept new connections and read cells
        if (FD_ISSET(node->listen_fd, &read_fds)) {
            struct sockaddr_in client_addr;
            socklen_t client_len = sizeof(client_addr);
            int client_fd = accept(node->listen_fd, (struct sockaddr*)&client_addr, &client_len);

            if (client_fd >= 0) {
                printf("[%s] New connection from %s:%d (fd=%d)\n",
                       relay_role_to_string(node->config.role),
                       inet_ntoa(client_addr.sin_addr),
                       ntohs(client_addr.sin_port),
                       client_fd);

                // Create a connection entry for this fd
                // This allows us to track open connections
                connection_t *conn = calloc(1, sizeof(connection_t));
                if (conn) {
                    conn->sockfd = client_fd;
                    strncpy(conn->peer_addr, inet_ntoa(client_addr.sin_addr), sizeof(conn->peer_addr) - 1);
                    conn->peer_port = ntohs(client_addr.sin_port);
                    conn->active = true;
                    conn->next = node->connections;
                    node->connections = conn;
                    node->num_connections++;
                }
            }
        }

        // Read from active connections
        for (connection_t *conn = node->connections; conn != NULL; conn = conn->next) {
            if (conn->active && FD_ISSET(conn->sockfd, &read_fds)) {
                cell_t *cell = cell_recv(conn->sockfd);
                if (cell) {
                    relay_node_process_cell(node, cell, conn->sockfd);
                    cell_free(cell);
                } else {
                    // Connection closed
                    printf("[%s] Connection %d closed\n",
                           relay_role_to_string(node->config.role), conn->sockfd);
                    close(conn->sockfd);
                    conn->active = false;
                }
            }
        }

        // Read from next_conn_fd (for receiving backward cells)
        for (circuit_t *c = node->circuits; c != NULL; c = c->next) {
            if (c->active && c->next_conn_fd >= 0 && FD_ISSET(c->next_conn_fd, &read_fds)) {
                cell_t *cell = cell_recv(c->next_conn_fd);
                if (cell) {
                    relay_node_process_cell(node, cell, c->next_conn_fd);
                    cell_free(cell);
                } else {
                    // Connection closed
                    printf("[%s] Next hop connection %d closed\n",
                           relay_role_to_string(node->config.role), c->next_conn_fd);
                    close(c->next_conn_fd);
                    c->next_conn_fd = -1;
                }
            }
        }

        // Handle data from target servers (Exit node)
        for (circuit_t *c = node->circuits; c != NULL; c = c->next) {
            if (c->active && c->target_fd >= 0 && FD_ISSET(c->target_fd, &read_fds)) {
                uint8_t buffer[CELL_PAYLOAD_LEN - 11];
                ssize_t n = recv(c->target_fd, buffer, sizeof(buffer), 0);

                if (n > 0) {
                    printf("[%s] Received %zd bytes from target\n",
                           relay_role_to_string(node->config.role), n);
                    relay_node_handle_relay_data(node, c, buffer, n, false);
                } else {
                    // Connection closed
                    close(c->target_fd);
                    c->target_fd = -1;
                }
            }
        }
    }

    return 0;
}

/**
 * Stop relay node
 */
void relay_node_stop(relay_node_t *node) {
    node->running = false;
}

/**
 * Cleanup relay node
 */
void relay_node_cleanup(relay_node_t *node) {
    // Destroy all circuits
    while (node->circuits) {
        relay_node_destroy_circuit(node, node->circuits);
    }

    // Close listening socket
    if (node->listen_fd >= 0) {
        close(node->listen_fd);
    }

    printf("[%s] Node cleaned up\n", relay_role_to_string(node->config.role));
}

/**
 * Print node statistics
 */
void relay_node_print_stats(const relay_node_t *node) {
    printf("\n=== %s Node Statistics ===\n", relay_role_to_string(node->config.role));
    printf("Port: %u\n", node->config.port);
    printf("Active circuits: %d\n", node->num_circuits);
    printf("Active connections: %d\n", node->num_connections);
    printf("===========================\n\n");
}
