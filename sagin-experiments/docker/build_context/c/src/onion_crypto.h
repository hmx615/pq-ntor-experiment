/**
 * onion_crypto.h - Tor Onion Encryption/Decryption Layer
 *
 * Implements multi-layer encryption (onion routing) for Tor cells.
 * Uses AES-128-CTR for stream cipher encryption.
 */

#ifndef ONION_CRYPTO_H
#define ONION_CRYPTO_H

#include <stdint.h>
#include <stdbool.h>
#include "cell.h"

/* Maximum number of layers in the onion (3 hops) */
#define MAX_ONION_LAYERS 3

/* Key material size per layer (from PQ-Ntor handshake) */
#define LAYER_KEY_SIZE 32      // AES-256 key
#define LAYER_IV_SIZE 16       // AES block size

/**
 * Onion encryption layer
 * Each hop in the circuit has one layer with its own keys
 */
typedef struct {
    bool active;                    // Is this layer initialized?
    uint8_t forward_key[LAYER_KEY_SIZE];   // For client→relay direction
    uint8_t backward_key[LAYER_KEY_SIZE];  // For relay→client direction
    uint8_t forward_iv[LAYER_IV_SIZE];     // Forward IV/counter
    uint8_t backward_iv[LAYER_IV_SIZE];    // Backward IV/counter
    void *forward_ctx;              // OpenSSL cipher context (forward)
    void *backward_ctx;             // OpenSSL cipher context (backward)
} onion_layer_t;

/**
 * Onion encryption state
 * Maintains all layers for a circuit
 */
typedef struct {
    int num_layers;                 // Number of active layers (1-3)
    onion_layer_t layers[MAX_ONION_LAYERS];
} onion_crypto_t;

/*
 * Initialization and cleanup
 */

/**
 * Initialize onion crypto state
 */
int onion_crypto_init(onion_crypto_t *crypto);

/**
 * Free onion crypto state and clear keys
 */
void onion_crypto_free(onion_crypto_t *crypto);

/*
 * Layer management
 */

/**
 * Initialize a single onion layer (for relay nodes)
 * @param layer Onion layer to initialize
 * @param key_material Key material from PQ-Ntor handshake (80 bytes)
 *        Format: Kf (32) | Kb (32) | IVf (8) | IVb (8)
 * @return 0 on success, -1 on error
 */
int onion_layer_init(onion_layer_t *layer, const uint8_t *key_material);

/**
 * Free a single onion layer
 */
void onion_layer_free(onion_layer_t *layer);

/**
 * Add a new layer to the onion
 * @param crypto Onion crypto state
 * @param layer_index Layer index (0 for Guard, 1 for Middle, 2 for Exit)
 * @param key_material Key material from PQ-Ntor handshake (80 bytes)
 *        Format: Kf (32) | Kb (32) | IVf (8) | IVb (8)
 * @return 0 on success, -1 on error
 */
int onion_crypto_add_layer(onion_crypto_t *crypto,
                           int layer_index,
                           const uint8_t *key_material);

/**
 * Remove a layer from the onion (for circuit teardown)
 */
int onion_crypto_remove_layer(onion_crypto_t *crypto, int layer_index);

/*
 * Encryption operations (Client side)
 */

/**
 * Encrypt RELAY cell payload for sending (onion wrap)
 * Applies encryption in reverse order: Exit -> Middle -> Guard
 * @param crypto Onion crypto state
 * @param payload RELAY cell payload (507 bytes)
 * @return 0 on success, -1 on error
 */
int onion_crypto_encrypt(onion_crypto_t *crypto, uint8_t *payload);

/**
 * Decrypt RELAY cell payload after receiving (onion unwrap)
 * Applies decryption in order: Guard -> Middle -> Exit
 * @param crypto Onion crypto state
 * @param payload RELAY cell payload (507 bytes)
 * @return 0 on success, -1 on error
 */
int onion_crypto_decrypt(onion_crypto_t *crypto, uint8_t *payload);

/*
 * Decryption operations (Relay node side)
 */

/**
 * Peel one layer of encryption (relay node)
 * @param layer Single layer to decrypt with
 * @param payload RELAY cell payload (507 bytes)
 * @param is_recognized Output: true if this layer recognizes the cell
 * @return 0 on success, -1 on error
 */
int onion_crypto_peel_layer(onion_layer_t *layer,
                            uint8_t *payload,
                            bool *is_recognized);

/**
 * Add one layer of encryption for backward direction (relay node)
 * @param layer Single layer to encrypt with
 * @param payload RELAY cell payload (507 bytes)
 * @return 0 on success, -1 on error
 */
int onion_crypto_add_layer_back(onion_layer_t *layer, uint8_t *payload);

/*
 * Key material extraction (from PQ-Ntor)
 */

/**
 * Extract key material from PQ-Ntor output
 * PQ-Ntor produces: Kf (32) | Kb (32) | IVf (16) | IVb (16) = 96 bytes
 * But we only use 72 bytes for compatibility
 * @param ntor_output Output from pq_ntor_client_finish or pq_ntor_server_reply
 * @param key_material Output buffer (72 bytes)
 */
int onion_crypto_extract_keys(const uint8_t *ntor_output, uint8_t *key_material);

/*
 * RELAY cell digest handling
 */

/**
 * Update and verify RELAY cell digest
 * The digest field in RELAY cells is used to verify integrity
 * @param layer Layer with running digest state
 * @param payload RELAY cell payload (507 bytes)
 * @param is_sending true if sending (update digest), false if receiving (verify)
 * @return 0 on success, -1 on error
 */
int onion_crypto_update_digest(onion_layer_t *layer,
                               uint8_t *payload,
                               bool is_sending);

/**
 * Check if RELAY cell is recognized by this layer
 * A cell is "recognized" if its digest is valid for this layer
 * @param layer Layer to check against
 * @param payload RELAY cell payload (507 bytes)
 * @return true if recognized, false otherwise
 */
bool onion_crypto_is_recognized(onion_layer_t *layer, const uint8_t *payload);

/*
 * Testing and debugging
 */

/**
 * Encrypt payload with a single layer (for testing)
 */
int onion_crypto_encrypt_single(onion_layer_t *layer, uint8_t *payload, size_t len);

/**
 * Decrypt payload with a single layer (for testing)
 */
int onion_crypto_decrypt_single(onion_layer_t *layer, uint8_t *payload, size_t len);

#endif /* ONION_CRYPTO_H */
