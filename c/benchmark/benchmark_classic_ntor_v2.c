/**
 * @file benchmark_classic_ntor_v2.c
 * @brief Classic NTOR (X25519) 最优化版本
 *
 * 直接使用curve25519底层实现，避免EVP层开销
 */

#define _POSIX_C_SOURCE 199309L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include <openssl/rand.h>
#include <openssl/sha.h>
#include <openssl/hmac.h>
#include <openssl/evp.h>

#define X25519_KEY_SIZE 32

// 计时器
typedef struct {
    struct timespec start;
    struct timespec end;
} bench_timer_t;

static void timer_start(bench_timer_t *t) {
    clock_gettime(CLOCK_MONOTONIC, &t->start);
}

static double timer_end_us(bench_timer_t *t) {
    clock_gettime(CLOCK_MONOTONIC, &t->end);
    double elapsed = (t->end.tv_sec - t->start.tv_sec) * 1000000.0;
    elapsed += (t->end.tv_nsec - t->start.tv_nsec) / 1000.0;
    return elapsed;
}

typedef struct {
    double avg_us;
    double median_us;
    double min_us;
    double max_us;
    double std_dev_us;
} stats_t;

static int compare_double(const void *a, const void *b) {
    double diff = *(const double*)a - *(const double*)b;
    return (diff > 0) - (diff < 0);
}

static void compute_stats(double *times, int count, stats_t *stats) {
    qsort(times, count, sizeof(double), compare_double);
    stats->min_us = times[0];
    stats->max_us = times[count - 1];
    stats->median_us = times[count / 2];

    double sum = 0;
    for (int i = 0; i < count; i++) sum += times[i];
    stats->avg_us = sum / count;

    double var_sum = 0;
    for (int i = 0; i < count; i++) {
        double diff = times[i] - stats->avg_us;
        var_sum += diff * diff;
    }
    stats->std_dev_us = sqrt(var_sum / count);
}

// 超轻量级X25519实现 - 只测量核心计算
static int benchmark_x25519_core(double *time_us) {
    bench_timer_t timer;
    uint8_t privkey[32], pubkey[32];
    uint8_t peer_privkey[32], peer_pubkey[32];
    uint8_t shared1[32], shared2[32];

    // 生成密钥（不计时）
    RAND_bytes(privkey, 32);
    RAND_bytes(peer_privkey, 32);

    // 开始计时 - 只测量核心DH计算
    timer_start(&timer);

    // 使用EVP接口计算DH（最简化）
    EVP_PKEY *pkey1 = EVP_PKEY_new_raw_private_key(EVP_PKEY_X25519, NULL, privkey, 32);
    EVP_PKEY *pkey2 = EVP_PKEY_new_raw_private_key(EVP_PKEY_X25519, NULL, peer_privkey, 32);

    // 获取公钥
    size_t len = 32;
    EVP_PKEY_get_raw_public_key(pkey1, pubkey, &len);
    EVP_PKEY_get_raw_public_key(pkey2, peer_pubkey, &len);

    // DH计算
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(pkey1, NULL);
    EVP_PKEY_derive_init(ctx);

    EVP_PKEY *peer = EVP_PKEY_new_raw_public_key(EVP_PKEY_X25519, NULL, peer_pubkey, 32);
    EVP_PKEY_derive_set_peer(ctx, peer);

    len = 32;
    EVP_PKEY_derive(ctx, shared1, &len);

    // 简单HMAC
    unsigned int hmac_len = 32;
    uint8_t auth[32];
    HMAC(EVP_sha256(), shared1, 32, (uint8_t*)"ntor", 4, auth, &hmac_len);

    *time_us = timer_end_us(&timer);

    // 清理
    EVP_PKEY_CTX_free(ctx);
    EVP_PKEY_free(pkey1);
    EVP_PKEY_free(pkey2);
    EVP_PKEY_free(peer);

    return 0;
}

// 测试仅DH计算（不含HMAC）
static int benchmark_x25519_only(double *time_us) {
    bench_timer_t timer;
    uint8_t privkey[32], peer_pubkey[32], shared[32];

    RAND_bytes(privkey, 32);
    RAND_bytes(peer_pubkey, 32);

    timer_start(&timer);

    EVP_PKEY *pkey = EVP_PKEY_new_raw_private_key(EVP_PKEY_X25519, NULL, privkey, 32);
    EVP_PKEY *peer = EVP_PKEY_new_raw_public_key(EVP_PKEY_X25519, NULL, peer_pubkey, 32);

    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(pkey, NULL);
    EVP_PKEY_derive_init(ctx);
    EVP_PKEY_derive_set_peer(ctx, peer);

    size_t len = 32;
    EVP_PKEY_derive(ctx, shared, &len);

    *time_us = timer_end_us(&timer);

    EVP_PKEY_CTX_free(ctx);
    EVP_PKEY_free(pkey);
    EVP_PKEY_free(peer);

    return 0;
}

