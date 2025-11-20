/**
 * @file test_pq_ntor.c
 * @brief PQ-Ntor 握手协议测试程序
 *
 * 测试完整的客户端-服务端握手流程
 */

#include <stdio.h>
#include <string.h>
#include <assert.h>
#include "../src/pq_ntor.h"

// 辅助函数：打印十六进制
void print_hex(const char *label, const uint8_t *data, size_t len) {
    printf("%s (%zu bytes): ", label, len);
    if (len <= 32) {
        for (size_t i = 0; i < len; i++) {
            printf("%02x", data[i]);
        }
    } else {
        // 只打印前 16 和后 16 字节
        for (size_t i = 0; i < 16; i++) {
            printf("%02x", data[i]);
        }
        printf("...");
        for (size_t i = len - 16; i < len; i++) {
            printf("%02x", data[i]);
        }
    }
    printf("\n");
}

// 测试基本握手流程
void test_basic_handshake() {
    printf("\n=== Test 1: Basic Handshake ===\n");

    // 设置 relay 身份
    uint8_t relay_identity[PQ_NTOR_RELAY_ID_LENGTH];
    memset(relay_identity, 0xAB, sizeof(relay_identity));
    printf("Relay ID: ");
    for (int i = 0; i < PQ_NTOR_RELAY_ID_LENGTH; i++) {
        printf("%02x", relay_identity[i]);
    }
    printf("\n\n");

    // === 客户端：创建 onionskin ===
    printf("Step 1: Client creates onionskin\n");
    pq_ntor_client_state client_state;
    uint8_t onionskin[PQ_NTOR_ONIONSKIN_LEN];

    int ret = pq_ntor_client_create_onionskin(&client_state, onionskin, relay_identity);
    assert(ret == PQ_NTOR_SUCCESS);

    printf("✓ Onionskin created\n");
    print_hex("  Onionskin", onionskin, PQ_NTOR_ONIONSKIN_LEN);
    printf("  (Client PK: %zu bytes + Relay ID: %d bytes)\n\n",
           (size_t)KYBER_PUBLIC_KEY_BYTES, PQ_NTOR_RELAY_ID_LENGTH);

    // === 服务端：处理 onionskin 并创建 reply ===
    printf("Step 2: Server processes onionskin and creates reply\n");
    pq_ntor_server_state server_state;
    uint8_t reply[PQ_NTOR_REPLY_LEN];

    ret = pq_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity);
    assert(ret == PQ_NTOR_SUCCESS);

    printf("✓ Reply created\n");
    print_hex("  Reply", reply, PQ_NTOR_REPLY_LEN);
    printf("  (Ciphertext: %zu bytes + AUTH: %d bytes)\n\n",
           (size_t)KYBER_CIPHERTEXT_BYTES, HMAC_SHA256_OUTPUT_LENGTH);

    // === 客户端：处理 reply 并完成握手 ===
    printf("Step 3: Client processes reply and finishes handshake\n");
    ret = pq_ntor_client_finish_handshake(&client_state, reply);
    assert(ret == PQ_NTOR_SUCCESS);

    printf("✓ Handshake completed successfully\n");
    printf("✓ AUTH verification passed\n\n");

    // === 提取会话密钥 ===
    printf("Step 4: Extract session keys\n");
    uint8_t client_key[PQ_NTOR_KEY_ENC_LEN];
    uint8_t server_key[PQ_NTOR_KEY_ENC_LEN];

    ret = pq_ntor_client_get_key(client_key, &client_state);
    assert(ret == PQ_NTOR_SUCCESS);

    ret = pq_ntor_server_get_key(server_key, &server_state);
    assert(ret == PQ_NTOR_SUCCESS);

    print_hex("  Client K_enc", client_key, PQ_NTOR_KEY_ENC_LEN);
    print_hex("  Server K_enc", server_key, PQ_NTOR_KEY_ENC_LEN);

    // 验证双方密钥一致
    assert(memcmp(client_key, server_key, PQ_NTOR_KEY_ENC_LEN) == 0);
    printf("✓ Keys match!\n");

    // 清理
    pq_ntor_client_state_cleanup(&client_state);
    pq_ntor_server_state_cleanup(&server_state);

    printf("\n✅ Test 1 PASSED: Basic handshake works correctly\n");
}

