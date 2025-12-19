/**
 * @file classic_ntor.c
 * @brief Classic Ntor 握手协议实现
 *
 * 使用 OpenSSL 的 X25519 实现经典 Ntor 握手
 */

#include "classic_ntor.h"
#include <string.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/core_names.h>

/**
 * @brief 生成 X25519 密钥对
 */
static int generate_x25519_keypair(uint8_t *public_key, uint8_t *secret_key) {
    EVP_PKEY *pkey = NULL;
    EVP_PKEY_CTX *pctx = NULL;
    size_t pubkey_len = X25519_KEY_SIZE;
    size_t privkey_len = X25519_KEY_SIZE;
    int ret = CLASSIC_NTOR_ERROR;

    // 创建密钥生成上下文
    pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
    if (!pctx) goto cleanup;

    // 初始化密钥生成
    if (EVP_PKEY_keygen_init(pctx) <= 0) goto cleanup;

    // 生成密钥
    if (EVP_PKEY_keygen(pctx, &pkey) <= 0) goto cleanup;

    // 提取公钥
    if (EVP_PKEY_get_raw_public_key(pkey, public_key, &pubkey_len) <= 0) goto cleanup;
    if (pubkey_len != X25519_KEY_SIZE) goto cleanup;

    // 提取私钥
    if (EVP_PKEY_get_raw_private_key(pkey, secret_key, &privkey_len) <= 0) goto cleanup;
    if (privkey_len != X25519_KEY_SIZE) goto cleanup;

    ret = CLASSIC_NTOR_SUCCESS;

cleanup:
    if (pkey) EVP_PKEY_free(pkey);
    if (pctx) EVP_PKEY_CTX_free(pctx);
    return ret;
}

/**
 * @brief 执行 X25519 密钥交换
 */
static int x25519_key_exchange(uint8_t *shared_secret,
                               const uint8_t *my_secret_key,
                               const uint8_t *peer_public_key) {
    EVP_PKEY *my_pkey = NULL;
    EVP_PKEY *peer_pkey = NULL;
    EVP_PKEY_CTX *ctx = NULL;
    size_t secret_len = X25519_SHARED_SIZE;
    int ret = CLASSIC_NTOR_ERROR;

    // 从原始私钥创建自己的密钥对象
    my_pkey = EVP_PKEY_new_raw_private_key(EVP_PKEY_X25519, NULL,
                                            my_secret_key, X25519_KEY_SIZE);
    if (!my_pkey) goto cleanup;

    // 从原始公钥创建对方的密钥对象
    peer_pkey = EVP_PKEY_new_raw_public_key(EVP_PKEY_X25519, NULL,
                                             peer_public_key, X25519_KEY_SIZE);
    if (!peer_pkey) goto cleanup;

    // 创建密钥派生上下文
    ctx = EVP_PKEY_CTX_new(my_pkey, NULL);
    if (!ctx) goto cleanup;

    // 初始化密钥派生
    if (EVP_PKEY_derive_init(ctx) <= 0) goto cleanup;

    // 设置对方的公钥
    if (EVP_PKEY_derive_set_peer(ctx, peer_pkey) <= 0) goto cleanup;

    // 派生共享密钥
    if (EVP_PKEY_derive(ctx, shared_secret, &secret_len) <= 0) goto cleanup;
    if (secret_len != X25519_SHARED_SIZE) goto cleanup;

    ret = CLASSIC_NTOR_SUCCESS;

cleanup:
    if (ctx) EVP_PKEY_CTX_free(ctx);
    if (peer_pkey) EVP_PKEY_free(peer_pkey);
    if (my_pkey) EVP_PKEY_free(my_pkey);
    return ret;
}

/**
 * @brief 派生会话密钥
 */
static int derive_keys(uint8_t *k_auth, uint8_t *k_enc,
                       const uint8_t *shared_secret,
                       const uint8_t *transcript, size_t transcript_len) {
    uint8_t key_material[CLASSIC_NTOR_KEY_MATERIAL_LEN];

    // 使用 HKDF 派生密钥
    int ret = hkdf_sha256(key_material, CLASSIC_NTOR_KEY_MATERIAL_LEN,
                          shared_secret, X25519_SHARED_SIZE,
                          transcript, transcript_len,
                          (const uint8_t *)CLASSIC_NTOR_INFO_STRING,
                          strlen(CLASSIC_NTOR_INFO_STRING));

    if (ret != 0) {
        return CLASSIC_NTOR_ERROR;
    }

    // 分离认证密钥和加密密钥
    memcpy(k_auth, key_material, CLASSIC_NTOR_KEY_AUTH_LEN);
    memcpy(k_enc, key_material + CLASSIC_NTOR_KEY_AUTH_LEN, CLASSIC_NTOR_KEY_ENC_LEN);

    // 清除临时密钥材料
    explicit_bzero(key_material, sizeof(key_material));

    return CLASSIC_NTOR_SUCCESS;
}

