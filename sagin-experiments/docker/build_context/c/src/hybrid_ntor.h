/**
 * @file hybrid_ntor.h
 * @brief Hybrid Ntor Handshake Protocol Interface
 *
 * Implements hybrid post-quantum key exchange combining Kyber-512 KEM
 * with X25519 ECDH for defense-in-depth security.
 *
 * This follows IETF recommendations for hybrid key exchange:
 * - Kyber-512 provides quantum resistance (NIST Level 1)
 * - X25519 provides classical security guarantee
 * - Combined shared secret ensures security even if one primitive fails
 *
 * Protocol Flow:
 * 1. Client: Generate Kyber keypair (pk_k, sk_k) and X25519 keypair (X, x)
 * 2. Client -> Server: onionskin (pk_k, X, relay_identity)
 * 3. Server: Generate X25519 keypair (Y, y)
 * 4. Server: Encapsulate with pk_k to get (ct, ss_k)
 * 5. Server: ECDH: ss_x = y * X
 * 6. Server: Combine: ss_hybrid = HKDF(ss_k || ss_x)
 * 7. Server: Derive keys and compute AUTH
 * 8. Server -> Client: reply (ct, Y, AUTH)
 * 9. Client: Decapsulate ct to get ss_k
 * 10. Client: ECDH: ss_x = x * Y
 * 11. Client: Combine and verify AUTH
 *
 * Reference: draft-ietf-tls-hybrid-design
 */

#ifndef HYBRID_NTOR_H
#define HYBRID_NTOR_H

#include <stdint.h>
#include <stddef.h>
#include "kyber_kem.h"
#include "crypto_utils.h"

// X25519 key sizes
#define X25519_KEY_SIZE      32
#define X25519_SHARED_SIZE   32

// Hybrid Ntor message sizes
#define HYBRID_NTOR_RELAY_ID_LENGTH   20  // Relay node identity length

// Onionskin: Kyber_pk (800) + X25519_pk (32) + relay_id (20) = 852 bytes
#define HYBRID_NTOR_ONIONSKIN_LEN     (KYBER_PUBLIC_KEY_BYTES + X25519_KEY_SIZE + HYBRID_NTOR_RELAY_ID_LENGTH)

// Reply: Kyber_ct (768) + X25519_pk (32) + AUTH (32) = 832 bytes
#define HYBRID_NTOR_REPLY_LEN         (KYBER_CIPHERTEXT_BYTES + X25519_KEY_SIZE + HMAC_SHA256_OUTPUT_LENGTH)

// Derived key lengths (same as pq_ntor for compatibility)
#define HYBRID_NTOR_KEY_AUTH_LEN      32  // Authentication key
#define HYBRID_NTOR_KEY_ENC_LEN       80  // Encryption key: Kf(32) + Kb(32) + IVf(8) + IVb(8)
#define HYBRID_NTOR_KEY_MATERIAL_LEN  (HYBRID_NTOR_KEY_AUTH_LEN + HYBRID_NTOR_KEY_ENC_LEN)

// Combined shared secret size
#define HYBRID_SHARED_SECRET_LEN      32

// Return values
#define HYBRID_NTOR_SUCCESS    0
#define HYBRID_NTOR_ERROR     -1
#define HYBRID_NTOR_AUTH_FAIL -2  // Authentication failed

// Protocol context strings
#define HYBRID_NTOR_COMBINE_INFO   "hybrid-ntor-combine"
#define HYBRID_NTOR_KEYS_INFO      "hybrid-ntor-keys"
#define HYBRID_NTOR_SERVER_AUTH    "server"

/**
 * @brief Client state structure for hybrid handshake
 */
typedef struct {
    // Kyber-512 keys
    uint8_t kyber_public_key[KYBER_PUBLIC_KEY_BYTES];
    uint8_t kyber_secret_key[KYBER_SECRET_KEY_BYTES];
    uint8_t kyber_shared_secret[KYBER_SHARED_SECRET_BYTES];

    // X25519 keys
    uint8_t x25519_public_key[X25519_KEY_SIZE];
    uint8_t x25519_secret_key[X25519_KEY_SIZE];
    uint8_t x25519_shared_secret[X25519_SHARED_SIZE];

    // Combined hybrid shared secret
    uint8_t hybrid_shared_secret[HYBRID_SHARED_SECRET_LEN];

    // Relay identity
    uint8_t relay_identity[HYBRID_NTOR_RELAY_ID_LENGTH];

    // Derived session keys
    uint8_t k_auth[HYBRID_NTOR_KEY_AUTH_LEN];
    uint8_t k_enc[HYBRID_NTOR_KEY_ENC_LEN];
} hybrid_ntor_client_state;

