/**
 * test_kyber_simple.c - 飞腾派Kyber KEM验证程序
 *
 * 功能: 测试liboqs在ARM64上是否正常工作
 *
 * 如果此程序运行成功，说明飞腾派环境完全就绪，可以编译完整的PQ-Tor代码！
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <oqs/oqs.h>

int main(void) {
    printf("======================================\n");
    printf("  飞腾派Kyber KEM验证程序\n");
    printf("======================================\n\n");

    // 1. 检查Kyber512是否可用
    printf("[1/4] 检查Kyber512算法...\n");
    if (!OQS_KEM_alg_is_enabled("Kyber512")) {
        fprintf(stderr, "      ❌ Kyber512不可用\n");
        return 1;
    }
    printf("      ✅ Kyber512可用\n\n");

    // 2. 创建KEM对象
    printf("[2/4] 创建KEM对象...\n");
    OQS_KEM *kem = OQS_KEM_new("Kyber512");
    if (kem == NULL) {
        fprintf(stderr, "      ❌ 创建KEM失败\n");
        return 1;
    }
    printf("      ✅ KEM对象创建成功\n");
    printf("      公钥大小: %zu bytes\n", kem->length_public_key);
    printf("      密钥大小: %zu bytes\n", kem->length_secret_key);
    printf("      密文大小: %zu bytes\n", kem->length_ciphertext);
    printf("      共享密钥: %zu bytes\n\n", kem->length_shared_secret);

    // 3. 密钥生成
    printf("[3/4] 生成密钥对...\n");
    uint8_t *public_key = malloc(kem->length_public_key);
    uint8_t *secret_key = malloc(kem->length_secret_key);

    if (public_key == NULL || secret_key == NULL) {
        fprintf(stderr, "      ❌ 内存分配失败\n");
        OQS_KEM_free(kem);
        return 1;
    }

    if (OQS_KEM_keypair(kem, public_key, secret_key) != OQS_SUCCESS) {
        fprintf(stderr, "      ❌ 密钥生成失败\n");
        free(public_key);
        free(secret_key);
        OQS_KEM_free(kem);
        return 1;
    }
    printf("      ✅ 密钥对生成成功\n\n");

    // 4. 封装/解封装测试
    printf("[4/4] 测试封装/解封装...\n");
    uint8_t *ciphertext = malloc(kem->length_ciphertext);
    uint8_t *shared_secret_enc = malloc(kem->length_shared_secret);
    uint8_t *shared_secret_dec = malloc(kem->length_shared_secret);

    if (ciphertext == NULL || shared_secret_enc == NULL || shared_secret_dec == NULL) {
        fprintf(stderr, "      ❌ 内存分配失败\n");
        goto cleanup;
    }

    // 封装
    if (OQS_KEM_encaps(kem, ciphertext, shared_secret_enc, public_key) != OQS_SUCCESS) {
        fprintf(stderr, "      ❌ 封装失败\n");
        goto cleanup;
    }
    printf("      ✅ 封装成功\n");

    // 解封装
    if (OQS_KEM_decaps(kem, shared_secret_dec, ciphertext, secret_key) != OQS_SUCCESS) {
        fprintf(stderr, "      ❌ 解封装失败\n");
        goto cleanup;
    }
    printf("      ✅ 解封装成功\n");

    // 验证共享密钥一致
    if (memcmp(shared_secret_enc, shared_secret_dec, kem->length_shared_secret) != 0) {
        fprintf(stderr, "      ❌ 共享密钥不匹配\n");
        goto cleanup;
    }
    printf("      ✅ 共享密钥匹配\n\n");

    printf("======================================\n");
    printf("  ✅ 所有测试通过！\n");
    printf("  飞腾派环境配置成功！\n");
    printf("  可以开始编译完整PQ-Tor代码！\n");
    printf("======================================\n");

cleanup:
    free(public_key);
    free(secret_key);
    free(ciphertext);
    free(shared_secret_enc);
    free(shared_secret_dec);
    OQS_KEM_free(kem);

    return 0;
}
