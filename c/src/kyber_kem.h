/**
 * @file kyber_kem.h
 * @brief Kyber KEM 封装接口
 *
 * 提供简化的 Kyber512/768 KEM API，用于 PQ-Ntor 握手协议
 */

#ifndef KYBER_KEM_H
#define KYBER_KEM_H

#include <stdint.h>
#include <stddef.h>

// Kyber512 参数 (NIST Security Level 1)
#define KYBER512_PUBLIC_KEY_BYTES    800
#define KYBER512_SECRET_KEY_BYTES    1632
#define KYBER512_CIPHERTEXT_BYTES    768
#define KYBER512_SHARED_SECRET_BYTES 32

// Kyber768 参数 (NIST Security Level 3)
#define KYBER768_PUBLIC_KEY_BYTES    1184
#define KYBER768_SECRET_KEY_BYTES    2400
#define KYBER768_CIPHERTEXT_BYTES    1088
#define KYBER768_SHARED_SECRET_BYTES 32

// 选择使用的 Kyber 变体 (可在编译时切换)
#ifndef USE_KYBER768
    // 默认使用 Kyber512
    #define KYBER_PUBLIC_KEY_BYTES    KYBER512_PUBLIC_KEY_BYTES
    #define KYBER_SECRET_KEY_BYTES    KYBER512_SECRET_KEY_BYTES
    #define KYBER_CIPHERTEXT_BYTES    KYBER512_CIPHERTEXT_BYTES
    #define KYBER_SHARED_SECRET_BYTES KYBER512_SHARED_SECRET_BYTES
    #define KYBER_ALGORITHM_NAME      "Kyber512"
#else
    #define KYBER_PUBLIC_KEY_BYTES    KYBER768_PUBLIC_KEY_BYTES
    #define KYBER_SECRET_KEY_BYTES    KYBER768_SECRET_KEY_BYTES
    #define KYBER_CIPHERTEXT_BYTES    KYBER768_CIPHERTEXT_BYTES
    #define KYBER_SHARED_SECRET_BYTES KYBER768_SHARED_SECRET_BYTES
    #define KYBER_ALGORITHM_NAME      "Kyber768"
#endif

// 返回值
#define KYBER_SUCCESS 0
#define KYBER_ERROR  -1

/**
 * @brief 生成 Kyber 密钥对
 *
 * @param public_key 输出：公钥 (KYBER_PUBLIC_KEY_BYTES 字节)
 * @param secret_key 输出：私钥 (KYBER_SECRET_KEY_BYTES 字节)
 * @return KYBER_SUCCESS 成功，KYBER_ERROR 失败
 */
int kyber_keypair(uint8_t *public_key, uint8_t *secret_key);

/**
 * @brief Kyber 封装：生成密文和共享密钥
 *
 * @param ciphertext 输出：密文 (KYBER_CIPHERTEXT_BYTES 字节)
 * @param shared_secret 输出：共享密钥 (KYBER_SHARED_SECRET_BYTES 字节)
 * @param public_key 输入：对方的公钥 (KYBER_PUBLIC_KEY_BYTES 字节)
 * @return KYBER_SUCCESS 成功，KYBER_ERROR 失败
 */
int kyber_encapsulate(uint8_t *ciphertext,
                      uint8_t *shared_secret,
                      const uint8_t *public_key);

/**
 * @brief Kyber 解封装：从密文恢复共享密钥
 *
 * @param shared_secret 输出：共享密钥 (KYBER_SHARED_SECRET_BYTES 字节)
 * @param ciphertext 输入：密文 (KYBER_CIPHERTEXT_BYTES 字节)
 * @param secret_key 输入：自己的私钥 (KYBER_SECRET_KEY_BYTES 字节)
 * @return KYBER_SUCCESS 成功，KYBER_ERROR 失败
 */
int kyber_decapsulate(uint8_t *shared_secret,
                      const uint8_t *ciphertext,
                      const uint8_t *secret_key);

/**
 * @brief 获取当前使用的 Kyber 算法名称
 *
 * @return 算法名称字符串 ("Kyber512" 或 "Kyber768")
 */
const char* kyber_get_algorithm_name(void);

/**
 * @brief 打印 Kyber 参数信息（用于调试）
 */
void kyber_print_parameters(void);

/**
 * @brief 清理 Kyber KEM 资源（可选调用）
 */
void kyber_cleanup(void);

#endif // KYBER_KEM_H
