/**
 * @file test_classic_ntor.c
 * @brief Classic NTOR 握手协议测试
 */

#include <stdio.h>
#include <string.h>
#include <time.h>
#include "../src/classic_ntor.h"

#define TEST_PASS "\033[0;32m[PASS]\033[0m"
#define TEST_FAIL "\033[0;31m[FAIL]\033[0m"

void print_hex(const char *label, const uint8_t *data, size_t len) {
    printf("%s: ", label);
    for (size_t i = 0; i < len; i++) {
        printf("%02x", data[i]);
        if ((i + 1) % 32 == 0 && i + 1 < len) printf("\n%*s", (int)strlen(label) + 2, "");
    }
    printf("\n");
}

int test_classic_ntor_handshake() {
    printf("\n=== Test 1: Classic NTOR Complete Handshake ===\n");

    classic_ntor_client_state client_state;
    classic_ntor_server_state server_state;
    uint8_t onionskin[CLASSIC_NTOR_ONIONSKIN_LEN];
    uint8_t reply[CLASSIC_NTOR_REPLY_LEN];
    uint8_t relay_identity[CLASSIC_NTOR_RELAY_ID_LENGTH];
    uint8_t client_key[CLASSIC_NTOR_KEY_ENC_LEN];
    uint8_t server_key[CLASSIC_NTOR_KEY_ENC_LEN];

    // 生成测试用的 relay identity
    memset(relay_identity, 0xAA, CLASSIC_NTOR_RELAY_ID_LENGTH);

    // 客户端：创建 onionskin
    printf("Client: Creating onionskin...\n");
    clock_t start = clock();
    int ret = classic_ntor_client_create_onionskin(&client_state, onionskin, relay_identity);
    clock_t end = clock();
    double client_create_time = ((double)(end - start) / CLOCKS_PER_SEC) * 1000000;

    if (ret != CLASSIC_NTOR_SUCCESS) {
        printf("%s Client failed to create onionskin\n", TEST_FAIL);
        return -1;
    }
    printf("%s Client created onionskin (%.2f μs)\n", TEST_PASS, client_create_time);
    printf("Onionskin size: %d bytes\n", CLASSIC_NTOR_ONIONSKIN_LEN);

    // 服务端：处理 onionskin 并创建 reply
    printf("\nServer: Processing onionskin and creating reply...\n");
    start = clock();
    ret = classic_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity);
    end = clock();
    double server_reply_time = ((double)(end - start) / CLOCKS_PER_SEC) * 1000000;

    if (ret != CLASSIC_NTOR_SUCCESS) {
        printf("%s Server failed to create reply\n", TEST_FAIL);
        return -1;
    }
    printf("%s Server created reply (%.2f μs)\n", TEST_PASS, server_reply_time);
    printf("Reply size: %d bytes\n", CLASSIC_NTOR_REPLY_LEN);

    // 客户端：处理 reply 并完成握手
    printf("\nClient: Processing reply and finishing handshake...\n");
    start = clock();
    ret = classic_ntor_client_finish_handshake(&client_state, reply);
    end = clock();
    double client_finish_time = ((double)(end - start) / CLOCKS_PER_SEC) * 1000000;

    if (ret != CLASSIC_NTOR_SUCCESS) {
        printf("%s Client failed to finish handshake\n", TEST_FAIL);
        return -1;
    }
    printf("%s Client finished handshake (%.2f μs)\n", TEST_PASS, client_finish_time);

    // 提取密钥
    classic_ntor_client_get_key(client_key, &client_state);
    classic_ntor_server_get_key(server_key, &server_state);

    // 验证密钥一致性
    printf("\nVerifying key agreement...\n");
    if (memcmp(client_key, server_key, CLASSIC_NTOR_KEY_ENC_LEN) == 0) {
        printf("%s Keys match!\n", TEST_PASS);
    } else {
        printf("%s Keys do not match!\n", TEST_FAIL);
        print_hex("Client key", client_key, 32);
        print_hex("Server key", server_key, 32);
        return -1;
    }

    // 性能总结
    printf("\n=== Performance Summary ===\n");
    printf("Client onionskin creation: %.2f μs\n", client_create_time);
    printf("Server reply creation:     %.2f μs\n", server_reply_time);
    printf("Client handshake finish:   %.2f μs\n", client_finish_time);
    printf("Total handshake time:      %.2f μs (%.3f ms)\n",
           client_create_time + server_reply_time + client_finish_time,
           (client_create_time + server_reply_time + client_finish_time) / 1000.0);
    printf("Message sizes: Onionskin=%d bytes, Reply=%d bytes\n",
           CLASSIC_NTOR_ONIONSKIN_LEN, CLASSIC_NTOR_REPLY_LEN);

    // 清理
    classic_ntor_client_state_cleanup(&client_state);
    classic_ntor_server_state_cleanup(&server_state);

    return 0;
}

