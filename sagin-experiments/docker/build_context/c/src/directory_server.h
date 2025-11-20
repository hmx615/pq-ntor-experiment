/**
 * directory_server.h - PQ-Tor Directory Server
 *
 * Simple HTTP server that provides:
 * 1. Node directory service (list of Guard, Middle, Exit nodes)
 * 2. JSON API for node discovery
 */

#ifndef DIRECTORY_SERVER_H
#define DIRECTORY_SERVER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* Server configuration */
#define DIR_SERVER_PORT 5000
#define DIR_SERVER_MAX_CLIENTS 10
#define DIR_SERVER_BUFFER_SIZE 4096

/* Node types */
typedef enum {
    NODE_TYPE_GUARD = 1,
    NODE_TYPE_MIDDLE = 2,
    NODE_TYPE_EXIT = 3
} node_type_t;

/* Node information */
typedef struct {
    char hostname[256];
    uint16_t port;
    node_type_t type;
    uint8_t identity[20];  // Node identity (fingerprint)
    bool active;
} node_info_t;

/**
 * Initialize directory server
 * @param port Server port (default: 5000)
 * @return 0 on success, -1 on error
 */
int dir_server_init(uint16_t port);

/**
 * Start directory server (blocking)
 * Runs HTTP server and handles client requests
 * @return 0 on success, -1 on error
 */
int dir_server_run(void);

/**
 * Stop directory server
 */
void dir_server_stop(void);

/**
 * Get list of nodes by type
 * @param type Node type filter (0 for all)
 * @param nodes Output buffer for nodes
 * @param max_nodes Maximum number of nodes to return
 * @return Number of nodes returned, -1 on error
 */
int dir_server_get_nodes(node_type_t type, node_info_t *nodes, int max_nodes);

/**
 * Generate JSON response for /nodes endpoint
 * @param buffer Output buffer
 * @param buffer_size Buffer size
 * @param type Node type filter (0 for all)
 * @return Number of bytes written, -1 on error
 */
int dir_server_generate_json(char *buffer, size_t buffer_size, node_type_t type);

#endif /* DIRECTORY_SERVER_H */
