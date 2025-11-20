/**
 * @file test_kyber.c
 * @brief 测试 Kyber KEM 基本功能
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../src/kyber_kem.h"

// 打印十六进制数据（前 n 字节）
static void print_hex(const char *label, const uint8_t *data, size_t len, size_t preview) {
    printf("%s: ", label);
    for (size_t i = 0; i < preview && i < len; i++) {
        printf("%02x", data[i]);
    }
    if (len > preview) {
        printf("... (%zu bytes total)", len);
    } else {
        printf(" (%zu bytes)", len);
    }
    printf("\n");
}

int main(void) {
    printf("======================================================================\n");
    printf("🧪 Testing Kyber KEM Wrapper\n");
    printf("======================================================================\n\n");

    // 显示参数
    kyber_print_parameters();
    printf("\n");

    // 分配内存
    uint8_t *alice_public_key = malloc(KYBER_PUBLIC_KEY_BYTES);
    uint8_t *alice_secret_key = malloc(KYBER_SECRET_KEY_BYTES);
    uint8_t *ciphertext = malloc(KYBER_CIPHERTEXT_BYTES);
    uint8_t *shared_secret_bob = malloc(KYBER_SHARED_SECRET_BYTES);
    uint8_t *shared_secret_alice = malloc(KYBER_SHARED_SECRET_BYTES);

    if (!alice_public_key || !alice_secret_key || !ciphertext ||
        !shared_secret_bob || !shared_secret_alice) {
        fprintf(stderr, "❌ Memory allocation failed!\n");
        return 1;
    }

    // 第 1 步：Alice 生成密钥对
    printf("Step 1: Alice generates keypair\n");
    printf("---------------------------------------\n");
    int ret = kyber_keypair(alice_public_key, alice_secret_key);
    if (ret != KYBER_SUCCESS) {
        fprintf(stderr, "❌ Keypair generation failed!\n");
        goto cleanup;
    }
    print_hex("  Alice public key", alice_public_key, KYBER_PUBLIC_KEY_BYTES, 8);
    print_hex("  Alice secret key", alice_secret_key, KYBER_SECRET_KEY_BYTES, 8);
    printf("✓ Keypair generated successfully\n\n");

    // 第 2 步：Bob 封装（使用 Alice 的公钥）
    printf("Step 2: Bob encapsulates (using Alice's public key)\n");
    printf("---------------------------------------\n");
    ret = kyber_encapsulate(ciphertext, shared_secret_bob, alice_public_key);
    if (ret != KYBER_SUCCESS) {
        fprintf(stderr, "❌ Encapsulation failed!\n");
        goto cleanup;
    }
    print_hex("  Ciphertext", ciphertext, KYBER_CIPHERTEXT_BYTES, 8);
    print_hex("  Bob's shared secret", shared_secret_bob, KYBER_SHARED_SECRET_BYTES, 16);
    printf("✓ Encapsulation successful\n\n");

    // 第 3 步：Alice 解封装（使用她的私钥）
    printf("Step 3: Alice decapsulates (using her secret key)\n");
    printf("---------------------------------------\n");
    ret = kyber_decapsulate(shared_secret_alice, ciphertext, alice_secret_key);
    if (ret != KYBER_SUCCESS) {
        fprintf(stderr, "❌ Decapsulation failed!\n");
        goto cleanup;
    }
    print_hex("  Alice's shared secret", shared_secret_alice, KYBER_SHARED_SECRET_BYTES, 16);
    printf("✓ Decapsulation successful\n\n");

    // 第 4 步：验证共享密钥是否匹配
    printf("Step 4: Verify shared secrets match\n");
    printf("---------------------------------------\n");
    if (memcmp(shared_secret_alice, shared_secret_bob, KYBER_SHARED_SECRET_BYTES) == 0) {
        printf("✅ SUCCESS: Shared secrets match!\n");
        printf("   Shared secret (full): ");
        for (size_t i = 0; i < KYBER_SHARED_SECRET_BYTES; i++) {
            printf("%02x", shared_secret_alice[i]);
        }
        printf("\n");
    } else {
        fprintf(stderr, "❌ FAILURE: Shared secrets do NOT match!\n");
        fprintf(stderr, "   Bob:   ");
        for (size_t i = 0; i < KYBER_SHARED_SECRET_BYTES; i++) {
            fprintf(stderr, "%02x", shared_secret_bob[i]);
        }
        fprintf(stderr, "\n   Alice: ");
        for (size_t i = 0; i < KYBER_SHARED_SECRET_BYTES; i++) {
            fprintf(stderr, "%02x", shared_secret_alice[i]);
        }
        fprintf(stderr, "\n");
        goto cleanup;
    }

    printf("\n======================================================================\n");
    printf("✅ All Kyber KEM tests passed!\n");
    printf("======================================================================\n");

    // 清理
    ret = 0;
cleanup:
    free(alice_public_key);
    free(alice_secret_key);
    free(ciphertext);
    free(shared_secret_bob);
    free(shared_secret_alice);
    kyber_cleanup();
    return ret;
}
