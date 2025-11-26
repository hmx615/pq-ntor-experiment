/**
 * client_main.c - Tor Client Main Program
 *
 * Simple client that:
 * 1. Fetches node list from directory
 * 2. Builds 3-hop circuit
 * 3. Sends HTTP GET request through Tor
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "../src/tor_client.h"

int main(int argc, char *argv[]) {
    tor_client_config_t config = {
        .directory_host = "localhost",
        .directory_port = 5000,
        .timeout_seconds = 30,
        .use_classic_ntor = 0  // Default to PQ-NTOR
    };

    char target_url[512] = "http://localhost:8000/";

    // Parse command line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-d") == 0 && i + 1 < argc) {
            strncpy(config.directory_host, argv[++i], sizeof(config.directory_host) - 1);
        } else if (strcmp(argv[i], "-p") == 0 && i + 1 < argc) {
            config.directory_port = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-u") == 0 && i + 1 < argc) {
            strncpy(target_url, argv[++i], sizeof(target_url) - 1);
        } else if (strcmp(argv[i], "--mode") == 0 && i + 1 < argc) {
            i++;
            if (strcmp(argv[i], "classic") == 0) {
                config.use_classic_ntor = 1;
            } else if (strcmp(argv[i], "pq") == 0) {
                config.use_classic_ntor = 0;
            } else {
                fprintf(stderr, "Error: Invalid mode '%s'. Use 'classic' or 'pq'\n", argv[i]);
                return 1;
            }
        } else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            printf("Usage: %s [options]\n", argv[0]);
            printf("Options:\n");
            printf("  -d HOST      Directory server host (default: localhost)\n");
            printf("  -p PORT      Directory server port (default: 5000)\n");
            printf("  -u URL       Target URL to fetch (default: http://localhost:8000/)\n");
            printf("  --mode MODE  Use 'classic' or 'pq' NTOR (default: pq)\n");
            printf("  -h           Show this help\n");
            printf("\nExample:\n");
            printf("  %s -u http://localhost:8000/\n", argv[0]);
            printf("  %s --mode classic -u http://localhost:8000/\n", argv[0]);
            return 0;
        }
    }

    // Disable stdout/stderr buffering for real-time logging
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    srand(time(NULL));

    printf("============================================\n");
    if (config.use_classic_ntor) {
        printf("  Tor Client (Classic NTOR)\n");
    } else {
        printf("  Tor Client (PQ-NTOR)\n");
    }
    printf("============================================\n\n");

    // Initialize client
    tor_client_t client;
    if (tor_client_init(&client, &config) != 0) {
        fprintf(stderr, "Failed to initialize client\n");
        return 1;
    }

    // Fetch directory
    printf("[1/4] Fetching directory...\n");
    if (tor_client_fetch_directory(&client) != 0) {
        fprintf(stderr, "Failed to fetch directory\n");
        tor_client_cleanup(&client);
        return 1;
    }

    // Build circuit
    printf("\n[2/4] Building 3-hop circuit...\n");
    if (tor_client_build_circuit(&client) != 0) {
        fprintf(stderr, "Failed to build circuit\n");
        tor_client_cleanup(&client);
        return 1;
    }

    // Send HTTP request
    printf("\n[3/4] Sending HTTP GET request...\n");
    printf("Target: %s\n\n", target_url);

    char response[16384];
    int response_len = tor_client_http_get(&client, target_url, response, sizeof(response));

    if (response_len < 0) {
        fprintf(stderr, "HTTP request failed\n");
        tor_client_cleanup(&client);
        return 1;
    }

    // Display response
    printf("============================================\n");
    printf("%s\n", response);
    printf("============================================\n");

    // Cleanup
    tor_client_cleanup(&client);

    printf("\nTest completed successfully!\n");
    return 0;
}
