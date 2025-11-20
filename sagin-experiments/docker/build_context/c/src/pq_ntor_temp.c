/**
 * @file pq_ntor.c
 * @brief PQ-Ntor 握手协议实现
 */

#include "pq_ntor.h"
#include <string.h>
#include <stdio.h>

/**
 * 辅助函数：构建握手转录 (transcript)
 * transcript = pk_client || ct || relay_identity
 */
static void build_transcript(uint8_t *transcript, size_t *transcript_len,
                            const uint8_t *pk_client,
                            const uint8_t *ciphertext,
                            const uint8_t *relay_identity) {
    size_t pos = 0;

    // pk_client
    memcpy(transcript + pos, pk_client, KYBER_PUBLIC_KEY_BYTES);
    pos += KYBER_PUBLIC_KEY_BYTES;

    // ciphertext (服务端创建 reply 时可能为 NULL)
    if (ciphertext) {
        memcpy(transcript + pos, ciphertext, KYBER_CIPHERTEXT_BYTES);
        pos += KYBER_CIPHERTEXT_BYTES;
    }

    // relay_identity
    memcpy(transcript + pos, relay_identity, PQ_NTOR_RELAY_ID_LENGTH);
    pos += PQ_NTOR_RELAY_ID_LENGTH;

    *transcript_len = pos;
}

/**
 * 辅助函数：派生会话密钥
 * (K_auth || K_enc) = HKDF(K_kem, NULL, transcript, "pq-ntor-keys")
 */
static int derive_keys(uint8_t *k_auth, uint8_t *k_enc,
                      const uint8_t *k_kem,
                      const uint8_t *transcript, size_t transcript_len) {
    uint8_t key_material[PQ_NTOR_KEY_MATERIAL_LEN];

    // HKDF: 使用 transcript 作为 info
    int ret = hkdf_sha256(key_material, sizeof(key_material),
                         NULL, 0,  // 不使用 salt
                         k_kem, KYBER_SHARED_SECRET_BYTES,
                         transcript, transcript_len);

    if (ret != CRYPTO_SUCCESS) {
        return PQ_NTOR_ERROR;
    }

    // 分离密钥
    memcpy(k_auth, key_material, PQ_NTOR_KEY_AUTH_LEN);
    memcpy(k_enc, key_material + PQ_NTOR_KEY_AUTH_LEN, PQ_NTOR_KEY_ENC_LEN);

    // 清理敏感数据
    memset(key_material, 0, sizeof(key_material));

    return PQ_NTOR_SUCCESS;
}

/**
 * 客户端：创建 onionskin
 */
int pq_ntor_client_create_onionskin(pq_ntor_client_state *state,
                                    uint8_t *onionskin,
                                    const uint8_t *relay_identity) {
    if (!state || !onionskin || !relay_identity) {
        return PQ_NTOR_ERROR;
    }

    // 生成临时密钥对
    if (kyber_keypair(state->client_public_key, state->client_secret_key) != KYBER_SUCCESS) {
        return PQ_NTOR_ERROR;
    }

    // 保存 relay_identity
    memcpy(state->relay_identity, relay_identity, PQ_NTOR_RELAY_ID_LENGTH);

    // 构建 onionskin: pk_client || relay_identity
    memcpy(onionskin, state->client_public_key, KYBER_PUBLIC_KEY_BYTES);
    memcpy(onionskin + KYBER_PUBLIC_KEY_BYTES, relay_identity, PQ_NTOR_RELAY_ID_LENGTH);

    return PQ_NTOR_SUCCESS;
}

/**
 * 服务端：处理 onionskin 并创建 reply
 */
int pq_ntor_server_create_reply(pq_ntor_server_state *state,
                                uint8_t *reply,
                                const uint8_t *onionskin,
                                const uint8_t *relay_identity) {
    if (!state || !reply || !onionskin || !relay_identity) {
        return PQ_NTOR_ERROR;
    }

    // 解析 onionskin
    uint8_t pk_client[KYBER_PUBLIC_KEY_BYTES];
    uint8_t received_relay_id[PQ_NTOR_RELAY_ID_LENGTH];

    memcpy(pk_client, onionskin, KYBER_PUBLIC_KEY_BYTES);
    memcpy(received_relay_id, onionskin + KYBER_PUBLIC_KEY_BYTES, PQ_NTOR_RELAY_ID_LENGTH);

    // 验证 relay_identity（应该匹配本节点）
    if (memcmp(received_relay_id, relay_identity, PQ_NTOR_RELAY_ID_LENGTH) != 0) {
        fprintf(stderr, "Error: relay_identity mismatch\n");
        return PQ_NTOR_ERROR;
    }

    // 使用客户端公钥进行封装
    uint8_t ciphertext[KYBER_CIPHERTEXT_BYTES];
    if (kyber_encapsulate(ciphertext, state->k_kem, pk_client) != KYBER_SUCCESS) {
        return PQ_NTOR_ERROR;
    }

    // 构建 transcript
    uint8_t transcript[KYBER_PUBLIC_KEY_BYTES + KYBER_CIPHERTEXT_BYTES + PQ_NTOR_RELAY_ID_LENGTH];
    size_t transcript_len;
    build_transcript(transcript, &transcript_len, pk_client, ciphertext, relay_identity);

    // 派生密钥
    if (derive_keys(state->k_auth, state->k_enc, state->k_kem, transcript, transcript_len) != PQ_NTOR_SUCCESS) {
        memset(state->k_kem, 0, sizeof(state->k_kem));
        return PQ_NTOR_ERROR;
    }

    // 计算 AUTH = HMAC(K_auth, transcript || "server")
    uint8_t auth_input[sizeof(transcript) + 32];  // transcript + "server"
    memcpy(auth_input, transcript, transcript_len);
    memcpy(auth_input + transcript_len, PQ_NTOR_SERVER_AUTH_STRING, strlen(PQ_NTOR_SERVER_AUTH_STRING));

    uint8_t auth[HMAC_SHA256_OUTPUT_LENGTH];
    if (hmac_sha256(auth, state->k_auth, PQ_NTOR_KEY_AUTH_LEN,
                   auth_input, transcript_len + strlen(PQ_NTOR_SERVER_AUTH_STRING)) != CRYPTO_SUCCESS) {
        memset(state->k_kem, 0, sizeof(state->k_kem));
        memset(state->k_auth, 0, sizeof(state->k_auth));
        memset(state->k_enc, 0, sizeof(state->k_enc));
        return PQ_NTOR_ERROR;
    }

    // 构建 reply: ciphertext || AUTH
    memcpy(reply, ciphertext, KYBER_CIPHERTEXT_BYTES);
    memcpy(reply + KYBER_CIPHERTEXT_BYTES, auth, HMAC_SHA256_OUTPUT_LENGTH);

    // 清理临时数据
    memset(transcript, 0, sizeof(transcript));
    memset(auth_input, 0, sizeof(auth_input));

    return PQ_NTOR_SUCCESS;
}

