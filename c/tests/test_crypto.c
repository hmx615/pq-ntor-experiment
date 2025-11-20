/**
 * @file test_crypto.c
 * @brief 加密工具函数测试程序
 *
 * 测试 HMAC-SHA256 和 HKDF-SHA256 的正确性
 */

#include <stdio.h>
#include <string.h>
#include <assert.h>
#include "../src/crypto_utils.h"

// 辅助函数：打印十六进制
void print_hex(const char *label, const uint8_t *data, size_t len) {
    printf("%s: ", label);
    for (size_t i = 0; i < len; i++) {
        printf("%02x", data[i]);
    }
    printf("\n");
}

// 辅助函数：比较字节数组
int bytes_equal(const uint8_t *a, const uint8_t *b, size_t len) {
    return memcmp(a, b, len) == 0;
}

// 测试 HMAC-SHA256
void test_hmac_sha256() {
    printf("\n=== Test HMAC-SHA256 ===\n");

    // RFC 4231 Test Case 2
    uint8_t key[] = "Jefe";
    uint8_t data[] = "what do ya want for nothing?";
    uint8_t output[HMAC_SHA256_OUTPUT_LENGTH];

    // 期望的 HMAC-SHA256 结果 (RFC 4231)
    uint8_t expected[] = {
        0x5b, 0xdc, 0xc1, 0x46, 0xbf, 0x60, 0x75, 0x4e,
        0x6a, 0x04, 0x24, 0x26, 0x08, 0x95, 0x75, 0xc7,
        0x5a, 0x00, 0x3f, 0x08, 0x9d, 0x27, 0x39, 0x83,
        0x9d, 0xec, 0x58, 0xb9, 0x64, 0xec, 0x38, 0x43
    };

    int ret = hmac_sha256(output, key, strlen((char*)key), data, strlen((char*)data));
    assert(ret == CRYPTO_SUCCESS);

    print_hex("Computed", output, HMAC_SHA256_OUTPUT_LENGTH);
    print_hex("Expected", expected, HMAC_SHA256_OUTPUT_LENGTH);

    if (bytes_equal(output, expected, HMAC_SHA256_OUTPUT_LENGTH)) {
        printf("✓ HMAC-SHA256 test PASSED\n");
    } else {
        printf("✗ HMAC-SHA256 test FAILED\n");
        assert(0);
    }
}

// 测试 HKDF-Extract
void test_hkdf_extract() {
    printf("\n=== Test HKDF-Extract ===\n");

    // RFC 5869 Test Case 1
    uint8_t ikm[] = {
        0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b,
        0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b,
        0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b
    };
    uint8_t salt[] = {
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0a, 0x0b, 0x0c
    };
    uint8_t prk[SHA256_DIGEST_LENGTH];

    // 期望的 PRK (RFC 5869)
    uint8_t expected_prk[] = {
        0x07, 0x77, 0x09, 0x36, 0x2c, 0x2e, 0x32, 0xdf,
        0x0d, 0xdc, 0x3f, 0x0d, 0xc4, 0x7b, 0xba, 0x63,
        0x90, 0xb6, 0xc7, 0x3b, 0xb5, 0x0f, 0x9c, 0x31,
        0x22, 0xec, 0x84, 0x4a, 0xd7, 0xc2, 0xb3, 0xe5
    };

    int ret = hkdf_extract(prk, salt, sizeof(salt), ikm, sizeof(ikm));
    assert(ret == CRYPTO_SUCCESS);

    print_hex("PRK Computed", prk, SHA256_DIGEST_LENGTH);
    print_hex("PRK Expected", expected_prk, SHA256_DIGEST_LENGTH);

    if (bytes_equal(prk, expected_prk, SHA256_DIGEST_LENGTH)) {
        printf("✓ HKDF-Extract test PASSED\n");
    } else {
        printf("✗ HKDF-Extract test FAILED\n");
        assert(0);
    }
}

// 测试 HKDF-Expand
void test_hkdf_expand() {
    printf("\n=== Test HKDF-Expand ===\n");

    // RFC 5869 Test Case 1
    uint8_t prk[] = {
        0x07, 0x77, 0x09, 0x36, 0x2c, 0x2e, 0x32, 0xdf,
        0x0d, 0xdc, 0x3f, 0x0d, 0xc4, 0x7b, 0xba, 0x63,
        0x90, 0xb6, 0xc7, 0x3b, 0xb5, 0x0f, 0x9c, 0x31,
        0x22, 0xec, 0x84, 0x4a, 0xd7, 0xc2, 0xb3, 0xe5
    };
    uint8_t info[] = {0xf0, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8, 0xf9};
    uint8_t okm[42];

    // 期望的 OKM (RFC 5869, 前 42 字节)
    uint8_t expected_okm[] = {
        0x3c, 0xb2, 0x5f, 0x25, 0xfa, 0xac, 0xd5, 0x7a,
        0x90, 0x43, 0x4f, 0x64, 0xd0, 0x36, 0x2f, 0x2a,
        0x2d, 0x2d, 0x0a, 0x90, 0xcf, 0x1a, 0x5a, 0x4c,
        0x5d, 0xb0, 0x2d, 0x56, 0xec, 0xc4, 0xc5, 0xbf,
        0x34, 0x00, 0x72, 0x08, 0xd5, 0xb8, 0x87, 0x18,
        0x58, 0x65
    };

    int ret = hkdf_expand(okm, sizeof(okm), prk, info, sizeof(info));
    assert(ret == CRYPTO_SUCCESS);

    print_hex("OKM Computed", okm, sizeof(okm));
    print_hex("OKM Expected", expected_okm, sizeof(expected_okm));

    if (bytes_equal(okm, expected_okm, sizeof(okm))) {
        printf("✓ HKDF-Expand test PASSED\n");
    } else {
        printf("✗ HKDF-Expand test FAILED\n");
        assert(0);
    }
}

