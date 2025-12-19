/**
 * @file hybrid_ntor.c
 * @brief Hybrid Ntor Handshake Protocol Implementation
 *
 * Combines Kyber-512 KEM with X25519 ECDH for hybrid post-quantum security.
 */

#include "hybrid_ntor.h"
#include <string.h>
#include <stdio.h>
#include <openssl/evp.h>
#include <openssl/rand.h>

/**
 * Generate X25519 keypair
 */
static int generate_x25519_keypair(uint8_t *public_key, uint8_t *secret_key) {
    EVP_PKEY *pkey = NULL;
    EVP_PKEY_CTX *pctx = NULL;
    size_t pubkey_len = X25519_KEY_SIZE;
    size_t privkey_len = X25519_KEY_SIZE;
    int ret = HYBRID_NTOR_ERROR;

    pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
    if (!pctx) goto cleanup;

    if (EVP_PKEY_keygen_init(pctx) <= 0) goto cleanup;
    if (EVP_PKEY_keygen(pctx, &pkey) <= 0) goto cleanup;

    if (EVP_PKEY_get_raw_public_key(pkey, public_key, &pubkey_len) <= 0) goto cleanup;
    if (pubkey_len != X25519_KEY_SIZE) goto cleanup;

    if (EVP_PKEY_get_raw_private_key(pkey, secret_key, &privkey_len) <= 0) goto cleanup;
    if (privkey_len != X25519_KEY_SIZE) goto cleanup;

    ret = HYBRID_NTOR_SUCCESS;

cleanup:
    if (pkey) EVP_PKEY_free(pkey);
    if (pctx) EVP_PKEY_CTX_free(pctx);
    return ret;
}

/**
 * Perform X25519 key exchange
 */
static int x25519_key_exchange(uint8_t *shared_secret,
                               const uint8_t *my_secret_key,
                               const uint8_t *peer_public_key) {
    EVP_PKEY *my_pkey = NULL;
    EVP_PKEY *peer_pkey = NULL;
    EVP_PKEY_CTX *ctx = NULL;
    size_t secret_len = X25519_SHARED_SIZE;
    int ret = HYBRID_NTOR_ERROR;

    my_pkey = EVP_PKEY_new_raw_private_key(EVP_PKEY_X25519, NULL,
                                            my_secret_key, X25519_KEY_SIZE);
    if (!my_pkey) goto cleanup;

    peer_pkey = EVP_PKEY_new_raw_public_key(EVP_PKEY_X25519, NULL,
                                             peer_public_key, X25519_KEY_SIZE);
    if (!peer_pkey) goto cleanup;

    ctx = EVP_PKEY_CTX_new(my_pkey, NULL);
    if (!ctx) goto cleanup;

    if (EVP_PKEY_derive_init(ctx) <= 0) goto cleanup;
    if (EVP_PKEY_derive_set_peer(ctx, peer_pkey) <= 0) goto cleanup;
    if (EVP_PKEY_derive(ctx, shared_secret, &secret_len) <= 0) goto cleanup;
    if (secret_len != X25519_SHARED_SIZE) goto cleanup;

    ret = HYBRID_NTOR_SUCCESS;

cleanup:
    if (ctx) EVP_PKEY_CTX_free(ctx);
    if (peer_pkey) EVP_PKEY_free(peer_pkey);
    if (my_pkey) EVP_PKEY_free(my_pkey);
    return ret;
}

/**
 * Combine Kyber and X25519 shared secrets into hybrid shared secret
 * hybrid_ss = HKDF(kyber_ss || x25519_ss, "hybrid-ntor-combine")
 */
