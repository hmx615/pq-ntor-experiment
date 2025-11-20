/**
 * @file crypto_utils.h
 * @brief 加密工具函数（HMAC-SHA256, HKDF-SHA256）
 *
 * 为 PQ-Ntor 协议提供密钥派生和消息认证功能
 */

#ifndef CRYPTO_UTILS_H
#define CRYPTO_UTILS_H

#include <stdint.h>
#include <stddef.h>

// SHA256 相关常量
#define SHA256_DIGEST_LENGTH 32
#define HMAC_SHA256_OUTPUT_LENGTH 32

// 返回值
#define CRYPTO_SUCCESS 0
#define CRYPTO_ERROR  -1

/**
 * @brief 计算 HMAC-SHA256
 *
 * @param output 输出：HMAC 结果 (32 字节)
 * @param key HMAC 密钥
 * @param key_len 密钥长度
 * @param data 输入数据
 * @param data_len 数据长度
 * @return CRYPTO_SUCCESS 成功，CRYPTO_ERROR 失败
 */
int hmac_sha256(uint8_t *output,
                const uint8_t *key, size_t key_len,
                const uint8_t *data, size_t data_len);

/**
 * @brief HKDF-Extract (RFC 5869)
 *
 * PRK = HMAC-Hash(salt, IKM)
 *
 * @param prk 输出：伪随机密钥 (32 字节)
 * @param salt 可选的盐值 (可为 NULL)
 * @param salt_len 盐值长度 (salt 为 NULL 时应为 0)
 * @param ikm 输入密钥材料
 * @param ikm_len 输入密钥材料长度
 * @return CRYPTO_SUCCESS 成功，CRYPTO_ERROR 失败
 */
int hkdf_extract(uint8_t *prk,
                 const uint8_t *salt, size_t salt_len,
                 const uint8_t *ikm, size_t ikm_len);

/**
 * @brief HKDF-Expand (RFC 5869)
 *
 * OKM = HKDF-Expand(PRK, info, L)
 *
 * @param okm 输出：输出密钥材料
 * @param okm_len 期望的输出长度 (最大 255 * 32 = 8160 字节)
 * @param prk 伪随机密钥 (32 字节)
 * @param info 可选的上下文信息 (可为 NULL)
 * @param info_len 上下文信息长度 (info 为 NULL 时应为 0)
 * @return CRYPTO_SUCCESS 成功，CRYPTO_ERROR 失败
 */
int hkdf_expand(uint8_t *okm, size_t okm_len,
                const uint8_t *prk,
                const uint8_t *info, size_t info_len);

/**
 * @brief HKDF 完整流程 (Extract + Expand)
 *
 * @param okm 输出：输出密钥材料
 * @param okm_len 期望的输出长度
 * @param salt 可选的盐值 (可为 NULL)
 * @param salt_len 盐值长度
 * @param ikm 输入密钥材料
 * @param ikm_len 输入密钥材料长度
 * @param info 可选的上下文信息 (可为 NULL)
 * @param info_len 上下文信息长度
 * @return CRYPTO_SUCCESS 成功，CRYPTO_ERROR 失败
 */
int hkdf_sha256(uint8_t *okm, size_t okm_len,
                const uint8_t *salt, size_t salt_len,
                const uint8_t *ikm, size_t ikm_len,
                const uint8_t *info, size_t info_len);

/**
 * @brief 计算 SHA256 哈希（辅助函数）
 *
 * @param output 输出：哈希值 (32 字节)
 * @param data 输入数据
 * @param data_len 数据长度
 * @return CRYPTO_SUCCESS 成功，CRYPTO_ERROR 失败
 */
int sha256_hash(uint8_t *output, const uint8_t *data, size_t data_len);

#endif // CRYPTO_UTILS_H
