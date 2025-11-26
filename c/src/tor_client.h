/**
 * tor_client.h - PQ-Tor Client Implementation
 *
 * Implements Tor client functionality:
 * - Fetch node list from directory server
 * - Build 3-hop circuit (Guard -> Middle -> Exit)
 * - Send HTTP requests through Tor
 */

#ifndef TOR_CLIENT_H
#define TOR_CLIENT_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "cell.h"
#include "pq_ntor.h"
#include "onion_crypto.h"

/* Node information from directory */
typedef struct {
    char hostname[256];
    uint16_t port;
    uint8_t identity[20];
    int type;  // 1=Guard, 2=Middle, 3=Exit
} tor_node_t;

/* Circuit state */
typedef struct {
    circuit_id_t circ_id;
    int guard_fd;                    // Connection to Guard node

    // Nodes in circuit
    tor_node_t guard;
    tor_node_t middle;
    tor_node_t exit;

    // Crypto state for all layers
    onion_crypto_t crypto;

    bool established;
} tor_circuit_t;

/* Client configuration */
typedef struct {
    char directory_host[256];
    uint16_t directory_port;
    int timeout_seconds;
    int use_classic_ntor;  // 0 = PQ-NTOR, 1 = Classic NTOR
} tor_client_config_t;

/* Client state */
typedef struct {
    tor_client_config_t config;
    tor_circuit_t *circuit;

    // Available nodes
    tor_node_t *guards;
    int num_guards;
    tor_node_t *middles;
    int num_middles;
    tor_node_t *exits;
    int num_exits;
} tor_client_t;

/*
 * Client lifecycle
 */

/**
 * Initialize client with configuration
 */
int tor_client_init(tor_client_t *client, const tor_client_config_t *config);

/**
 * Fetch node list from directory server
 */
int tor_client_fetch_directory(tor_client_t *client);

/**
 * Build 3-hop circuit
 */
int tor_client_build_circuit(tor_client_t *client);

/**
 * Destroy circuit and cleanup
 */
void tor_client_destroy_circuit(tor_client_t *client);

/**
 * Cleanup client
 */
void tor_client_cleanup(tor_client_t *client);

/*
 * Circuit building
 */

/**
 * Step 1: Connect to Guard and establish first hop
 */
int tor_client_create_first_hop(tor_client_t *client, const tor_node_t *guard);

/**
 * Step 2: Extend circuit to Middle node
 */
int tor_client_extend_to_middle(tor_client_t *client, const tor_node_t *middle);

/**
 * Step 3: Extend circuit to Exit node
 */
int tor_client_extend_to_exit(tor_client_t *client, const tor_node_t *exit);

/*
 * Data transmission
 */

/**
 * Begin stream to target (sends RELAY_BEGIN)
 */
int tor_client_begin_stream(tor_client_t *client, const char *target_host, uint16_t target_port);

/**
 * Send data through circuit (RELAY_DATA)
 */
int tor_client_send_data(tor_client_t *client, const uint8_t *data, size_t len);

/**
 * Receive data from circuit (RELAY_DATA)
 */
int tor_client_recv_data(tor_client_t *client, uint8_t *buffer, size_t max_len);

/*
 * High-level API
 */

/**
 * Send HTTP GET request through Tor
 * @param client Tor client
 * @param url Target URL (e.g., "http://example.com/path")
 * @param response Output buffer for HTTP response
 * @param response_size Size of response buffer
 * @return Number of bytes received, or -1 on error
 */
int tor_client_http_get(tor_client_t *client,
                        const char *url,
                        char *response,
                        size_t response_size);

/**
 * Print client statistics
 */
void tor_client_print_stats(const tor_client_t *client);

#endif /* TOR_CLIENT_H */