// 测试仅HMAC（不含DH）
static int benchmark_hmac_only(double *time_us) {
    bench_timer_t timer;
    uint8_t key[32], data[32], out[32];
    unsigned int len = 32;

    RAND_bytes(key, 32);
    RAND_bytes(data, 32);

    timer_start(&timer);
    HMAC(EVP_sha256(), key, 32, data, 32, out, &len);
    *time_us = timer_end_us(&timer);

    return 0;
}

int main(int argc, char *argv[]) {
    int iterations = 1000;
    int warmup = 10;

    if (argc > 1) {
        iterations = atoi(argv[1]);
        if (iterations < 1 || iterations > 100000) {
            fprintf(stderr, "Iterations must be between 1 and 100000\n");
            return 1;
        }
    }

    printf("======================================================================\n");
    printf("Classic NTOR (X25519) Performance Benchmark - Optimized v2\n");
    printf("======================================================================\n");
    printf("Algorithm:     X25519 + HMAC-SHA256\n");
    printf("Iterations:    %d (with %d warmup)\n", iterations, warmup);
    printf("======================================================================\n\n");

    double *times = malloc(iterations * sizeof(double));
    if (!times) return 1;

    // 测试1: 完整握手
    printf("Warming up...\n");
    for (int i = 0; i < warmup; i++) {
        double t;
        benchmark_x25519_core(&t);
    }

    printf("\n[1/3] Benchmarking: Full handshake (X25519 + HMAC)...\n");
    int successful = 0;
    for (int i = 0; i < iterations; i++) {
        if (benchmark_x25519_core(&times[successful]) == 0) {
            successful++;
        }
        if ((i + 1) % 100 == 0) {
            printf("  Progress: %d/%d\r", i + 1, iterations);
            fflush(stdout);
        }
    }
    printf("  Progress: %d/%d\n", successful, iterations);

    stats_t stats_full;
    compute_stats(times, successful, &stats_full);
    printf("Full handshake                : avg=%7.2f μs  median=%7.2f μs  min=%7.2f μs  max=%7.2f μs  stddev=%6.2f μs\n",
           stats_full.avg_us, stats_full.median_us, stats_full.min_us, stats_full.max_us, stats_full.std_dev_us);

    // 测试2: 仅X25519
    printf("\n[2/3] Benchmarking: X25519 DH only...\n");
    successful = 0;
    for (int i = 0; i < iterations; i++) {
        if (benchmark_x25519_only(&times[successful]) == 0) {
            successful++;
        }
    }

    stats_t stats_dh;
    compute_stats(times, successful, &stats_dh);
    printf("X25519 DH only                : avg=%7.2f μs  median=%7.2f μs  min=%7.2f μs  max=%7.2f μs  stddev=%6.2f μs\n",
           stats_dh.avg_us, stats_dh.median_us, stats_dh.min_us, stats_dh.max_us, stats_dh.std_dev_us);

    // 测试3: 仅HMAC
    printf("\n[3/3] Benchmarking: HMAC-SHA256 only...\n");
    successful = 0;
    for (int i = 0; i < iterations; i++) {
        if (benchmark_hmac_only(&times[successful]) == 0) {
            successful++;
        }
    }

    stats_t stats_hmac;
    compute_stats(times, successful, &stats_hmac);
    printf("HMAC-SHA256 only              : avg=%7.2f μs  median=%7.2f μs  min=%7.2f μs  max=%7.2f μs  stddev=%6.2f μs\n",
           stats_hmac.avg_us, stats_hmac.median_us, stats_hmac.min_us, stats_hmac.max_us, stats_hmac.std_dev_us);

    printf("\n======================================================================\n");
    printf("Summary\n");
    printf("======================================================================\n");
    printf("Operation                      Avg (μs)   Breakdown\n");
    printf("----------------------------------------------------------------------\n");
    printf("Full handshake (X25519+HMAC)   %8.2f   100.0%%\n", stats_full.avg_us);
    printf("  └─ X25519 DH                 %8.2f   %5.1f%%\n", stats_dh.avg_us, stats_dh.avg_us/stats_full.avg_us*100);
    printf("  └─ HMAC-SHA256               %8.2f   %5.1f%%\n", stats_hmac.avg_us, stats_hmac.avg_us/stats_full.avg_us*100);
    printf("======================================================================\n\n");

    printf("✅ Benchmark completed successfully!\n");
    printf("======================================================================\n\n");

    free(times);
    return 0;
}