// 测试完整 HKDF
void test_hkdf_full() {
    printf("\n=== Test HKDF (Full) ===\n");

    // RFC 5869 Test Case 1
    uint8_t ikm[] = {
        0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b,
        0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b,
        0x0b, 0x0b, 0x0b, 0x0b, 0x0b, 0x0b
    };
    uint8_t salt[] = {
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0a, 0x0b, 0x0c
    };
    uint8_t info[] = {0xf0, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8, 0xf9};
    uint8_t okm[42];

    uint8_t expected_okm[] = {
        0x3c, 0xb2, 0x5f, 0x25, 0xfa, 0xac, 0xd5, 0x7a,
        0x90, 0x43, 0x4f, 0x64, 0xd0, 0x36, 0x2f, 0x2a,
        0x2d, 0x2d, 0x0a, 0x90, 0xcf, 0x1a, 0x5a, 0x4c,
        0x5d, 0xb0, 0x2d, 0x56, 0xec, 0xc4, 0xc5, 0xbf,
        0x34, 0x00, 0x72, 0x08, 0xd5, 0xb8, 0x87, 0x18,
        0x58, 0x65
    };

    int ret = hkdf_sha256(okm, sizeof(okm), salt, sizeof(salt), ikm, sizeof(ikm), info, sizeof(info));
    assert(ret == CRYPTO_SUCCESS);

    print_hex("Full HKDF OKM", okm, sizeof(okm));
    print_hex("Expected OKM ", expected_okm, sizeof(expected_okm));

    if (bytes_equal(okm, expected_okm, sizeof(okm))) {
        printf("✓ HKDF (Full) test PASSED\n");
    } else {
        printf("✗ HKDF (Full) test FAILED\n");
        assert(0);
    }
}

// 测试 PQ-Ntor 场景
void test_pq_ntor_scenario() {
    printf("\n=== Test PQ-Ntor Key Derivation Scenario ===\n");

    // 模拟 Kyber 共享密钥
    uint8_t k_kem[32] = {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
        0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10,
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
        0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10
    };

    // 模拟握手转录 (transcript)
    uint8_t transcript[100];
    memset(transcript, 0xaa, sizeof(transcript));

    // 上下文信息
    uint8_t info[] = "pq-ntor-keys";

    // 派生密钥材料 (K_auth || K_enc)
    uint8_t key_material[64]; // 32 bytes K_auth + 32 bytes K_enc

    int ret = hkdf_sha256(key_material, sizeof(key_material),
                          NULL, 0,  // 不使用 salt
                          k_kem, sizeof(k_kem),
                          info, strlen((char*)info));
    assert(ret == CRYPTO_SUCCESS);

    printf("K_kem:        ");
    for (int i = 0; i < 32; i++) printf("%02x", k_kem[i]);
    printf("\n");

    printf("K_auth:       ");
    for (int i = 0; i < 32; i++) printf("%02x", key_material[i]);
    printf("\n");

    printf("K_enc:        ");
    for (int i = 0; i < 32; i++) printf("%02x", key_material[32 + i]);
    printf("\n");

    // 计算 AUTH = HMAC(K_auth, transcript)
    uint8_t auth[HMAC_SHA256_OUTPUT_LENGTH];
    ret = hmac_sha256(auth, key_material, 32, transcript, sizeof(transcript));
    assert(ret == CRYPTO_SUCCESS);

    printf("AUTH:         ");
    for (int i = 0; i < 32; i++) printf("%02x", auth[i]);
    printf("\n");

    printf("✓ PQ-Ntor scenario test PASSED\n");
}

int main() {
    printf("======================================================================\n");
    printf("Crypto Utils Test Suite\n");
    printf("======================================================================\n");

    test_hmac_sha256();
    test_hkdf_extract();
    test_hkdf_expand();
    test_hkdf_full();
    test_pq_ntor_scenario();

    printf("\n======================================================================\n");
    printf("✅ All crypto tests passed!\n");
    printf("======================================================================\n");

    return 0;
}
