/**
 * @file pq_ntor.h
 * @brief PQ-Ntor 握手协议接口
 *
 * 基于 Kyber KEM 的后量子 Ntor 握手协议实现
 *
 * 协议流程：
 * 1. Client: 生成临时密钥对 (pk_c, sk_c)
 * 2. Client → Server: onionskin (pk_c, relay_identity)
 * 3. Server: 封装生成 (ct, K_kem)
 * 4. Server: 派生密钥 K_auth, K_enc = HKDF(K_kem, transcript, "pq-ntor-keys")
 * 5. Server: 计算 AUTH = HMAC(K_auth, transcript || "server")
 * 6. Server → Client: reply (ct, AUTH)
 * 7. Client: 解封装得到 K_kem'
 * 8. Client: 派生密钥并验证 AUTH
 * 9. 双方使用 K_enc 进行后续通信
 */

#ifndef PQ_NTOR_H
#define PQ_NTOR_H

#include <stdint.h>
#include <stddef.h>
#include "kyber_kem.h"
#include "crypto_utils.h"

// PQ-Ntor 消息大小
#define PQ_NTOR_RELAY_ID_LENGTH   20  // 中继节点身份标识长度
#define PQ_NTOR_ONIONSKIN_LEN     (KYBER_PUBLIC_KEY_BYTES + PQ_NTOR_RELAY_ID_LENGTH)
#define PQ_NTOR_REPLY_LEN         (KYBER_CIPHERTEXT_BYTES + HMAC_SHA256_OUTPUT_LENGTH)

// 派生密钥长度
#define PQ_NTOR_KEY_AUTH_LEN      32  // 认证密钥
#define PQ_NTOR_KEY_ENC_LEN       80  // 加密密钥：Kf(32) + Kb(32) + IVf(8) + IVb(8)
#define PQ_NTOR_KEY_MATERIAL_LEN  (PQ_NTOR_KEY_AUTH_LEN + PQ_NTOR_KEY_ENC_LEN)

// 返回值
#define PQ_NTOR_SUCCESS    0
#define PQ_NTOR_ERROR     -1
#define PQ_NTOR_AUTH_FAIL -2  // 认证失败

// 协议上下文信息
#define PQ_NTOR_INFO_STRING "pq-ntor-keys"
#define PQ_NTOR_SERVER_AUTH_STRING "server"

/**
 * @brief 客户端状态结构
 */
typedef struct {
    uint8_t client_public_key[KYBER_PUBLIC_KEY_BYTES];
    uint8_t client_secret_key[KYBER_SECRET_KEY_BYTES];
    uint8_t relay_identity[PQ_NTOR_RELAY_ID_LENGTH];
    uint8_t k_kem[KYBER_SHARED_SECRET_BYTES];
    uint8_t k_auth[PQ_NTOR_KEY_AUTH_LEN];
    uint8_t k_enc[PQ_NTOR_KEY_ENC_LEN];
} pq_ntor_client_state;

/**
 * @brief 服务端状态结构
 */
typedef struct {
    uint8_t k_kem[KYBER_SHARED_SECRET_BYTES];
    uint8_t k_auth[PQ_NTOR_KEY_AUTH_LEN];
    uint8_t k_enc[PQ_NTOR_KEY_ENC_LEN];
} pq_ntor_server_state;

/**
 * @brief 客户端：创建 onionskin
 *
 * 生成临时密钥对并构建 onionskin 消息
 *
 * @param state 客户端状态（输出）
 * @param onionskin 输出：onionskin 消息 (PQ_NTOR_ONIONSKIN_LEN 字节)
 * @param relay_identity 中继节点身份标识 (PQ_NTOR_RELAY_ID_LENGTH 字节)
 * @return PQ_NTOR_SUCCESS 成功，PQ_NTOR_ERROR 失败
 */
int pq_ntor_client_create_onionskin(pq_ntor_client_state *state,
                                    uint8_t *onionskin,
                                    const uint8_t *relay_identity);

/**
 * @brief 服务端：处理 onionskin 并创建 reply
 *
 * 接收 onionskin，封装生成共享密钥，派生会话密钥，创建 reply
 *
 * @param state 服务端状态（输出）
 * @param reply 输出：reply 消息 (PQ_NTOR_REPLY_LEN 字节)
 * @param onionskin 输入：onionskin 消息 (PQ_NTOR_ONIONSKIN_LEN 字节)
 * @param relay_identity 本节点的身份标识 (PQ_NTOR_RELAY_ID_LENGTH 字节)
 * @return PQ_NTOR_SUCCESS 成功，PQ_NTOR_ERROR 失败
 */
int pq_ntor_server_create_reply(pq_ntor_server_state *state,
                                uint8_t *reply,
                                const uint8_t *onionskin,
                                const uint8_t *relay_identity);

/**
 * @brief 客户端：处理 reply 并完成握手
 *
 * 接收 reply，解封装恢复共享密钥，派生会话密钥，验证认证标签
 *
 * @param state 客户端状态（输入/输出）
 * @param reply 输入：reply 消息 (PQ_NTOR_REPLY_LEN 字节)
 * @return PQ_NTOR_SUCCESS 成功，PQ_NTOR_AUTH_FAIL 认证失败，PQ_NTOR_ERROR 其他错误
 */
int pq_ntor_client_finish_handshake(pq_ntor_client_state *state,
                                    const uint8_t *reply);

/**
 * @brief 从客户端状态提取加密密钥
 *
 * @param key 输出：加密密钥 (PQ_NTOR_KEY_ENC_LEN 字节)
 * @param state 客户端状态
 * @return PQ_NTOR_SUCCESS 成功，PQ_NTOR_ERROR 失败
 */
int pq_ntor_client_get_key(uint8_t *key, const pq_ntor_client_state *state);

/**
 * @brief 从服务端状态提取加密密钥
 *
 * @param key 输出：加密密钥 (PQ_NTOR_KEY_ENC_LEN 字节)
 * @param state 服务端状态
 * @return PQ_NTOR_SUCCESS 成功，PQ_NTOR_ERROR 失败
 */
int pq_ntor_server_get_key(uint8_t *key, const pq_ntor_server_state *state);

/**
 * @brief 清理客户端状态（清除敏感数据）
 *
 * @param state 客户端状态
 */
void pq_ntor_client_state_cleanup(pq_ntor_client_state *state);

/**
 * @brief 清理服务端状态（清除敏感数据）
 *
 * @param state 服务端状态
 */
void pq_ntor_server_state_cleanup(pq_ntor_server_state *state);

#endif // PQ_NTOR_H