/**
 * @brief 客户端：创建 onionskin
 */
int classic_ntor_client_create_onionskin(classic_ntor_client_state *state,
                                         uint8_t *onionskin,
                                         const uint8_t *relay_identity) {
    if (!state || !onionskin || !relay_identity) {
        return CLASSIC_NTOR_ERROR;
    }

    // 生成临时密钥对
    if (generate_x25519_keypair(state->client_public_key,
                                 state->client_secret_key) != CLASSIC_NTOR_SUCCESS) {
        return CLASSIC_NTOR_ERROR;
    }

    // 保存 relay identity
    memcpy(state->relay_identity, relay_identity, CLASSIC_NTOR_RELAY_ID_LENGTH);

    // 构建 onionskin: client_public_key || relay_identity
    memcpy(onionskin, state->client_public_key, X25519_KEY_SIZE);
    memcpy(onionskin + X25519_KEY_SIZE, relay_identity, CLASSIC_NTOR_RELAY_ID_LENGTH);

    return CLASSIC_NTOR_SUCCESS;
}

/**
 * @brief 服务端：处理 onionskin 并创建 reply
 */
int classic_ntor_server_create_reply(classic_ntor_server_state *state,
                                     uint8_t *reply,
                                     const uint8_t *onionskin,
                                     const uint8_t *relay_identity) {
    if (!state || !reply || !onionskin || !relay_identity) {
        return CLASSIC_NTOR_ERROR;
    }

    uint8_t client_public_key[X25519_KEY_SIZE];
    uint8_t server_public_key[X25519_KEY_SIZE];
    uint8_t server_secret_key[X25519_KEY_SIZE];
    uint8_t transcript[X25519_KEY_SIZE + CLASSIC_NTOR_RELAY_ID_LENGTH + X25519_KEY_SIZE];
    uint8_t auth_input[sizeof(transcript) + strlen(CLASSIC_NTOR_SERVER_AUTH_STRING)];
    uint8_t auth_tag[HMAC_SHA256_OUTPUT_LENGTH];

    // 解析 onionskin
    memcpy(client_public_key, onionskin, X25519_KEY_SIZE);

    // 生成服务器临时密钥对
    if (generate_x25519_keypair(server_public_key, server_secret_key) != CLASSIC_NTOR_SUCCESS) {
        explicit_bzero(server_secret_key, sizeof(server_secret_key));
        return CLASSIC_NTOR_ERROR;
    }

    // 执行 ECDH 密钥交换
    if (x25519_key_exchange(state->shared_secret, server_secret_key,
                            client_public_key) != CLASSIC_NTOR_SUCCESS) {
        explicit_bzero(server_secret_key, sizeof(server_secret_key));
        return CLASSIC_NTOR_ERROR;
    }

    // 清除服务器私钥（不再需要）
    explicit_bzero(server_secret_key, sizeof(server_secret_key));

    // 构建 transcript: client_pk || relay_id || server_pk
    memcpy(transcript, client_public_key, X25519_KEY_SIZE);
    memcpy(transcript + X25519_KEY_SIZE, relay_identity, CLASSIC_NTOR_RELAY_ID_LENGTH);
    memcpy(transcript + X25519_KEY_SIZE + CLASSIC_NTOR_RELAY_ID_LENGTH,
           server_public_key, X25519_KEY_SIZE);

    // 派生密钥
    if (derive_keys(state->k_auth, state->k_enc, state->shared_secret,
                    transcript, sizeof(transcript)) != CLASSIC_NTOR_SUCCESS) {
        return CLASSIC_NTOR_ERROR;
    }

    // 计算认证标签: HMAC(k_auth, transcript || "server")
    memcpy(auth_input, transcript, sizeof(transcript));
    memcpy(auth_input + sizeof(transcript), CLASSIC_NTOR_SERVER_AUTH_STRING,
           strlen(CLASSIC_NTOR_SERVER_AUTH_STRING));

    if (hmac_sha256(auth_tag, state->k_auth, CLASSIC_NTOR_KEY_AUTH_LEN,
                    auth_input, sizeof(auth_input)) != 0) {
        return CLASSIC_NTOR_ERROR;
    }

    // 构建 reply: server_public_key || auth_tag
    memcpy(reply, server_public_key, X25519_KEY_SIZE);
    memcpy(reply + X25519_KEY_SIZE, auth_tag, HMAC_SHA256_OUTPUT_LENGTH);

    return CLASSIC_NTOR_SUCCESS;
}