/**
 * 客户端：处理 reply 并完成握手
 */
int pq_ntor_client_finish_handshake(pq_ntor_client_state *state,
                                    const uint8_t *reply) {
    if (!state || !reply) {
        return PQ_NTOR_ERROR;
    }

    // 解析 reply
    uint8_t ciphertext[KYBER_CIPHERTEXT_BYTES];
    uint8_t received_auth[HMAC_SHA256_OUTPUT_LENGTH];

    memcpy(ciphertext, reply, KYBER_CIPHERTEXT_BYTES);
    memcpy(received_auth, reply + KYBER_CIPHERTEXT_BYTES, HMAC_SHA256_OUTPUT_LENGTH);

    // 解封装恢复共享密钥
    if (kyber_decapsulate(state->k_kem, ciphertext, state->client_secret_key) != KYBER_SUCCESS) {
        return PQ_NTOR_ERROR;
    }

    // 构建 transcript
    uint8_t transcript[KYBER_PUBLIC_KEY_BYTES + KYBER_CIPHERTEXT_BYTES + PQ_NTOR_RELAY_ID_LENGTH];
    size_t transcript_len;
    build_transcript(transcript, &transcript_len,
                    state->client_public_key, ciphertext, state->relay_identity);

    // 派生密钥
    if (derive_keys(state->k_auth, state->k_enc, state->k_kem, transcript, transcript_len) != PQ_NTOR_SUCCESS) {
        memset(state->k_kem, 0, sizeof(state->k_kem));
        return PQ_NTOR_ERROR;
    }

    // 验证 AUTH
    uint8_t auth_input[sizeof(transcript) + 32];
    memcpy(auth_input, transcript, transcript_len);
    memcpy(auth_input + transcript_len, PQ_NTOR_SERVER_AUTH_STRING, strlen(PQ_NTOR_SERVER_AUTH_STRING));

    uint8_t computed_auth[HMAC_SHA256_OUTPUT_LENGTH];
    if (hmac_sha256(computed_auth, state->k_auth, PQ_NTOR_KEY_AUTH_LEN,
                   auth_input, transcript_len + strlen(PQ_NTOR_SERVER_AUTH_STRING)) != CRYPTO_SUCCESS) {
        memset(state->k_kem, 0, sizeof(state->k_kem));
        memset(state->k_auth, 0, sizeof(state->k_auth));
        memset(state->k_enc, 0, sizeof(state->k_enc));
        return PQ_NTOR_ERROR;
    }

    // 常量时间比较 AUTH
    int auth_valid = 1;
    for (size_t i = 0; i < HMAC_SHA256_OUTPUT_LENGTH; i++) {
        if (computed_auth[i] != received_auth[i]) {
            auth_valid = 0;
        }
    }

    // 清理临时数据
    memset(transcript, 0, sizeof(transcript));
    memset(auth_input, 0, sizeof(auth_input));
    memset(computed_auth, 0, sizeof(computed_auth));

    if (!auth_valid) {
        memset(state->k_kem, 0, sizeof(state->k_kem));
        memset(state->k_auth, 0, sizeof(state->k_auth));
        memset(state->k_enc, 0, sizeof(state->k_enc));
        return PQ_NTOR_AUTH_FAIL;
    }

    return PQ_NTOR_SUCCESS;
}

/**
 * 提取客户端加密密钥
 */
int pq_ntor_client_get_key(uint8_t *key, const pq_ntor_client_state *state) {
    if (!key || !state) {
        return PQ_NTOR_ERROR;
    }
    memcpy(key, state->k_enc, PQ_NTOR_KEY_ENC_LEN);
    return PQ_NTOR_SUCCESS;
}

/**
 * 提取服务端加密密钥
 */
int pq_ntor_server_get_key(uint8_t *key, const pq_ntor_server_state *state) {
    if (!key || !state) {
        return PQ_NTOR_ERROR;
    }
    memcpy(key, state->k_enc, PQ_NTOR_KEY_ENC_LEN);
    return PQ_NTOR_SUCCESS;
}

/**
 * 清理客户端状态
 */
void pq_ntor_client_state_cleanup(pq_ntor_client_state *state) {
    if (state) {
        memset(state, 0, sizeof(pq_ntor_client_state));
    }
}

/**
 * 清理服务端状态
 */
void pq_ntor_server_state_cleanup(pq_ntor_server_state *state) {
    if (state) {
        memset(state, 0, sizeof(pq_ntor_server_state));
    }
}