static int combine_shared_secrets(uint8_t *hybrid_ss,
                                  const uint8_t *kyber_ss,
                                  const uint8_t *x25519_ss) {
    uint8_t combined[KYBER_SHARED_SECRET_BYTES + X25519_SHARED_SIZE];

    // Concatenate: kyber_ss || x25519_ss
    memcpy(combined, kyber_ss, KYBER_SHARED_SECRET_BYTES);
    memcpy(combined + KYBER_SHARED_SECRET_BYTES, x25519_ss, X25519_SHARED_SIZE);

    // HKDF to derive hybrid shared secret
    int ret = hkdf_sha256(hybrid_ss, HYBRID_SHARED_SECRET_LEN,
                          NULL, 0,  // no salt
                          combined, sizeof(combined),
                          (const uint8_t *)HYBRID_NTOR_COMBINE_INFO,
                          strlen(HYBRID_NTOR_COMBINE_INFO));

    // Clear temporary buffer
    memset(combined, 0, sizeof(combined));

    return (ret == CRYPTO_SUCCESS) ? HYBRID_NTOR_SUCCESS : HYBRID_NTOR_ERROR;
}

/**
 * Build transcript for key derivation
 * transcript = kyber_pk || x25519_pk_client || kyber_ct || x25519_pk_server || relay_identity
 */
static void build_transcript(uint8_t *transcript, size_t *transcript_len,
                             const uint8_t *kyber_pk,
                             const uint8_t *x25519_pk_client,
                             const uint8_t *kyber_ct,
                             const uint8_t *x25519_pk_server,
                             const uint8_t *relay_identity) {
    size_t pos = 0;

    // Kyber public key
    memcpy(transcript + pos, kyber_pk, KYBER_PUBLIC_KEY_BYTES);
    pos += KYBER_PUBLIC_KEY_BYTES;

    // X25519 client public key
    memcpy(transcript + pos, x25519_pk_client, X25519_KEY_SIZE);
    pos += X25519_KEY_SIZE;

    // Kyber ciphertext (if available)
    if (kyber_ct) {
        memcpy(transcript + pos, kyber_ct, KYBER_CIPHERTEXT_BYTES);
        pos += KYBER_CIPHERTEXT_BYTES;
    }

    // X25519 server public key (if available)
    if (x25519_pk_server) {
        memcpy(transcript + pos, x25519_pk_server, X25519_KEY_SIZE);
        pos += X25519_KEY_SIZE;
    }

    // Relay identity
    memcpy(transcript + pos, relay_identity, HYBRID_NTOR_RELAY_ID_LENGTH);
    pos += HYBRID_NTOR_RELAY_ID_LENGTH;

    *transcript_len = pos;
}

/**
 * Derive session keys from hybrid shared secret
 * (K_auth || K_enc) = HKDF(hybrid_ss, transcript_hash, "hybrid-ntor-keys")
 */
static int derive_keys(uint8_t *k_auth, uint8_t *k_enc,
                       const uint8_t *hybrid_ss,
                       const uint8_t *transcript, size_t transcript_len) {
    uint8_t key_material[HYBRID_NTOR_KEY_MATERIAL_LEN];
    uint8_t transcript_hash[SHA256_DIGEST_LENGTH];

    // Hash transcript as salt
    if (sha256_hash(transcript_hash, transcript, transcript_len) != CRYPTO_SUCCESS) {
        return HYBRID_NTOR_ERROR;
    }

    // HKDF to derive key material
    int ret = hkdf_sha256(key_material, sizeof(key_material),
                          transcript_hash, sizeof(transcript_hash),
                          hybrid_ss, HYBRID_SHARED_SECRET_LEN,
                          (const uint8_t *)HYBRID_NTOR_KEYS_INFO,
                          strlen(HYBRID_NTOR_KEYS_INFO));

    if (ret != CRYPTO_SUCCESS) {
        memset(transcript_hash, 0, sizeof(transcript_hash));
        return HYBRID_NTOR_ERROR;
    }

    // Split key material
    memcpy(k_auth, key_material, HYBRID_NTOR_KEY_AUTH_LEN);
    memcpy(k_enc, key_material + HYBRID_NTOR_KEY_AUTH_LEN, HYBRID_NTOR_KEY_ENC_LEN);

    // Clear sensitive data
    memset(key_material, 0, sizeof(key_material));
    memset(transcript_hash, 0, sizeof(transcript_hash));

    return HYBRID_NTOR_SUCCESS;
}

/**
 * Client: Create onionskin
 */
