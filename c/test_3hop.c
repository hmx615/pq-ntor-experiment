#include "src/tor_client.h"
#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("=== Testing 3-hop Circuit Building ===\n\n");

    tor_client_t *client = tor_client_init("localhost", 5000);
    if (!client) {
        fprintf(stderr, "Failed to initialize client\n");
        return 1;
    }

    printf("[1/2] Fetching directory...\n");
    if (tor_client_fetch_directory(client) != 0) {
        fprintf(stderr, "Failed to fetch directory\n");
        tor_client_cleanup(client);
        return 1;
    }
    printf("Found %d guards, %d middles, %d exits\n\n",
           client->num_guards, client->num_middles, client->num_exits);

    printf("[2/2] Building 3-hop circuit...\n");
    if (tor_client_build_circuit(client) != 0) {
        fprintf(stderr, "Failed to build circuit\n");
        tor_client_cleanup(client);
        return 1;
    }

    printf("\n");
    printf("=== SUCCESS ===\n");
    printf("3-hop PQ-Tor circuit successfully established!\n");
    printf("Circuit established: %s\n", client->circuit->established ? "YES" : "NO");

    tor_client_cleanup(client);
    return 0;
}
