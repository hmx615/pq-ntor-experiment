/**
 * @file classic_ntor.h
 * @brief Classic Ntor 握手协议接口
 *
 * 基于 X25519 ECDH 的经典 Ntor 握手协议实现
 * 用于与 PQ-NTOR 进行性能对比
 *
 * 参考: Tor Spec - "TAP, CREATE and EXTEND cells"
 * 经典 ntor 使用 Curve25519 (X25519) 进行密钥交换
 *
 * 协议流程：
 * 1. Client: 生成临时密钥对 (x, X = x*G)
 * 2. Client → Server: onionskin (X, relay_identity)
 * 3. Server: 生成临时密钥 (y, Y = y*G)
 * 4. Server: 计算共享密钥 K = x*Y = y*X (ECDH)
 * 5. Server: 派生密钥 K_auth, K_enc = HKDF(K, transcript, "classic-ntor-keys")
 * 6. Server: 计算 AUTH = HMAC(K_auth, transcript || "server")
 * 7. Server → Client: reply (Y, AUTH)
 * 8. Client: 计算共享密钥 K = x*Y
 * 9. Client: 派生密钥并验证 AUTH
 * 10. 双方使用 K_enc 进行后续通信
 */

#ifndef CLASSIC_NTOR_H
#define CLASSIC_NTOR_H

#include <stdint.h>
#include <stddef.h>
#include "crypto_utils.h"

// X25519 密钥大小
#define X25519_KEY_SIZE      32   // 公钥和私钥都是32字节
#define X25519_SHARED_SIZE   32   // 共享密钥32字节

// Classic Ntor 消息大小
#define CLASSIC_NTOR_RELAY_ID_LENGTH   20  // 中继节点身份标识长度
#define CLASSIC_NTOR_ONIONSKIN_LEN     (X25519_KEY_SIZE + CLASSIC_NTOR_RELAY_ID_LENGTH)  // 52字节
#define CLASSIC_NTOR_REPLY_LEN         (X25519_KEY_SIZE + HMAC_SHA256_OUTPUT_LENGTH)    // 64字节

// 派生密钥长度（与PQ-NTOR保持一致以便对比）
#define CLASSIC_NTOR_KEY_AUTH_LEN      32  // 认证密钥
#define CLASSIC_NTOR_KEY_ENC_LEN       80  // 加密密钥：Kf(32) + Kb(32) + IVf(8) + IVb(8)
#define CLASSIC_NTOR_KEY_MATERIAL_LEN  (CLASSIC_NTOR_KEY_AUTH_LEN + CLASSIC_NTOR_KEY_ENC_LEN)

// 返回值
#define CLASSIC_NTOR_SUCCESS    0
#define CLASSIC_NTOR_ERROR     -1
#define CLASSIC_NTOR_AUTH_FAIL -2  // 认证失败

// 协议上下文信息
#define CLASSIC_NTOR_INFO_STRING "classic-ntor-keys"
#define CLASSIC_NTOR_SERVER_AUTH_STRING "server"

/**
 * @brief 客户端状态结构
 */
typedef struct {
    uint8_t client_public_key[X25519_KEY_SIZE];
    uint8_t client_secret_key[X25519_KEY_SIZE];
    uint8_t relay_identity[CLASSIC_NTOR_RELAY_ID_LENGTH];
    uint8_t shared_secret[X25519_SHARED_SIZE];
    uint8_t k_auth[CLASSIC_NTOR_KEY_AUTH_LEN];
    uint8_t k_enc[CLASSIC_NTOR_KEY_ENC_LEN];
} classic_ntor_client_state;

/**
 * @brief 服务端状态结构
 */
typedef struct {
    uint8_t shared_secret[X25519_SHARED_SIZE];
    uint8_t k_auth[CLASSIC_NTOR_KEY_AUTH_LEN];
    uint8_t k_enc[CLASSIC_NTOR_KEY_ENC_LEN];
} classic_ntor_server_state;

/**
 * @brief 客户端：创建 onionskin
 *
 * 生成 X25519 临时密钥对并构建 onionskin 消息
 *
 * @param state 客户端状态（输出）
 * @param onionskin 输出：onionskin 消息 (CLASSIC_NTOR_ONIONSKIN_LEN 字节)
 * @param relay_identity 中继节点身份标识 (CLASSIC_NTOR_RELAY_ID_LENGTH 字节)
 * @return CLASSIC_NTOR_SUCCESS 成功，CLASSIC_NTOR_ERROR 失败
 */
int classic_ntor_client_create_onionskin(classic_ntor_client_state *state,
                                         uint8_t *onionskin,
                                         const uint8_t *relay_identity);

/**
 * @brief 服务端：处理 onionskin 并创建 reply
 *
 * 接收 onionskin，进行 ECDH 密钥交换，派生会话密钥，创建 reply
 *
 * @param state 服务端状态（输出）
 * @param reply 输出：reply 消息 (CLASSIC_NTOR_REPLY_LEN 字节)
 * @param onionskin 输入：onionskin 消息 (CLASSIC_NTOR_ONIONSKIN_LEN 字节)
 * @param relay_identity 本节点的身份标识 (CLASSIC_NTOR_RELAY_ID_LENGTH 字节)
 * @return CLASSIC_NTOR_SUCCESS 成功，CLASSIC_NTOR_ERROR 失败
 */
int classic_ntor_server_create_reply(classic_ntor_server_state *state,
                                     uint8_t *reply,
                                     const uint8_t *onionskin,
                                     const uint8_t *relay_identity);

/**
 * @brief 客户端：处理 reply 并完成握手
 *
 * 接收 reply，进行 ECDH 密钥交换，派生会话密钥，验证认证标签
 *
 * @param state 客户端状态（输入/输出）
 * @param reply 输入：reply 消息 (CLASSIC_NTOR_REPLY_LEN 字节)
 * @return CLASSIC_NTOR_SUCCESS 成功，CLASSIC_NTOR_AUTH_FAIL 认证失败，CLASSIC_NTOR_ERROR 其他错误
 */
int classic_ntor_client_finish_handshake(classic_ntor_client_state *state,
                                         const uint8_t *reply);

/**
 * @brief 从客户端状态提取加密密钥
 *
 * @param key 输出：加密密钥 (CLASSIC_NTOR_KEY_ENC_LEN 字节)
 * @param state 客户端状态
 * @return CLASSIC_NTOR_SUCCESS 成功，CLASSIC_NTOR_ERROR 失败
 */
int classic_ntor_client_get_key(uint8_t *key, const classic_ntor_client_state *state);

/**
 * @brief 从服务端状态提取加密密钥
 *
 * @param key 输出：加密密钥 (CLASSIC_NTOR_KEY_ENC_LEN 字节)
 * @param state 服务端状态
 * @return CLASSIC_NTOR_SUCCESS 成功，CLASSIC_NTOR_ERROR 失败
 */
int classic_ntor_server_get_key(uint8_t *key, const classic_ntor_server_state *state);

/**
 * @brief 清理客户端状态（清除敏感数据）
 *
 * @param state 客户端状态
 */
void classic_ntor_client_state_cleanup(classic_ntor_client_state *state);

/**
 * @brief 清理服务端状态（清除敏感数据）
 *
 * @param state 服务端状态
 */
void classic_ntor_server_state_cleanup(classic_ntor_server_state *state);

#endif // CLASSIC_NTOR_H
