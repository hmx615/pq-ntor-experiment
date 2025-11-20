/**
 * test_onion.c - Test Onion Encryption/Decryption
 */

#include "../src/onion_crypto.h"
#include "../src/cell.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>

// Generate test key material
void generate_test_keys(uint8_t *key_material) {
    for (int i = 0; i < 80; i++) {
        key_material[i] = i & 0xFF;
    }
}

void test_single_layer_encrypt_decrypt() {
    printf("Testing single layer encryption/decryption...\n");

    uint8_t key_material[80];
    generate_test_keys(key_material);

    // Create two crypto contexts with same keys (simulating client and relay)
    onion_crypto_t client_crypto, relay_crypto;
    assert(onion_crypto_init(&client_crypto) == 0);
    assert(onion_crypto_init(&relay_crypto) == 0);

    assert(onion_crypto_add_layer(&client_crypto, 0, key_material) == 0);
    assert(onion_crypto_add_layer(&relay_crypto, 0, key_material) == 0);

    // Test data
    uint8_t original[CELL_PAYLOAD_LEN];
    memset(original, 0xAA, CELL_PAYLOAD_LEN);

    // Client encrypts
    uint8_t encrypted[CELL_PAYLOAD_LEN];
    memcpy(encrypted, original, CELL_PAYLOAD_LEN);
    assert(onion_crypto_encrypt(&client_crypto, encrypted) == 0);

    // Should be different after encryption
    assert(memcmp(original, encrypted, CELL_PAYLOAD_LEN) != 0);

    // Relay decrypts (peels layer)
    bool recognized;
    assert(onion_crypto_peel_layer(&relay_crypto.layers[0], encrypted, &recognized) == 0);

    // Should match original
    assert(memcmp(original, encrypted, CELL_PAYLOAD_LEN) == 0);

    onion_crypto_free(&client_crypto);
    onion_crypto_free(&relay_crypto);
    printf("  ✓ Single layer encryption/decryption\n");
}

void test_multi_layer_encrypt_decrypt() {
    printf("Testing 3-layer encryption (forward direction)...\n");

    onion_crypto_t crypto;
    assert(onion_crypto_init(&crypto) == 0);

    // Generate test keys for 3 layers
    uint8_t key1[80], key2[80], key3[80];
    for (int i = 0; i < 80; i++) {
        key1[i] = (i + 1) & 0xFF;
        key2[i] = (i + 2) & 0xFF;
        key3[i] = (i + 3) & 0xFF;
    }

    // Add 3 layers (Guard, Middle, Exit)
    assert(onion_crypto_add_layer(&crypto, 0, key1) == 0);  // Guard
    assert(onion_crypto_add_layer(&crypto, 1, key2) == 0);  // Middle
    assert(onion_crypto_add_layer(&crypto, 2, key3) == 0);  // Exit
    assert(crypto.num_layers == 3);

    // Test data
    uint8_t original[CELL_PAYLOAD_LEN];
    const char *message = "Hello through 3 hops!";
    memset(original, 0, CELL_PAYLOAD_LEN);
    strncpy((char *)original, message, CELL_PAYLOAD_LEN - 1);

    // Client encrypts with all 3 layers (Exit -> Middle -> Guard)
    uint8_t encrypted[CELL_PAYLOAD_LEN];
    memcpy(encrypted, original, CELL_PAYLOAD_LEN);
    assert(onion_crypto_encrypt(&crypto, encrypted) == 0);

    // Should be different
    assert(memcmp(original, encrypted, strlen(message)) != 0);

    // Now simulate each hop peeling one layer
    // Create relay contexts
    onion_crypto_t guard_crypto, middle_crypto, exit_crypto;
    onion_crypto_init(&guard_crypto);
    onion_crypto_init(&middle_crypto);
    onion_crypto_init(&exit_crypto);

    onion_crypto_add_layer(&guard_crypto, 0, key1);
    onion_crypto_add_layer(&middle_crypto, 0, key2);
    onion_crypto_add_layer(&exit_crypto, 0, key3);

    // Guard peels first layer
    bool recognized;
    assert(onion_crypto_peel_layer(&guard_crypto.layers[0], encrypted, &recognized) == 0);

    // Middle peels second layer
    assert(onion_crypto_peel_layer(&middle_crypto.layers[0], encrypted, &recognized) == 0);

    // Exit peels third layer
    assert(onion_crypto_peel_layer(&exit_crypto.layers[0], encrypted, &recognized) == 0);

    // Should match original now
    assert(memcmp(original, encrypted, CELL_PAYLOAD_LEN) == 0);

    onion_crypto_free(&crypto);
    onion_crypto_free(&guard_crypto);
    onion_crypto_free(&middle_crypto);
    onion_crypto_free(&exit_crypto);

    printf("  ✓ 3-layer encryption/decryption\n");
}

void test_relay_peel_layer() {
    printf("Testing relay node layer peeling...\n");

    uint8_t key_material[80];
    generate_test_keys(key_material);

    // Create two separate contexts (client and relay) with same keys
    onion_crypto_t client_crypto, relay_crypto;
    onion_crypto_init(&client_crypto);
    onion_crypto_init(&relay_crypto);

    assert(onion_crypto_add_layer(&client_crypto, 0, key_material) == 0);
    assert(onion_crypto_add_layer(&relay_crypto, 0, key_material) == 0);

    // Create test payload
    uint8_t payload[CELL_PAYLOAD_LEN];
    memset(payload, 0, CELL_PAYLOAD_LEN);
    payload[0] = RELAY_DATA;  // relay_command
    payload[1] = 0;           // recognized = 0 (should be recognized)
    payload[2] = 0;

    // Client encrypts
    uint8_t encrypted[CELL_PAYLOAD_LEN];
    memcpy(encrypted, payload, CELL_PAYLOAD_LEN);
    assert(onion_crypto_encrypt(&client_crypto, encrypted) == 0);

    // Relay node peels the layer
    bool is_recognized = false;
    assert(onion_crypto_peel_layer(&relay_crypto.layers[0], encrypted, &is_recognized) == 0);

    // After peeling, should match original
    assert(memcmp(payload, encrypted, CELL_PAYLOAD_LEN) == 0);
    assert(is_recognized == true);

    onion_crypto_free(&client_crypto);
    onion_crypto_free(&relay_crypto);
    printf("  ✓ Relay layer peeling\n");
}

