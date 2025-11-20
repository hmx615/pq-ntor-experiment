/**
 * directory_main.c - Directory Server Main Program
 *
 * Runs both directory server (port 5000) and test HTTP server (port 8000)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <pthread.h>
#include "../src/directory_server.h"
#include "../src/test_server.h"

static volatile int keep_running = 1;

void signal_handler(int signum) {
    printf("\n[Main] Received signal %d, shutting down...\n", signum);
    keep_running = 0;
    dir_server_stop();
    test_server_stop();
}

void* test_server_thread(void *arg) {
    (void)arg;
    test_server_run();
    return NULL;
}

int main(int argc, char *argv[]) {
    int dir_port = DIR_SERVER_PORT;
    int test_port = TEST_SERVER_PORT;

    // Parse command line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-p") == 0 && i + 1 < argc) {
            dir_port = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-t") == 0 && i + 1 < argc) {
            test_port = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            printf("Usage: %s [options]\n", argv[0]);
            printf("Options:\n");
            printf("  -p PORT    Directory server port (default: 5000)\n");
            printf("  -t PORT    Test server port (default: 8000)\n");
            printf("  -h         Show this help\n");
            return 0;
        }
    }

    // Setup signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    printf("============================================\n");
    printf("  PQ-Tor Directory + Test Server\n");
    printf("============================================\n\n");

    // Initialize directory server
    if (dir_server_init(dir_port) != 0) {
        fprintf(stderr, "[Main] Failed to initialize directory server\n");
        return 1;
    }

    // Initialize test server
    if (test_server_init(test_port) != 0) {
        fprintf(stderr, "[Main] Failed to initialize test server\n");
        dir_server_stop();
        return 1;
    }

    // Start test server in separate thread
    pthread_t test_thread;
    if (pthread_create(&test_thread, NULL, test_server_thread, NULL) != 0) {
        fprintf(stderr, "[Main] Failed to create test server thread\n");
        dir_server_stop();
        test_server_stop();
        return 1;
    }

    printf("\n");
    printf("Servers running:\n");
    printf("  Directory Server: http://localhost:%d/nodes\n", dir_port);
    printf("  Test Server:      http://localhost:%d/\n", test_port);
    printf("\n");
    printf("Press Ctrl+C to stop...\n");
    printf("\n");

    // Run directory server (blocking)
    dir_server_run();

    // Wait for test server thread
    pthread_join(test_thread, NULL);

    printf("[Main] Shutdown complete\n");
    return 0;
}
