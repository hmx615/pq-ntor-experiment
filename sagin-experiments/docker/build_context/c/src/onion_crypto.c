/**
 * onion_crypto.c - Tor Onion Encryption/Decryption Layer Implementation
 */

#include "onion_crypto.h"
#include "crypto_utils.h"
#include <stdlib.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/sha.h>

/*
 * Helper functions for AES-CTR encryption
 */

static int aes_ctr_init(EVP_CIPHER_CTX **ctx,
                       const uint8_t *key,
                       const uint8_t *iv) {
    *ctx = EVP_CIPHER_CTX_new();
    if (!*ctx) {
        return -1;
    }

    // Use AES-256-CTR
    if (EVP_EncryptInit_ex(*ctx, EVP_aes_256_ctr(), NULL, key, iv) != 1) {
        EVP_CIPHER_CTX_free(*ctx);
        *ctx = NULL;
        return -1;
    }

    return 0;
}

static int aes_ctr_process(EVP_CIPHER_CTX *ctx,
                          uint8_t *out,
                          const uint8_t *in,
                          size_t len) {
    if (!ctx || !out || !in) {
        return -1;
    }

    int outlen;
    if (EVP_EncryptUpdate(ctx, out, &outlen, in, len) != 1) {
        return -1;
    }

    return 0;
}

static void aes_ctr_cleanup(EVP_CIPHER_CTX *ctx) {
    if (ctx) {
        EVP_CIPHER_CTX_free(ctx);
    }
}

/*
 * Initialization and cleanup
 */

int onion_crypto_init(onion_crypto_t *crypto) {
    if (!crypto) {
        return -1;
    }

    memset(crypto, 0, sizeof(onion_crypto_t));
    crypto->num_layers = 0;

    return 0;
}

void onion_crypto_free(onion_crypto_t *crypto) {
    if (!crypto) {
        return;
    }

    // Clean up all layers
    for (int i = 0; i < MAX_ONION_LAYERS; i++) {
        if (crypto->layers[i].active) {
            // Free cipher contexts
            if (crypto->layers[i].forward_ctx) {
                aes_ctr_cleanup((EVP_CIPHER_CTX *)crypto->layers[i].forward_ctx);
            }
            if (crypto->layers[i].backward_ctx) {
                aes_ctr_cleanup((EVP_CIPHER_CTX *)crypto->layers[i].backward_ctx);
            }

            // Clear keys
            memset(&crypto->layers[i], 0, sizeof(onion_layer_t));
        }
    }

    memset(crypto, 0, sizeof(onion_crypto_t));
}

/*
 * Single layer management (for relay nodes)
 */

int onion_layer_init(onion_layer_t *layer, const uint8_t *key_material) {
    if (!layer || !key_material) {
        return -1;
    }

    // Extract keys from key material
    // Format: Kf (32) | Kb (32) | IVf (8) | IVb (8) = 80 bytes
    memcpy(layer->forward_key, key_material, 32);
    memcpy(layer->backward_key, key_material + 32, 32);

    // Expand 8-byte IVs to 16 bytes (pad with zeros)
    memset(layer->forward_iv, 0, LAYER_IV_SIZE);
    memcpy(layer->forward_iv, key_material + 64, 8);

    memset(layer->backward_iv, 0, LAYER_IV_SIZE);
    memcpy(layer->backward_iv, key_material + 72, 8);

    // Initialize cipher contexts
    if (aes_ctr_init((EVP_CIPHER_CTX **)&layer->forward_ctx,
                     layer->forward_key,
                     layer->forward_iv) != 0) {
        return -1;
    }

    if (aes_ctr_init((EVP_CIPHER_CTX **)&layer->backward_ctx,
                     layer->backward_key,
                     layer->backward_iv) != 0) {
        aes_ctr_cleanup((EVP_CIPHER_CTX *)layer->forward_ctx);
        layer->forward_ctx = NULL;
        return -1;
    }

    layer->active = true;
    return 0;
}

