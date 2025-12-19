/**
 * relay_node.h - PQ-Tor Relay Node Implementation
 *
 * Supports three roles: Guard, Middle, Exit
 * Handles circuit creation, extension, and data relay
 */

#ifndef RELAY_NODE_H
#define RELAY_NODE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "cell.h"
#include "hybrid_ntor.h"
#include "onion_crypto.h"

/* Node roles */
typedef enum {
    RELAY_ROLE_GUARD = 1,   // Entry node (接受客户端连接)
    RELAY_ROLE_MIDDLE = 2,  // Middle node (只做转发)
    RELAY_ROLE_EXIT = 3     // Exit node (连接目标服务器)
} relay_role_t;

/* Node configuration */
typedef struct {
    relay_role_t role;
    char hostname[256];
    uint16_t port;
    uint8_t identity[20];  // Node identity fingerprint
    int max_circuits;
    int max_connections;
} relay_config_t;

/* Circuit state */
typedef enum {
    CIRCUIT_STATE_IDLE = 0,
    CIRCUIT_STATE_HANDSHAKE,    // 正在握手
    CIRCUIT_STATE_OPEN,         // 电路已建立
    CIRCUIT_STATE_EXTENDING,    // 正在扩展到下一跳
    CIRCUIT_STATE_CLOSING
} circuit_state_t;

/* Circuit entry (one circuit per connection) */
typedef struct circuit {
    circuit_id_t circ_id;
    circuit_state_t state;

    // Previous hop (toward client)
    int prev_conn_fd;           // Connection to previous hop (-1 if none)
    onion_layer_t crypto_layer; // Crypto for this hop

    // Next hop (toward exit)
    int next_conn_fd;           // Connection to next hop (-1 if none)
    circuit_id_t next_circ_id;  // Circuit ID on next hop

    // For Exit nodes: connection to target server
    int target_fd;              // Connection to target (-1 if none)
    char target_host[256];
    uint16_t target_port;

    bool active;
    struct circuit *next;       // Linked list
} circuit_t;

/* Connection entry */
typedef struct connection {
    int sockfd;
    char peer_addr[64];
    uint16_t peer_port;
    bool active;
    struct connection *next;
} connection_t;

/* Relay node state */
typedef struct {
    relay_config_t config;

    int listen_fd;              // Listening socket
    bool running;

    // Circuit management
    circuit_t *circuits;        // Linked list of circuits
    int num_circuits;

    // Connection management
    connection_t *connections;  // Linked list of connections
    int num_connections;
} relay_node_t;

/*
 * Node initialization and lifecycle
 */

/**
 * Initialize relay node
 */
int relay_node_init(relay_node_t *node, const relay_config_t *config);

/**
 * Start relay node (blocking, runs event loop)
 */
int relay_node_run(relay_node_t *node);

/**
 * Stop relay node
 */
void relay_node_stop(relay_node_t *node);

/**
 * Cleanup relay node
 */
void relay_node_cleanup(relay_node_t *node);

/*
 * Circuit management
 */

/**
 * Create new circuit
 */
circuit_t* relay_node_create_circuit(relay_node_t *node,
                                     circuit_id_t circ_id,
                                     int prev_conn_fd);

/**
 * Find circuit by ID and connection
 */
circuit_t* relay_node_find_circuit(relay_node_t *node,
                                   circuit_id_t circ_id,
                                   int conn_fd);

/**
 * Destroy circuit
 */
void relay_node_destroy_circuit(relay_node_t *node, circuit_t *circuit);

/*
 * Cell processing
 */

/**
 * Process incoming cell
 */
int relay_node_process_cell(relay_node_t *node,
                            cell_t *cell,
                            int conn_fd);

/**
 * Handle CREATE2 cell (establish circuit)
 */
int relay_node_handle_create2(relay_node_t *node,
                              cell_t *cell,
                              int conn_fd);

/**
 * Handle RELAY/RELAY_EARLY cell
 */
int relay_node_handle_relay(relay_node_t *node,
                            cell_t *cell,
                            int conn_fd);

/**
 * Handle RELAY_EXTEND2 (extend circuit to next hop)
 */
int relay_node_handle_extend2(relay_node_t *node,
                              circuit_t *circuit,
                              const uint8_t *extend_data,
                              uint16_t extend_len);

/**
 * Handle RELAY_DATA (forward data)
 */
int relay_node_handle_relay_data(relay_node_t *node,
                                 circuit_t *circuit,
                                 const uint8_t *data,
                                 uint16_t data_len,
                                 bool forward);

/**
 * Handle RELAY_BEGIN (Exit node: connect to target)
 */
int relay_node_handle_relay_begin(relay_node_t *node,
                                  circuit_t *circuit,
                                  const uint8_t *data,
                                  uint16_t data_len);

/**
 * Handle DESTROY cell
 */
int relay_node_handle_destroy(relay_node_t *node,
                              cell_t *cell,
                              int conn_fd);

/*
 * Utility functions
 */

/**
 * Get role name string
 */
const char* relay_role_to_string(relay_role_t role);

/**
 * Print node statistics
 */
void relay_node_print_stats(const relay_node_t *node);

#endif /* RELAY_NODE_H */