int test_auth_failure() {
    printf("\n=== Test 2: Authentication Failure Detection ===\n");

    classic_ntor_client_state client_state;
    classic_ntor_server_state server_state;
    uint8_t onionskin[CLASSIC_NTOR_ONIONSKIN_LEN];
    uint8_t reply[CLASSIC_NTOR_REPLY_LEN];
    uint8_t relay_identity[CLASSIC_NTOR_RELAY_ID_LENGTH];

    memset(relay_identity, 0xBB, CLASSIC_NTOR_RELAY_ID_LENGTH);

    // 正常握手流程
    classic_ntor_client_create_onionskin(&client_state, onionskin, relay_identity);
    classic_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity);

    // 篡改 reply 中的认证标签
    printf("Tampering with authentication tag...\n");
    reply[X25519_KEY_SIZE] ^= 0x01;  // 翻转一位

    // 客户端验证应该失败
    int ret = classic_ntor_client_finish_handshake(&client_state, reply);
    if (ret == CLASSIC_NTOR_AUTH_FAIL) {
        printf("%s Authentication failure correctly detected\n", TEST_PASS);
        return 0;
    } else {
        printf("%s Failed to detect authentication failure\n", TEST_FAIL);
        return -1;
    }
}

int test_performance_benchmark() {
    printf("\n=== Test 3: Performance Benchmark (100 iterations) ===\n");

    const int iterations = 100;
    double total_client_create = 0;
    double total_server_reply = 0;
    double total_client_finish = 0;

    for (int i = 0; i < iterations; i++) {
        classic_ntor_client_state client_state;
        classic_ntor_server_state server_state;
        uint8_t onionskin[CLASSIC_NTOR_ONIONSKIN_LEN];
        uint8_t reply[CLASSIC_NTOR_REPLY_LEN];
        uint8_t relay_identity[CLASSIC_NTOR_RELAY_ID_LENGTH];

        memset(relay_identity, i & 0xFF, CLASSIC_NTOR_RELAY_ID_LENGTH);

        clock_t start, end;

        // Client create
        start = clock();
        classic_ntor_client_create_onionskin(&client_state, onionskin, relay_identity);
        end = clock();
        total_client_create += ((double)(end - start) / CLOCKS_PER_SEC) * 1000000;

        // Server reply
        start = clock();
        classic_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity);
        end = clock();
        total_server_reply += ((double)(end - start) / CLOCKS_PER_SEC) * 1000000;

        // Client finish
        start = clock();
        classic_ntor_client_finish_handshake(&client_state, reply);
        end = clock();
        total_client_finish += ((double)(end - start) / CLOCKS_PER_SEC) * 1000000;

        classic_ntor_client_state_cleanup(&client_state);
        classic_ntor_server_state_cleanup(&server_state);
    }

    printf("Average times over %d iterations:\n", iterations);
    printf("  Client onionskin creation: %.2f μs\n", total_client_create / iterations);
    printf("  Server reply creation:     %.2f μs\n", total_server_reply / iterations);
    printf("  Client handshake finish:   %.2f μs\n", total_client_finish / iterations);
    printf("  Total handshake time:      %.2f μs (%.3f ms)\n",
           (total_client_create + total_server_reply + total_client_finish) / iterations,
           (total_client_create + total_server_reply + total_client_finish) / iterations / 1000.0);

    printf("%s Performance benchmark completed\n", TEST_PASS);
    return 0;
}

int main() {
    printf("╔══════════════════════════════════════════════════════════╗\n");
    printf("║     Classic NTOR (X25519) Handshake Protocol Test       ║\n");
    printf("╚══════════════════════════════════════════════════════════╝\n");

    int failed = 0;

    if (test_classic_ntor_handshake() != 0) failed++;
    if (test_auth_failure() != 0) failed++;
    if (test_performance_benchmark() != 0) failed++;

    printf("\n╔══════════════════════════════════════════════════════════╗\n");
    if (failed == 0) {
        printf("║                   ALL TESTS PASSED ✓                     ║\n");
    } else {
        printf("║                 %d TEST(S) FAILED ✗                      ║\n", failed);
    }
    printf("╚══════════════════════════════════════════════════════════╝\n");

    return failed;
}