int hybrid_ntor_client_create_onionskin(hybrid_ntor_client_state *state,
                                        uint8_t *onionskin,
                                        const uint8_t *relay_identity) {
    if (!state || !onionskin || !relay_identity) {
        return HYBRID_NTOR_ERROR;
    }

    // Generate Kyber keypair
    if (kyber_keypair(state->kyber_public_key, state->kyber_secret_key) != KYBER_SUCCESS) {
        return HYBRID_NTOR_ERROR;
    }

    // Generate X25519 keypair
    if (generate_x25519_keypair(state->x25519_public_key, state->x25519_secret_key) != HYBRID_NTOR_SUCCESS) {
        memset(state->kyber_secret_key, 0, sizeof(state->kyber_secret_key));
        return HYBRID_NTOR_ERROR;
    }

    // Save relay identity
    memcpy(state->relay_identity, relay_identity, HYBRID_NTOR_RELAY_ID_LENGTH);

    // Build onionskin: kyber_pk || x25519_pk || relay_identity
    size_t pos = 0;
    memcpy(onionskin + pos, state->kyber_public_key, KYBER_PUBLIC_KEY_BYTES);
    pos += KYBER_PUBLIC_KEY_BYTES;
    memcpy(onionskin + pos, state->x25519_public_key, X25519_KEY_SIZE);
    pos += X25519_KEY_SIZE;
    memcpy(onionskin + pos, relay_identity, HYBRID_NTOR_RELAY_ID_LENGTH);

    return HYBRID_NTOR_SUCCESS;
}

/**
 * Server: Process onionskin and create reply
 */
