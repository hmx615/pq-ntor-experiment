/**
 * @file kyber_kem.c
 * @brief Kyber KEM 封装实现（基于 liboqs）
 */

#include "kyber_kem.h"
#include <oqs/oqs.h>
#include <stdio.h>
#include <string.h>

// 全局 KEM 实例（延迟初始化）
static OQS_KEM *kem_instance = NULL;

/**
 * @brief 初始化 Kyber KEM 实例
 */
static int kyber_init(void) {
    if (kem_instance != NULL) {
        return KYBER_SUCCESS; // 已初始化
    }

    kem_instance = OQS_KEM_new(KYBER_ALGORITHM_NAME);
    if (kem_instance == NULL) {
        fprintf(stderr, "[Kyber] Error: Failed to initialize %s\n", KYBER_ALGORITHM_NAME);
        return KYBER_ERROR;
    }

    // 验证参数大小
    if (kem_instance->length_public_key != KYBER_PUBLIC_KEY_BYTES ||
        kem_instance->length_secret_key != KYBER_SECRET_KEY_BYTES ||
        kem_instance->length_ciphertext != KYBER_CIPHERTEXT_BYTES ||
        kem_instance->length_shared_secret != KYBER_SHARED_SECRET_BYTES) {
        fprintf(stderr, "[Kyber] Error: Parameter mismatch!\n");
        fprintf(stderr, "  Expected: pk=%zu, sk=%zu, ct=%zu, ss=%zu\n",
                (size_t)KYBER_PUBLIC_KEY_BYTES,
                (size_t)KYBER_SECRET_KEY_BYTES,
                (size_t)KYBER_CIPHERTEXT_BYTES,
                (size_t)KYBER_SHARED_SECRET_BYTES);
        fprintf(stderr, "  Got:      pk=%zu, sk=%zu, ct=%zu, ss=%zu\n",
                kem_instance->length_public_key,
                kem_instance->length_secret_key,
                kem_instance->length_ciphertext,
                kem_instance->length_shared_secret);
        OQS_KEM_free(kem_instance);
        kem_instance = NULL;
        return KYBER_ERROR;
    }

    return KYBER_SUCCESS;
}

/**
 * @brief 清理 Kyber KEM 实例
 */
void kyber_cleanup(void) {
    if (kem_instance != NULL) {
        OQS_KEM_free(kem_instance);
        kem_instance = NULL;
    }
}

int kyber_keypair(uint8_t *public_key, uint8_t *secret_key) {
    if (public_key == NULL || secret_key == NULL) {
        fprintf(stderr, "[Kyber] Error: NULL pointer in keypair\n");
        return KYBER_ERROR;
    }

    if (kyber_init() != KYBER_SUCCESS) {
        return KYBER_ERROR;
    }

    OQS_STATUS status = OQS_KEM_keypair(kem_instance, public_key, secret_key);
    if (status != OQS_SUCCESS) {
        fprintf(stderr, "[Kyber] Error: Keypair generation failed (status=%d)\n", status);
        return KYBER_ERROR;
    }

    return KYBER_SUCCESS;
}

int kyber_encapsulate(uint8_t *ciphertext,
                      uint8_t *shared_secret,
                      const uint8_t *public_key) {
    if (ciphertext == NULL || shared_secret == NULL || public_key == NULL) {
        fprintf(stderr, "[Kyber] Error: NULL pointer in encapsulate\n");
        return KYBER_ERROR;
    }

    if (kyber_init() != KYBER_SUCCESS) {
        return KYBER_ERROR;
    }

    OQS_STATUS status = OQS_KEM_encaps(kem_instance, ciphertext, shared_secret, public_key);
    if (status != OQS_SUCCESS) {
        fprintf(stderr, "[Kyber] Error: Encapsulation failed (status=%d)\n", status);
        return KYBER_ERROR;
    }

    return KYBER_SUCCESS;
}

int kyber_decapsulate(uint8_t *shared_secret,
                      const uint8_t *ciphertext,
                      const uint8_t *secret_key) {
    if (shared_secret == NULL || ciphertext == NULL || secret_key == NULL) {
        fprintf(stderr, "[Kyber] Error: NULL pointer in decapsulate\n");
        return KYBER_ERROR;
    }

    if (kyber_init() != KYBER_SUCCESS) {
        return KYBER_ERROR;
    }

    OQS_STATUS status = OQS_KEM_decaps(kem_instance, shared_secret, ciphertext, secret_key);
    if (status != OQS_SUCCESS) {
        fprintf(stderr, "[Kyber] Error: Decapsulation failed (status=%d)\n", status);
        return KYBER_ERROR;
    }

    return KYBER_SUCCESS;
}

const char* kyber_get_algorithm_name(void) {
    return KYBER_ALGORITHM_NAME;
}

void kyber_print_parameters(void) {
    printf("=== Kyber Parameters ===\n");
    printf("Algorithm:     %s\n", KYBER_ALGORITHM_NAME);
    printf("Public key:    %d bytes\n", KYBER_PUBLIC_KEY_BYTES);
    printf("Secret key:    %d bytes\n", KYBER_SECRET_KEY_BYTES);
    printf("Ciphertext:    %d bytes\n", KYBER_CIPHERTEXT_BYTES);
    printf("Shared secret: %d bytes\n", KYBER_SHARED_SECRET_BYTES);
    printf("========================\n");
}