void test_key_extraction() {
    printf("Testing key material extraction...\n");

    // Simulate PQ-Ntor output (96 bytes)
    uint8_t ntor_output[96];
    for (int i = 0; i < 96; i++) {
        ntor_output[i] = i;
    }

    uint8_t key_material[80];
    assert(onion_crypto_extract_keys(ntor_output, key_material) == 0);

    // Verify extraction
    assert(memcmp(key_material, ntor_output, 32) == 0);        // Kf
    assert(memcmp(key_material + 32, ntor_output + 32, 32) == 0); // Kb
    assert(memcmp(key_material + 64, ntor_output + 64, 8) == 0);  // IVf
    assert(memcmp(key_material + 72, ntor_output + 80, 8) == 0);  // IVb

    printf("  ✓ Key material extraction\n");
}

void test_circuit_simulation() {
    printf("Testing circuit simulation (Client -> Guard -> Middle -> Exit)...\n");

    // Setup: 3 nodes with their own crypto contexts
    onion_crypto_t client_crypto, guard_crypto, middle_crypto, exit_crypto;

    onion_crypto_init(&client_crypto);
    onion_crypto_init(&guard_crypto);
    onion_crypto_init(&middle_crypto);
    onion_crypto_init(&exit_crypto);

    // Generate keys for each hop
    uint8_t guard_keys[80], middle_keys[80], exit_keys[80];
    for (int i = 0; i < 80; i++) {
        guard_keys[i] = (i * 1) & 0xFF;
        middle_keys[i] = (i * 2) & 0xFF;
        exit_keys[i] = (i * 3) & 0xFF;
    }

    // Client adds all 3 layers
    assert(onion_crypto_add_layer(&client_crypto, 0, guard_keys) == 0);
    assert(onion_crypto_add_layer(&client_crypto, 1, middle_keys) == 0);
    assert(onion_crypto_add_layer(&client_crypto, 2, exit_keys) == 0);

    // Each relay gets its own layer
    assert(onion_crypto_add_layer(&guard_crypto, 0, guard_keys) == 0);
    assert(onion_crypto_add_layer(&middle_crypto, 0, middle_keys) == 0);
    assert(onion_crypto_add_layer(&exit_crypto, 0, exit_keys) == 0);

    // Client creates a RELAY cell
    const char *message = "Secret message to exit";
    uint8_t payload[CELL_PAYLOAD_LEN];
    memset(payload, 0, CELL_PAYLOAD_LEN);

    // RELAY cell format: cmd(1) | recognized(2) | stream_id(2) | digest(4) | length(2) | data(...)
    payload[0] = RELAY_DATA;
    payload[1] = 0;  // recognized = 0
    payload[2] = 0;
    uint16_t msg_len = strlen(message);
    payload[9] = (msg_len >> 8) & 0xFF;
    payload[10] = msg_len & 0xFF;
    memcpy(payload + 11, message, msg_len);

    // Save original for comparison
    uint8_t original[CELL_PAYLOAD_LEN];
    memcpy(original, payload, CELL_PAYLOAD_LEN);

    // Client encrypts (Exit -> Middle -> Guard)
    assert(onion_crypto_encrypt(&client_crypto, payload) == 0);

    // Guard receives and peels one layer
    bool recognized = false;
    uint8_t guard_payload[CELL_PAYLOAD_LEN];
    memcpy(guard_payload, payload, CELL_PAYLOAD_LEN);
    assert(onion_crypto_peel_layer(&guard_crypto.layers[0], guard_payload, &recognized) == 0);
    assert(recognized == false);  // Guard shouldn't recognize

    // Middle receives and peels one layer
    uint8_t middle_payload[CELL_PAYLOAD_LEN];
    memcpy(middle_payload, guard_payload, CELL_PAYLOAD_LEN);
    assert(onion_crypto_peel_layer(&middle_crypto.layers[0], middle_payload, &recognized) == 0);
    assert(recognized == false);  // Middle shouldn't recognize

    // Exit receives and peels final layer
    uint8_t exit_payload[CELL_PAYLOAD_LEN];
    memcpy(exit_payload, middle_payload, CELL_PAYLOAD_LEN);
    assert(onion_crypto_peel_layer(&exit_crypto.layers[0], exit_payload, &recognized) == 0);
    assert(recognized == true);  // Exit should recognize!

    // Exit should see the original message
    assert(memcmp(exit_payload, original, CELL_PAYLOAD_LEN) == 0);

    onion_crypto_free(&client_crypto);
    onion_crypto_free(&guard_crypto);
    onion_crypto_free(&middle_crypto);
    onion_crypto_free(&exit_crypto);

    printf("  ✓ Circuit simulation\n");
}

int main() {
    printf("\n=== Onion Encryption Tests ===\n\n");

    test_single_layer_encrypt_decrypt();
    test_multi_layer_encrypt_decrypt();
    test_relay_peel_layer();
    test_key_extraction();
    test_circuit_simulation();

    printf("\n=== All Onion Encryption Tests Passed! ===\n\n");
    return 0;
}
