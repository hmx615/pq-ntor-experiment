/**
 * @file test_hybrid_ntor.c
 * @brief Test program for Hybrid Ntor handshake protocol
 */

#include <stdio.h>
#include <string.h>
#include <time.h>
#include "hybrid_ntor.h"

#define TEST_ITERATIONS 100

/**
 * Print bytes in hex format
 */
static void print_hex(const char *label, const uint8_t *data, size_t len) {
    printf("%s: ", label);
    for (size_t i = 0; i < len && i < 32; i++) {
        printf("%02x", data[i]);
    }
    if (len > 32) printf("...");
    printf(" (%zu bytes)\n", len);
}

/**
 * Test single hybrid handshake
 */
static int test_single_handshake(int verbose) {
    hybrid_ntor_client_state client_state;
    hybrid_ntor_server_state server_state;

    uint8_t onionskin[HYBRID_NTOR_ONIONSKIN_LEN];
    uint8_t reply[HYBRID_NTOR_REPLY_LEN];
    uint8_t relay_identity[HYBRID_NTOR_RELAY_ID_LENGTH];

    // Generate relay identity
    memset(relay_identity, 0x42, sizeof(relay_identity));

    // Step 1: Client creates onionskin
    if (hybrid_ntor_client_create_onionskin(&client_state, onionskin, relay_identity) != HYBRID_NTOR_SUCCESS) {
        printf("FAIL: Client create onionskin failed\n");
        return -1;
    }
    if (verbose) {
        printf("\n=== Client State After Create Onionskin ===\n");
        print_hex("  Kyber PK", client_state.kyber_public_key, KYBER_PUBLIC_KEY_BYTES);
        print_hex("  X25519 PK", client_state.x25519_public_key, X25519_KEY_SIZE);
        print_hex("  Onionskin", onionskin, HYBRID_NTOR_ONIONSKIN_LEN);
    }

    // Step 2: Server creates reply
    if (hybrid_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity) != HYBRID_NTOR_SUCCESS) {
        printf("FAIL: Server create reply failed\n");
        return -1;
    }
    if (verbose) {
        printf("\n=== Server State After Create Reply ===\n");
        print_hex("  Kyber SS", server_state.kyber_shared_secret, KYBER_SHARED_SECRET_BYTES);
        print_hex("  X25519 SS", server_state.x25519_shared_secret, X25519_SHARED_SIZE);
        print_hex("  Hybrid SS", server_state.hybrid_shared_secret, HYBRID_SHARED_SECRET_LEN);
        print_hex("  K_enc", server_state.k_enc, HYBRID_NTOR_KEY_ENC_LEN);
        print_hex("  Reply", reply, HYBRID_NTOR_REPLY_LEN);
    }

    // Step 3: Client finishes handshake
    if (hybrid_ntor_client_finish_handshake(&client_state, reply) != HYBRID_NTOR_SUCCESS) {
        printf("FAIL: Client finish handshake failed (AUTH verification)\n");
        return -1;
    }
    if (verbose) {
        printf("\n=== Client State After Finish Handshake ===\n");
        print_hex("  Kyber SS", client_state.kyber_shared_secret, KYBER_SHARED_SECRET_BYTES);
        print_hex("  X25519 SS", client_state.x25519_shared_secret, X25519_SHARED_SIZE);
        print_hex("  Hybrid SS", client_state.hybrid_shared_secret, HYBRID_SHARED_SECRET_LEN);
        print_hex("  K_enc", client_state.k_enc, HYBRID_NTOR_KEY_ENC_LEN);
    }

    // Verify keys match
    if (memcmp(client_state.k_enc, server_state.k_enc, HYBRID_NTOR_KEY_ENC_LEN) != 0) {
        printf("FAIL: Client and server keys do not match!\n");
        print_hex("  Client K_enc", client_state.k_enc, HYBRID_NTOR_KEY_ENC_LEN);
        print_hex("  Server K_enc", server_state.k_enc, HYBRID_NTOR_KEY_ENC_LEN);
        return -1;
    }

    if (verbose) {
        printf("\n=== KEY AGREEMENT VERIFIED ===\n");
        printf("  Client and Server derived identical session keys!\n");
    }

    // Cleanup
    hybrid_ntor_client_state_cleanup(&client_state);
    hybrid_ntor_server_state_cleanup(&server_state);

    return 0;
}

/**
 * Test tampered reply (should fail AUTH)
 */