/**
 * @brief 客户端：处理 reply 并完成握手
 */
int classic_ntor_client_finish_handshake(classic_ntor_client_state *state,
                                         const uint8_t *reply) {
    if (!state || !reply) {
        return CLASSIC_NTOR_ERROR;
    }

    uint8_t server_public_key[X25519_KEY_SIZE];
    uint8_t received_auth_tag[HMAC_SHA256_OUTPUT_LENGTH];
    uint8_t transcript[X25519_KEY_SIZE + CLASSIC_NTOR_RELAY_ID_LENGTH + X25519_KEY_SIZE];
    uint8_t auth_input[sizeof(transcript) + strlen(CLASSIC_NTOR_SERVER_AUTH_STRING)];
    uint8_t computed_auth_tag[HMAC_SHA256_OUTPUT_LENGTH];

    // 解析 reply
    memcpy(server_public_key, reply, X25519_KEY_SIZE);
    memcpy(received_auth_tag, reply + X25519_KEY_SIZE, HMAC_SHA256_OUTPUT_LENGTH);

    // 执行 ECDH 密钥交换
    if (x25519_key_exchange(state->shared_secret, state->client_secret_key,
                            server_public_key) != CLASSIC_NTOR_SUCCESS) {
        return CLASSIC_NTOR_ERROR;
    }

    // 构建 transcript: client_pk || relay_id || server_pk
    memcpy(transcript, state->client_public_key, X25519_KEY_SIZE);
    memcpy(transcript + X25519_KEY_SIZE, state->relay_identity, CLASSIC_NTOR_RELAY_ID_LENGTH);
    memcpy(transcript + X25519_KEY_SIZE + CLASSIC_NTOR_RELAY_ID_LENGTH,
           server_public_key, X25519_KEY_SIZE);

    // 派生密钥
    if (derive_keys(state->k_auth, state->k_enc, state->shared_secret,
                    transcript, sizeof(transcript)) != CLASSIC_NTOR_SUCCESS) {
        return CLASSIC_NTOR_ERROR;
    }

    // 计算认证标签: HMAC(k_auth, transcript || "server")
    memcpy(auth_input, transcript, sizeof(transcript));
    memcpy(auth_input + sizeof(transcript), CLASSIC_NTOR_SERVER_AUTH_STRING,
           strlen(CLASSIC_NTOR_SERVER_AUTH_STRING));

    if (hmac_sha256(computed_auth_tag, state->k_auth, CLASSIC_NTOR_KEY_AUTH_LEN,
                    auth_input, sizeof(auth_input)) != 0) {
        return CLASSIC_NTOR_ERROR;
    }

    // 验证认证标签（常数时间比较）
    int auth_valid = 1;
    for (size_t i = 0; i < HMAC_SHA256_OUTPUT_LENGTH; i++) {
        if (received_auth_tag[i] != computed_auth_tag[i]) {
            auth_valid = 0;
        }
    }

    if (!auth_valid) {
        // 清除密钥材料
        classic_ntor_client_state_cleanup(state);
        return CLASSIC_NTOR_AUTH_FAIL;
    }

    return CLASSIC_NTOR_SUCCESS;
}

/**
 * @brief 从客户端状态提取加密密钥
 */
int classic_ntor_client_get_key(uint8_t *key, const classic_ntor_client_state *state) {
    if (!key || !state) {
        return CLASSIC_NTOR_ERROR;
    }
    memcpy(key, state->k_enc, CLASSIC_NTOR_KEY_ENC_LEN);
    return CLASSIC_NTOR_SUCCESS;
}

/**
 * @brief 从服务端状态提取加密密钥
 */
int classic_ntor_server_get_key(uint8_t *key, const classic_ntor_server_state *state) {
    if (!key || !state) {
        return CLASSIC_NTOR_ERROR;
    }
    memcpy(key, state->k_enc, CLASSIC_NTOR_KEY_ENC_LEN);
    return CLASSIC_NTOR_SUCCESS;
}

/**
 * @brief 清理客户端状态
 */
void classic_ntor_client_state_cleanup(classic_ntor_client_state *state) {
    if (state) {
        explicit_bzero(state, sizeof(classic_ntor_client_state));
    }
}

/**
 * @brief 清理服务端状态
 */
void classic_ntor_server_state_cleanup(classic_ntor_server_state *state) {
    if (state) {
        explicit_bzero(state, sizeof(classic_ntor_server_state));
    }
}
