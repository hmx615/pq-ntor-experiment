/**
 * relay_main.c - Relay Node Main Program
 *
 * Runs a relay node (Guard, Middle, or Exit)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include "../src/relay_node.h"

static relay_node_t *global_node = NULL;

void signal_handler(int signum) {
    printf("\n[Main] Received signal %d, shutting down...\n", signum);
    if (global_node) {
        relay_node_stop(global_node);
    }
}

int main(int argc, char *argv[]) {
    relay_config_t config = {
        .role = RELAY_ROLE_GUARD,
        .port = 6001,
        .max_circuits = 100,
        .max_connections = 100
    };

    // Default identity (will be different for each role)
    memset(config.identity, 0x01, sizeof(config.identity));
    strncpy(config.hostname, "0.0.0.0", sizeof(config.hostname));

    // Parse command line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-r") == 0 && i + 1 < argc) {
            // Role: guard, middle, exit
            i++;
            if (strcmp(argv[i], "guard") == 0) {
                config.role = RELAY_ROLE_GUARD;
                config.port = 6001;
                memset(config.identity, 0x01, sizeof(config.identity));
            } else if (strcmp(argv[i], "middle") == 0) {
                config.role = RELAY_ROLE_MIDDLE;
                config.port = 6002;
                memset(config.identity, 0x02, sizeof(config.identity));
            } else if (strcmp(argv[i], "exit") == 0) {
                config.role = RELAY_ROLE_EXIT;
                config.port = 6003;
                memset(config.identity, 0x03, sizeof(config.identity));
            } else {
                fprintf(stderr, "Invalid role: %s\n", argv[i]);
                return 1;
            }
        } else if (strcmp(argv[i], "-p") == 0 && i + 1 < argc) {
            config.port = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            printf("Usage: %s [options]\n", argv[0]);
            printf("Options:\n");
            printf("  -r ROLE    Node role: guard, middle, exit (default: guard)\n");
            printf("  -p PORT    Listen port (default: 6001 for guard, 6002 for middle, 6003 for exit)\n");
            printf("  -h         Show this help\n");
            printf("\nExamples:\n");
            printf("  %s -r guard\n", argv[0]);
            printf("  %s -r middle -p 6002\n", argv[0]);
            printf("  %s -r exit -p 6003\n", argv[0]);
            return 0;
        }
    }

    // Setup signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    printf("============================================\n");
    printf("  PQ-Tor Relay Node - %s\n", relay_role_to_string(config.role));
    printf("============================================\n\n");

    // Initialize relay node
    relay_node_t node;
    if (relay_node_init(&node, &config) != 0) {
        fprintf(stderr, "[Main] Failed to initialize relay node\n");
        return 1;
    }

    global_node = &node;

    printf("\n");
    printf("Node Configuration:\n");
    printf("  Role:     %s\n", relay_role_to_string(config.role));
    printf("  Port:     %u\n", config.port);
    printf("  Identity: ");
    for (int i = 0; i < 20; i++) {
        printf("%02x", config.identity[i]);
    }
    printf("\n\n");
    printf("Press Ctrl+C to stop...\n");
    printf("\n");

    // Run relay node (blocking)
    int ret = relay_node_run(&node);

    // Cleanup
    relay_node_cleanup(&node);

    printf("[Main] Shutdown complete\n");
    return ret;
}
