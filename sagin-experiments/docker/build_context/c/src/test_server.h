/**
 * test_server.h - Simple HTTP Test Server
 *
 * Simple HTTP server for testing anonymous access through Exit nodes
 */

#ifndef TEST_SERVER_H
#define TEST_SERVER_H

#include <stdint.h>

/* Server configuration */
#define TEST_SERVER_PORT 8000
#define TEST_SERVER_MAX_CLIENTS 10
#define TEST_SERVER_BUFFER_SIZE 4096

/**
 * Initialize test server
 * @param port Server port (default: 8000)
 * @return 0 on success, -1 on error
 */
int test_server_init(uint16_t port);

/**
 * Start test server (blocking)
 * Runs simple HTTP server and returns test pages
 * @return 0 on success, -1 on error
 */
int test_server_run(void);

/**
 * Stop test server
 */
void test_server_stop(void);

#endif /* TEST_SERVER_H */