int hybrid_ntor_server_create_reply(hybrid_ntor_server_state *state,
                                    uint8_t *reply,
                                    const uint8_t *onionskin,
                                    const uint8_t *relay_identity) {
    if (!state || !reply || !onionskin || !relay_identity) {
        return HYBRID_NTOR_ERROR;
    }

    // Parse onionskin
    uint8_t client_kyber_pk[KYBER_PUBLIC_KEY_BYTES];
    uint8_t client_x25519_pk[X25519_KEY_SIZE];
    uint8_t received_relay_id[HYBRID_NTOR_RELAY_ID_LENGTH];

    size_t pos = 0;
    memcpy(client_kyber_pk, onionskin + pos, KYBER_PUBLIC_KEY_BYTES);
    pos += KYBER_PUBLIC_KEY_BYTES;
    memcpy(client_x25519_pk, onionskin + pos, X25519_KEY_SIZE);
    pos += X25519_KEY_SIZE;
    memcpy(received_relay_id, onionskin + pos, HYBRID_NTOR_RELAY_ID_LENGTH);

    // Verify relay identity
    if (memcmp(received_relay_id, relay_identity, HYBRID_NTOR_RELAY_ID_LENGTH) != 0) {
        fprintf(stderr, "Error: relay_identity mismatch\n");
        return HYBRID_NTOR_ERROR;
    }

    // 1. Kyber encapsulation
    uint8_t kyber_ct[KYBER_CIPHERTEXT_BYTES];
    if (kyber_encapsulate(kyber_ct, state->kyber_shared_secret, client_kyber_pk) != KYBER_SUCCESS) {
        return HYBRID_NTOR_ERROR;
    }

    // 2. Generate server X25519 keypair and perform ECDH
    uint8_t server_x25519_pk[X25519_KEY_SIZE];
    uint8_t server_x25519_sk[X25519_KEY_SIZE];

    if (generate_x25519_keypair(server_x25519_pk, server_x25519_sk) != HYBRID_NTOR_SUCCESS) {
        memset(state->kyber_shared_secret, 0, sizeof(state->kyber_shared_secret));
        return HYBRID_NTOR_ERROR;
    }

    if (x25519_key_exchange(state->x25519_shared_secret, server_x25519_sk, client_x25519_pk) != HYBRID_NTOR_SUCCESS) {
        memset(state->kyber_shared_secret, 0, sizeof(state->kyber_shared_secret));
        memset(server_x25519_sk, 0, sizeof(server_x25519_sk));
        return HYBRID_NTOR_ERROR;
    }

    // Clear server secret key (no longer needed)
    memset(server_x25519_sk, 0, sizeof(server_x25519_sk));

    // 3. Combine shared secrets
    if (combine_shared_secrets(state->hybrid_shared_secret,
                               state->kyber_shared_secret,
                               state->x25519_shared_secret) != HYBRID_NTOR_SUCCESS) {
        memset(state->kyber_shared_secret, 0, sizeof(state->kyber_shared_secret));
        memset(state->x25519_shared_secret, 0, sizeof(state->x25519_shared_secret));
        return HYBRID_NTOR_ERROR;
    }

    // 4. Build transcript and derive keys
    // Max transcript size: kyber_pk(800) + x25519_pk_c(32) + kyber_ct(768) + x25519_pk_s(32) + relay_id(20) = 1652
    uint8_t transcript[1652];
    size_t transcript_len;
    build_transcript(transcript, &transcript_len,
                     client_kyber_pk, client_x25519_pk,
                     kyber_ct, server_x25519_pk,
                     relay_identity);

    if (derive_keys(state->k_auth, state->k_enc,
                    state->hybrid_shared_secret, transcript, transcript_len) != HYBRID_NTOR_SUCCESS) {
        memset(state->hybrid_shared_secret, 0, sizeof(state->hybrid_shared_secret));
        return HYBRID_NTOR_ERROR;
    }

    // 5. Compute AUTH = HMAC(K_auth, transcript || "server")
    uint8_t auth_input[sizeof(transcript) + 32];
    memcpy(auth_input, transcript, transcript_len);
    memcpy(auth_input + transcript_len, HYBRID_NTOR_SERVER_AUTH, strlen(HYBRID_NTOR_SERVER_AUTH));

    uint8_t auth[HMAC_SHA256_OUTPUT_LENGTH];
    if (hmac_sha256(auth, state->k_auth, HYBRID_NTOR_KEY_AUTH_LEN,
                    auth_input, transcript_len + strlen(HYBRID_NTOR_SERVER_AUTH)) != CRYPTO_SUCCESS) {
        hybrid_ntor_server_state_cleanup(state);
        return HYBRID_NTOR_ERROR;
    }

    // 6. Build reply: kyber_ct || x25519_pk_server || AUTH
    pos = 0;
    memcpy(reply + pos, kyber_ct, KYBER_CIPHERTEXT_BYTES);
    pos += KYBER_CIPHERTEXT_BYTES;
    memcpy(reply + pos, server_x25519_pk, X25519_KEY_SIZE);
    pos += X25519_KEY_SIZE;
    memcpy(reply + pos, auth, HMAC_SHA256_OUTPUT_LENGTH);

    // Clear temporary data
    memset(transcript, 0, sizeof(transcript));
    memset(auth_input, 0, sizeof(auth_input));

    return HYBRID_NTOR_SUCCESS;
}

/**
 * Client: Process reply and complete handshake
 */