// 测试认证失败场景
void test_auth_failure() {
    printf("\n=== Test 2: AUTH Failure Detection ===\n");

    uint8_t relay_identity[PQ_NTOR_RELAY_ID_LENGTH];
    memset(relay_identity, 0xCD, sizeof(relay_identity));

    // 客户端创建 onionskin
    pq_ntor_client_state client_state;
    uint8_t onionskin[PQ_NTOR_ONIONSKIN_LEN];
    int ret = pq_ntor_client_create_onionskin(&client_state, onionskin, relay_identity);
    assert(ret == PQ_NTOR_SUCCESS);

    // 服务端创建 reply
    pq_ntor_server_state server_state;
    uint8_t reply[PQ_NTOR_REPLY_LEN];
    ret = pq_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity);
    assert(ret == PQ_NTOR_SUCCESS);

    // 篡改 reply 中的 AUTH（最后一个字节）
    printf("Tampering with AUTH tag...\n");
    reply[PQ_NTOR_REPLY_LEN - 1] ^= 0x01;

    // 客户端应该检测到认证失败
    ret = pq_ntor_client_finish_handshake(&client_state, reply);
    assert(ret == PQ_NTOR_AUTH_FAIL);

    printf("✓ AUTH failure correctly detected\n");

    pq_ntor_client_state_cleanup(&client_state);
    pq_ntor_server_state_cleanup(&server_state);

    printf("\n✅ Test 2 PASSED: AUTH verification works\n");
}

// 测试多次握手
void test_multiple_handshakes() {
    printf("\n=== Test 3: Multiple Handshakes ===\n");

    uint8_t relay_identity[PQ_NTOR_RELAY_ID_LENGTH];

    for (int i = 0; i < 3; i++) {
        printf("Handshake #%d...\n", i + 1);

        // 每次使用不同的 relay_identity
        memset(relay_identity, 0x10 + i, sizeof(relay_identity));

        pq_ntor_client_state client_state;
        pq_ntor_server_state server_state;
        uint8_t onionskin[PQ_NTOR_ONIONSKIN_LEN];
        uint8_t reply[PQ_NTOR_REPLY_LEN];

        // 完整握手
        int ret = pq_ntor_client_create_onionskin(&client_state, onionskin, relay_identity);
        assert(ret == PQ_NTOR_SUCCESS);

        ret = pq_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity);
        assert(ret == PQ_NTOR_SUCCESS);

        ret = pq_ntor_client_finish_handshake(&client_state, reply);
        assert(ret == PQ_NTOR_SUCCESS);

        // 验证密钥
        uint8_t client_key[PQ_NTOR_KEY_ENC_LEN];
        uint8_t server_key[PQ_NTOR_KEY_ENC_LEN];
        pq_ntor_client_get_key(client_key, &client_state);
        pq_ntor_server_get_key(server_key, &server_state);
        assert(memcmp(client_key, server_key, PQ_NTOR_KEY_ENC_LEN) == 0);

        printf("  ✓ Handshake #%d completed\n", i + 1);

        pq_ntor_client_state_cleanup(&client_state);
        pq_ntor_server_state_cleanup(&server_state);
    }

    printf("\n✅ Test 3 PASSED: Multiple handshakes work\n");
}

// 测试通信开销
void test_communication_overhead() {
    printf("\n=== Test 4: Communication Overhead Analysis ===\n");

    printf("Protocol message sizes:\n");
    printf("  - Onionskin:  %zu bytes\n", (size_t)PQ_NTOR_ONIONSKIN_LEN);
    printf("    • Client PK:   %zu bytes\n", (size_t)KYBER_PUBLIC_KEY_BYTES);
    printf("    • Relay ID:    %d bytes\n", PQ_NTOR_RELAY_ID_LENGTH);
    printf("\n");
    printf("  - Reply:      %zu bytes\n", (size_t)PQ_NTOR_REPLY_LEN);
    printf("    • Ciphertext:  %zu bytes\n", (size_t)KYBER_CIPHERTEXT_BYTES);
    printf("    • AUTH tag:    %d bytes\n", HMAC_SHA256_OUTPUT_LENGTH);
    printf("\n");
    printf("  - Total handshake: %zu bytes\n",
           (size_t)(PQ_NTOR_ONIONSKIN_LEN + PQ_NTOR_REPLY_LEN));
    printf("\n");

    printf("Comparison with original Ntor:\n");
    printf("  - Original Ntor onionskin:  ~84 bytes\n");
    printf("  - Original Ntor reply:      ~64 bytes\n");
    printf("  - Original Ntor total:      ~148 bytes\n");
    printf("\n");
    printf("  - PQ-Ntor overhead: %.1fx increase\n",
           (double)(PQ_NTOR_ONIONSKIN_LEN + PQ_NTOR_REPLY_LEN) / 148.0);

    printf("\n✅ Test 4 PASSED: Overhead measurements completed\n");
}

int main() {
    printf("======================================================================\n");
    printf("PQ-Ntor Handshake Protocol Test Suite\n");
    printf("======================================================================\n");
    printf("Using: %s\n", kyber_get_algorithm_name());
    kyber_print_parameters();
    printf("\n");

    test_basic_handshake();
    test_auth_failure();
    test_multiple_handshakes();
    test_communication_overhead();

    printf("\n======================================================================\n");
    printf("✅ All PQ-Ntor tests passed!\n");
    printf("======================================================================\n");

    return 0;
}