/**
 * @brief Server state structure for hybrid handshake
 */
typedef struct {
    // Kyber-512 shared secret (from encapsulation)
    uint8_t kyber_shared_secret[KYBER_SHARED_SECRET_BYTES];

    // X25519 shared secret (from ECDH)
    uint8_t x25519_shared_secret[X25519_SHARED_SIZE];

    // Combined hybrid shared secret
    uint8_t hybrid_shared_secret[HYBRID_SHARED_SECRET_LEN];

    // Derived session keys
    uint8_t k_auth[HYBRID_NTOR_KEY_AUTH_LEN];
    uint8_t k_enc[HYBRID_NTOR_KEY_ENC_LEN];
} hybrid_ntor_server_state;

/**
 * @brief Client: Create onionskin message
 *
 * Generates both Kyber and X25519 keypairs, constructs onionskin message
 *
 * @param state Client state (output)
 * @param onionskin Output: onionskin message (HYBRID_NTOR_ONIONSKIN_LEN bytes)
 * @param relay_identity Relay node identity (HYBRID_NTOR_RELAY_ID_LENGTH bytes)
 * @return HYBRID_NTOR_SUCCESS on success, HYBRID_NTOR_ERROR on failure
 */
int hybrid_ntor_client_create_onionskin(hybrid_ntor_client_state *state,
                                        uint8_t *onionskin,
                                        const uint8_t *relay_identity);

/**
 * @brief Server: Process onionskin and create reply
 *
 * Receives onionskin, performs Kyber encapsulation and X25519 ECDH,
 * combines shared secrets, derives session keys, creates reply
 *
 * @param state Server state (output)
 * @param reply Output: reply message (HYBRID_NTOR_REPLY_LEN bytes)
 * @param onionskin Input: onionskin message (HYBRID_NTOR_ONIONSKIN_LEN bytes)
 * @param relay_identity This node's identity (HYBRID_NTOR_RELAY_ID_LENGTH bytes)
 * @return HYBRID_NTOR_SUCCESS on success, HYBRID_NTOR_ERROR on failure
 */
int hybrid_ntor_server_create_reply(hybrid_ntor_server_state *state,
                                    uint8_t *reply,
                                    const uint8_t *onionskin,
                                    const uint8_t *relay_identity);

/**
 * @brief Client: Process reply and complete handshake
 *
 * Receives reply, performs Kyber decapsulation and X25519 ECDH,
 * combines shared secrets, derives session keys, verifies AUTH
 *
 * @param state Client state (input/output)
 * @param reply Input: reply message (HYBRID_NTOR_REPLY_LEN bytes)
 * @return HYBRID_NTOR_SUCCESS on success, HYBRID_NTOR_AUTH_FAIL on auth failure, HYBRID_NTOR_ERROR on other error
 */
int hybrid_ntor_client_finish_handshake(hybrid_ntor_client_state *state,
                                        const uint8_t *reply);

/**
 * @brief Extract encryption key from client state
 *
 * @param key Output: encryption key (HYBRID_NTOR_KEY_ENC_LEN bytes)
 * @param state Client state
 * @return HYBRID_NTOR_SUCCESS on success, HYBRID_NTOR_ERROR on failure
 */
int hybrid_ntor_client_get_key(uint8_t *key, const hybrid_ntor_client_state *state);

/**
 * @brief Extract encryption key from server state
 *
 * @param key Output: encryption key (HYBRID_NTOR_KEY_ENC_LEN bytes)
 * @param state Server state
 * @return HYBRID_NTOR_SUCCESS on success, HYBRID_NTOR_ERROR on failure
 */
int hybrid_ntor_server_get_key(uint8_t *key, const hybrid_ntor_server_state *state);

/**
 * @brief Cleanup client state (clear sensitive data)
 *
 * @param state Client state to cleanup
 */
void hybrid_ntor_client_state_cleanup(hybrid_ntor_client_state *state);

/**
 * @brief Cleanup server state (clear sensitive data)
 *
 * @param state Server state to cleanup
 */
void hybrid_ntor_server_state_cleanup(hybrid_ntor_server_state *state);

#endif // HYBRID_NTOR_H