void onion_layer_free(onion_layer_t *layer) {
    if (!layer) return;

    if (layer->forward_ctx) {
        aes_ctr_cleanup((EVP_CIPHER_CTX *)layer->forward_ctx);
        layer->forward_ctx = NULL;
    }
    if (layer->backward_ctx) {
        aes_ctr_cleanup((EVP_CIPHER_CTX *)layer->backward_ctx);
        layer->backward_ctx = NULL;
    }

    // Clear sensitive data
    memset(layer->forward_key, 0, LAYER_KEY_SIZE);
    memset(layer->backward_key, 0, LAYER_KEY_SIZE);
    memset(layer->forward_iv, 0, LAYER_IV_SIZE);
    memset(layer->backward_iv, 0, LAYER_IV_SIZE);
    layer->active = false;
}

/*
 * Multi-layer management (for clients)
 */

int onion_crypto_add_layer(onion_crypto_t *crypto,
                           int layer_index,
                           const uint8_t *key_material) {
    if (!crypto || !key_material) {
        return -1;
    }

    if (layer_index < 0 || layer_index >= MAX_ONION_LAYERS) {
        return -1;
    }

    if (crypto->layers[layer_index].active) {
        // Layer already exists, clean it up first
        onion_crypto_remove_layer(crypto, layer_index);
    }

    onion_layer_t *layer = &crypto->layers[layer_index];

    // Extract keys from key material
    // Format: Kf (32) | Kb (32) | IVf (8) | IVb (8) = 80 bytes
    memcpy(layer->forward_key, key_material, 32);
    memcpy(layer->backward_key, key_material + 32, 32);

    // Expand 8-byte IVs to 16 bytes (pad with zeros)
    memset(layer->forward_iv, 0, LAYER_IV_SIZE);
    memcpy(layer->forward_iv, key_material + 64, 8);

    memset(layer->backward_iv, 0, LAYER_IV_SIZE);
    memcpy(layer->backward_iv, key_material + 72, 8);

    // Initialize cipher contexts
    if (aes_ctr_init((EVP_CIPHER_CTX **)&layer->forward_ctx,
                     layer->forward_key,
                     layer->forward_iv) != 0) {
        return -1;
    }

    if (aes_ctr_init((EVP_CIPHER_CTX **)&layer->backward_ctx,
                     layer->backward_key,
                     layer->backward_iv) != 0) {
        aes_ctr_cleanup((EVP_CIPHER_CTX *)layer->forward_ctx);
        layer->forward_ctx = NULL;
        return -1;
    }

    layer->active = true;
    crypto->num_layers++;

    return 0;
}

int onion_crypto_remove_layer(onion_crypto_t *crypto, int layer_index) {
    if (!crypto) {
        return -1;
    }

    if (layer_index < 0 || layer_index >= MAX_ONION_LAYERS) {
        return -1;
    }

    onion_layer_t *layer = &crypto->layers[layer_index];
    if (!layer->active) {
        return 0;  // Already removed
    }

    // Clean up cipher contexts
    if (layer->forward_ctx) {
        aes_ctr_cleanup((EVP_CIPHER_CTX *)layer->forward_ctx);
    }
    if (layer->backward_ctx) {
        aes_ctr_cleanup((EVP_CIPHER_CTX *)layer->backward_ctx);
    }

    // Clear sensitive data
    memset(layer, 0, sizeof(onion_layer_t));
    crypto->num_layers--;

    return 0;
}

/*
 * Client-side encryption operations
 */

int onion_crypto_encrypt(onion_crypto_t *crypto, uint8_t *payload) {
    if (!crypto || !payload) {
        return -1;
    }

    // Apply encryption in reverse order: Exit (2) -> Middle (1) -> Guard (0)
    // This ensures Guard sees the outermost layer
    for (int i = MAX_ONION_LAYERS - 1; i >= 0; i--) {
        if (crypto->layers[i].active) {
            if (aes_ctr_process((EVP_CIPHER_CTX *)crypto->layers[i].forward_ctx,
                               payload, payload, CELL_PAYLOAD_LEN) != 0) {
                return -1;
            }
        }
    }

    return 0;
}