int hybrid_ntor_client_finish_handshake(hybrid_ntor_client_state *state,
                                        const uint8_t *reply) {
    if (!state || !reply) {
        return HYBRID_NTOR_ERROR;
    }

    // Parse reply
    uint8_t kyber_ct[KYBER_CIPHERTEXT_BYTES];
    uint8_t server_x25519_pk[X25519_KEY_SIZE];
    uint8_t received_auth[HMAC_SHA256_OUTPUT_LENGTH];

    size_t pos = 0;
    memcpy(kyber_ct, reply + pos, KYBER_CIPHERTEXT_BYTES);
    pos += KYBER_CIPHERTEXT_BYTES;
    memcpy(server_x25519_pk, reply + pos, X25519_KEY_SIZE);
    pos += X25519_KEY_SIZE;
    memcpy(received_auth, reply + pos, HMAC_SHA256_OUTPUT_LENGTH);

    // 1. Kyber decapsulation
    if (kyber_decapsulate(state->kyber_shared_secret, kyber_ct, state->kyber_secret_key) != KYBER_SUCCESS) {
        return HYBRID_NTOR_ERROR;
    }

    // 2. X25519 ECDH
    if (x25519_key_exchange(state->x25519_shared_secret,
                            state->x25519_secret_key,
                            server_x25519_pk) != HYBRID_NTOR_SUCCESS) {
        memset(state->kyber_shared_secret, 0, sizeof(state->kyber_shared_secret));
        return HYBRID_NTOR_ERROR;
    }

    // 3. Combine shared secrets
    if (combine_shared_secrets(state->hybrid_shared_secret,
                               state->kyber_shared_secret,
                               state->x25519_shared_secret) != HYBRID_NTOR_SUCCESS) {
        memset(state->kyber_shared_secret, 0, sizeof(state->kyber_shared_secret));
        memset(state->x25519_shared_secret, 0, sizeof(state->x25519_shared_secret));
        return HYBRID_NTOR_ERROR;
    }

    // 4. Build transcript and derive keys
    uint8_t transcript[1652];
    size_t transcript_len;
    build_transcript(transcript, &transcript_len,
                     state->kyber_public_key, state->x25519_public_key,
                     kyber_ct, server_x25519_pk,
                     state->relay_identity);

    if (derive_keys(state->k_auth, state->k_enc,
                    state->hybrid_shared_secret, transcript, transcript_len) != HYBRID_NTOR_SUCCESS) {
        memset(state->hybrid_shared_secret, 0, sizeof(state->hybrid_shared_secret));
        return HYBRID_NTOR_ERROR;
    }

    // 5. Verify AUTH
    uint8_t auth_input[sizeof(transcript) + 32];
    memcpy(auth_input, transcript, transcript_len);
    memcpy(auth_input + transcript_len, HYBRID_NTOR_SERVER_AUTH, strlen(HYBRID_NTOR_SERVER_AUTH));

    uint8_t computed_auth[HMAC_SHA256_OUTPUT_LENGTH];
    if (hmac_sha256(computed_auth, state->k_auth, HYBRID_NTOR_KEY_AUTH_LEN,
                    auth_input, transcript_len + strlen(HYBRID_NTOR_SERVER_AUTH)) != CRYPTO_SUCCESS) {
        hybrid_ntor_client_state_cleanup(state);
        return HYBRID_NTOR_ERROR;
    }

    // Constant-time comparison
    int auth_valid = 1;
    for (size_t i = 0; i < HMAC_SHA256_OUTPUT_LENGTH; i++) {
        if (computed_auth[i] != received_auth[i]) {
            auth_valid = 0;
        }
    }

    // Clear temporary data
    memset(transcript, 0, sizeof(transcript));
    memset(auth_input, 0, sizeof(auth_input));
    memset(computed_auth, 0, sizeof(computed_auth));

    if (!auth_valid) {
        hybrid_ntor_client_state_cleanup(state);
        return HYBRID_NTOR_AUTH_FAIL;
    }

    return HYBRID_NTOR_SUCCESS;
}

/**
 * Extract client encryption key
 */
int hybrid_ntor_client_get_key(uint8_t *key, const hybrid_ntor_client_state *state) {
    if (!key || !state) {
        return HYBRID_NTOR_ERROR;
    }
    memcpy(key, state->k_enc, HYBRID_NTOR_KEY_ENC_LEN);
    return HYBRID_NTOR_SUCCESS;
}

/**
 * Extract server encryption key
 */
int hybrid_ntor_server_get_key(uint8_t *key, const hybrid_ntor_server_state *state) {
    if (!key || !state) {
        return HYBRID_NTOR_ERROR;
    }
    memcpy(key, state->k_enc, HYBRID_NTOR_KEY_ENC_LEN);
    return HYBRID_NTOR_SUCCESS;
}

/**
 * Cleanup client state
 */
void hybrid_ntor_client_state_cleanup(hybrid_ntor_client_state *state) {
    if (state) {
        memset(state, 0, sizeof(hybrid_ntor_client_state));
    }
}

/**
 * Cleanup server state
 */
void hybrid_ntor_server_state_cleanup(hybrid_ntor_server_state *state) {
    if (state) {
        memset(state, 0, sizeof(hybrid_ntor_server_state));
    }
}
