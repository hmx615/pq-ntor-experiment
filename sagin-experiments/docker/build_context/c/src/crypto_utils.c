/**
 * @file crypto_utils.c
 * @brief 加密工具函数实现
 *
 * 基于 OpenSSL 实现 HMAC-SHA256 和 HKDF-SHA256
 */

#include "crypto_utils.h"
#include <string.h>
#include <openssl/hmac.h>
#include <openssl/sha.h>
#include <openssl/evp.h>

/**
 * SHA256 哈希
 */
int sha256_hash(uint8_t *output, const uint8_t *data, size_t data_len) {
    if (!output || !data) {
        return CRYPTO_ERROR;
    }

    SHA256_CTX ctx;
    if (!SHA256_Init(&ctx)) {
        return CRYPTO_ERROR;
    }
    if (!SHA256_Update(&ctx, data, data_len)) {
        return CRYPTO_ERROR;
    }
    if (!SHA256_Final(output, &ctx)) {
        return CRYPTO_ERROR;
    }

    return CRYPTO_SUCCESS;
}

/**
 * HMAC-SHA256
 */
int hmac_sha256(uint8_t *output,
                const uint8_t *key, size_t key_len,
                const uint8_t *data, size_t data_len) {
    if (!output || !key || !data) {
        return CRYPTO_ERROR;
    }

    unsigned int len = HMAC_SHA256_OUTPUT_LENGTH;

    // 使用 OpenSSL 3.0+ 兼容的 API
    uint8_t *result = HMAC(EVP_sha256(), key, key_len, data, data_len, output, &len);

    if (!result || len != HMAC_SHA256_OUTPUT_LENGTH) {
        return CRYPTO_ERROR;
    }

    return CRYPTO_SUCCESS;
}

/**
 * HKDF-Extract
 * PRK = HMAC-Hash(salt, IKM)
 */
int hkdf_extract(uint8_t *prk,
                 const uint8_t *salt, size_t salt_len,
                 const uint8_t *ikm, size_t ikm_len) {
    if (!prk || !ikm) {
        return CRYPTO_ERROR;
    }

    // 如果没有提供 salt，使用全零的 hash 长度字节串
    uint8_t default_salt[SHA256_DIGEST_LENGTH] = {0};
    const uint8_t *actual_salt = salt ? salt : default_salt;
    size_t actual_salt_len = salt ? salt_len : SHA256_DIGEST_LENGTH;

    // PRK = HMAC-Hash(salt, IKM)
    return hmac_sha256(prk, actual_salt, actual_salt_len, ikm, ikm_len);
}

/**
 * HKDF-Expand
 * OKM = HKDF-Expand(PRK, info, L)
 */
int hkdf_expand(uint8_t *okm, size_t okm_len,
                const uint8_t *prk,
                const uint8_t *info, size_t info_len) {
    if (!okm || !prk || okm_len == 0) {
        return CRYPTO_ERROR;
    }

    // RFC 5869: L <= 255 * HashLen
    if (okm_len > 255 * SHA256_DIGEST_LENGTH) {
        return CRYPTO_ERROR;
    }

    uint8_t t[SHA256_DIGEST_LENGTH];
    uint8_t t_prev[SHA256_DIGEST_LENGTH];
    size_t t_len = 0;
    size_t okm_pos = 0;
    uint8_t counter = 1;

    // T(0) = empty string
    // T(i) = HMAC-Hash(PRK, T(i-1) | info | i)
    while (okm_pos < okm_len) {
        // 构建 HMAC 输入: T(i-1) | info | counter
        uint8_t hmac_input[SHA256_DIGEST_LENGTH + 1024 + 1]; // 假设 info 最大 1024 字节
        size_t hmac_input_len = 0;

        if (counter > 1) {
            memcpy(hmac_input, t_prev, t_len);
            hmac_input_len += t_len;
        }

        if (info && info_len > 0) {
            if (info_len > 1024) {
                return CRYPTO_ERROR; // info 太长
            }
            memcpy(hmac_input + hmac_input_len, info, info_len);
            hmac_input_len += info_len;
        }

        hmac_input[hmac_input_len++] = counter;

        // T(i) = HMAC-Hash(PRK, T(i-1) | info | i)
        if (hmac_sha256(t, prk, SHA256_DIGEST_LENGTH, hmac_input, hmac_input_len) != CRYPTO_SUCCESS) {
            return CRYPTO_ERROR;
        }

        // 复制到输出
        size_t to_copy = okm_len - okm_pos;
        if (to_copy > SHA256_DIGEST_LENGTH) {
            to_copy = SHA256_DIGEST_LENGTH;
        }
        memcpy(okm + okm_pos, t, to_copy);
        okm_pos += to_copy;

        // 保存当前 T 为下一轮的 T(i-1)
        memcpy(t_prev, t, SHA256_DIGEST_LENGTH);
        t_len = SHA256_DIGEST_LENGTH;

        counter++;
    }

    // 清理敏感数据
    memset(t, 0, sizeof(t));
    memset(t_prev, 0, sizeof(t_prev));

    return CRYPTO_SUCCESS;
}

/**
 * HKDF 完整流程
 */
int hkdf_sha256(uint8_t *okm, size_t okm_len,
                const uint8_t *salt, size_t salt_len,
                const uint8_t *ikm, size_t ikm_len,
                const uint8_t *info, size_t info_len) {
    if (!okm || !ikm) {
        return CRYPTO_ERROR;
    }

    // Step 1: Extract
    uint8_t prk[SHA256_DIGEST_LENGTH];
    if (hkdf_extract(prk, salt, salt_len, ikm, ikm_len) != CRYPTO_SUCCESS) {
        memset(prk, 0, sizeof(prk));
        return CRYPTO_ERROR;
    }

    // Step 2: Expand
    int result = hkdf_expand(okm, okm_len, prk, info, info_len);

    // 清理敏感数据
    memset(prk, 0, sizeof(prk));

    return result;
}