int onion_crypto_decrypt(onion_crypto_t *crypto, uint8_t *payload) {
    if (!crypto || !payload) {
        return -1;
    }

    // Apply decryption in forward order: Guard (0) -> Middle (1) -> Exit (2)
    for (int i = 0; i < MAX_ONION_LAYERS; i++) {
        if (crypto->layers[i].active) {
            if (aes_ctr_process((EVP_CIPHER_CTX *)crypto->layers[i].backward_ctx,
                               payload, payload, CELL_PAYLOAD_LEN) != 0) {
                return -1;
            }
        }
    }

    return 0;
}

/*
 * Relay node operations
 */

int onion_crypto_peel_layer(onion_layer_t *layer,
                            uint8_t *payload,
                            bool *is_recognized) {
    if (!layer || !payload || !is_recognized) {
        return -1;
    }

    if (!layer->active) {
        return -1;
    }

    // Decrypt one layer
    if (aes_ctr_process((EVP_CIPHER_CTX *)layer->forward_ctx,
                       payload, payload, CELL_PAYLOAD_LEN) != 0) {
        return -1;
    }

    // Check if cell is recognized (simplified: check if 'recognized' field is 0)
    // In real Tor, this would verify the digest
    uint16_t recognized;
    memcpy(&recognized, payload + 1, 2);  // Offset 1 in RELAY cell
    *is_recognized = (recognized == 0);

    return 0;
}

int onion_crypto_add_layer_back(onion_layer_t *layer, uint8_t *payload) {
    if (!layer || !payload) {
        return -1;
    }

    if (!layer->active) {
        return -1;
    }

    // Encrypt one layer in backward direction
    if (aes_ctr_process((EVP_CIPHER_CTX *)layer->backward_ctx,
                       payload, payload, CELL_PAYLOAD_LEN) != 0) {
        return -1;
    }

    return 0;
}

/*
 * Key material extraction
 */

int onion_crypto_extract_keys(const uint8_t *ntor_output, uint8_t *key_material) {
    if (!ntor_output || !key_material) {
        return -1;
    }

    // PQ-Ntor output format (from HKDF):
    // Kf (32) | Kb (32) | IVf (16) | IVb (16) = 96 bytes
    // We extract: Kf (32) | Kb (32) | IVf (8) | IVb (8) = 72 bytes

    memcpy(key_material, ntor_output, 32);        // Kf
    memcpy(key_material + 32, ntor_output + 32, 32); // Kb
    memcpy(key_material + 64, ntor_output + 64, 8);  // IVf (first 8 bytes)
    memcpy(key_material + 72, ntor_output + 80, 8);  // IVb (first 8 bytes)

    return 0;
}

/*
 * RELAY cell digest handling (simplified)
 */

int onion_crypto_update_digest(onion_layer_t *layer,
                               uint8_t *payload,
                               bool is_sending) {
    if (!layer || !payload) {
        return -1;
    }

    // Simplified digest handling
    // In real Tor, this maintains a running SHA-1 digest
    // For our implementation, we just set digest to 0
    if (is_sending) {
        // Clear digest field when sending
        memset(payload + 5, 0, 4);  // Offset 5 in RELAY cell
    }

    return 0;
}

bool onion_crypto_is_recognized(onion_layer_t *layer, const uint8_t *payload) {
    if (!layer || !payload) {
        return false;
    }

    // Simplified recognition check
    // In real Tor, this verifies the digest matches
    // For our implementation, we check if 'recognized' field is 0
    uint16_t recognized;
    memcpy(&recognized, payload + 1, 2);

    return (recognized == 0);
}

/*
 * Testing functions
 */

int onion_crypto_encrypt_single(onion_layer_t *layer, uint8_t *payload, size_t len) {
    if (!layer || !payload || !layer->active) {
        return -1;
    }

    return aes_ctr_process((EVP_CIPHER_CTX *)layer->forward_ctx,
                          payload, payload, len);
}

int onion_crypto_decrypt_single(onion_layer_t *layer, uint8_t *payload, size_t len) {
    if (!layer || !payload || !layer->active) {
        return -1;
    }

    return aes_ctr_process((EVP_CIPHER_CTX *)layer->backward_ctx,
                          payload, payload, len);
}