static int test_tampered_reply(void) {
    hybrid_ntor_client_state client_state;
    hybrid_ntor_server_state server_state;

    uint8_t onionskin[HYBRID_NTOR_ONIONSKIN_LEN];
    uint8_t reply[HYBRID_NTOR_REPLY_LEN];
    uint8_t relay_identity[HYBRID_NTOR_RELAY_ID_LENGTH];

    memset(relay_identity, 0x42, sizeof(relay_identity));

    // Create onionskin
    if (hybrid_ntor_client_create_onionskin(&client_state, onionskin, relay_identity) != HYBRID_NTOR_SUCCESS) {
        return -1;
    }

    // Create reply
    if (hybrid_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity) != HYBRID_NTOR_SUCCESS) {
        return -1;
    }

    // Tamper with reply (flip a bit in AUTH)
    reply[HYBRID_NTOR_REPLY_LEN - 1] ^= 0x01;

    // This should fail
    int result = hybrid_ntor_client_finish_handshake(&client_state, reply);
    if (result == HYBRID_NTOR_AUTH_FAIL) {
        return 0; // Expected failure
    }

    printf("FAIL: Tampered reply should have been rejected!\n");
    return -1;
}

/**
 * Performance benchmark
 */
static void benchmark_hybrid_ntor(void) {
    hybrid_ntor_client_state client_state;
    hybrid_ntor_server_state server_state;

    uint8_t onionskin[HYBRID_NTOR_ONIONSKIN_LEN];
    uint8_t reply[HYBRID_NTOR_REPLY_LEN];
    uint8_t relay_identity[HYBRID_NTOR_RELAY_ID_LENGTH];

    memset(relay_identity, 0x42, sizeof(relay_identity));

    clock_t start, end;
    double create_time = 0, reply_time = 0, finish_time = 0;

    printf("\nRunning %d iterations...\n", TEST_ITERATIONS);

    for (int i = 0; i < TEST_ITERATIONS; i++) {
        // Measure create onionskin
        start = clock();
        hybrid_ntor_client_create_onionskin(&client_state, onionskin, relay_identity);
        end = clock();
        create_time += ((double)(end - start)) / CLOCKS_PER_SEC * 1000000;

        // Measure create reply
        start = clock();
        hybrid_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity);
        end = clock();
        reply_time += ((double)(end - start)) / CLOCKS_PER_SEC * 1000000;

        // Measure finish handshake
        start = clock();
        hybrid_ntor_client_finish_handshake(&client_state, reply);
        end = clock();
        finish_time += ((double)(end - start)) / CLOCKS_PER_SEC * 1000000;

        // Cleanup
        hybrid_ntor_client_state_cleanup(&client_state);
        hybrid_ntor_server_state_cleanup(&server_state);
    }

    printf("\n=== Hybrid NTOR Performance ===\n");
    printf("  Client create onionskin: %.2f us (avg)\n", create_time / TEST_ITERATIONS);
    printf("  Server create reply:     %.2f us (avg)\n", reply_time / TEST_ITERATIONS);
    printf("  Client finish handshake: %.2f us (avg)\n", finish_time / TEST_ITERATIONS);
    printf("  Total handshake:         %.2f us (avg)\n",
           (create_time + reply_time + finish_time) / TEST_ITERATIONS);
    printf("\n");
    printf("  Message sizes:\n");
    printf("    Onionskin: %d bytes\n", HYBRID_NTOR_ONIONSKIN_LEN);
    printf("    Reply:     %d bytes\n", HYBRID_NTOR_REPLY_LEN);
}

int main(void) {
    printf("====================================\n");
    printf("  Hybrid NTOR Test Suite\n");
    printf("====================================\n\n");

    printf("Protocol: Kyber-512 + X25519 Hybrid\n");
    printf("  Onionskin size: %d bytes\n", HYBRID_NTOR_ONIONSKIN_LEN);
    printf("  Reply size:     %d bytes\n", HYBRID_NTOR_REPLY_LEN);
    printf("\n");

    // Test 1: Single handshake with verbose output
    printf("Test 1: Single handshake (verbose)...\n");
    if (test_single_handshake(1) != 0) {
        printf("\n*** TEST 1 FAILED ***\n");
        return 1;
    }
    printf("\n*** TEST 1 PASSED ***\n\n");

    // Test 2: Multiple handshakes
    printf("Test 2: Multiple handshakes (%d iterations)...\n", TEST_ITERATIONS);
    for (int i = 0; i < TEST_ITERATIONS; i++) {
        if (test_single_handshake(0) != 0) {
            printf("FAIL at iteration %d\n", i);
            return 1;
        }
    }
    printf("*** TEST 2 PASSED ***\n\n");

    // Test 3: Tampered reply detection
    printf("Test 3: Tampered reply detection...\n");
    if (test_tampered_reply() != 0) {
        printf("\n*** TEST 3 FAILED ***\n");
        return 1;
    }
    printf("*** TEST 3 PASSED ***\n");

    // Benchmark
    benchmark_hybrid_ntor();

    printf("====================================\n");
    printf("  All tests passed!\n");
    printf("====================================\n");

    return 0;
}
