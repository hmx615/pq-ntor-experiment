/**
 * @file benchmark_classic_ntor.c
 * @brief Classic NTOR (X25519) 性能基准测试
 *
 * 用于与PQ-NTOR对比，使用相同的测试框架
 */

#define _POSIX_C_SOURCE 199309L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/hmac.h>

// X25519参数
#define X25519_KEY_SIZE 32
#define ONIONSKIN_LEN 52  // 32 + 20
#define REPLY_LEN 64      // 32 + 32

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

// 统计结构
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
    for (int i = 0; i < count; i++) {
        sum += times[i];
    }
    stats->avg_us = sum / count;

    double var_sum = 0;
    for (int i = 0; i < count; i++) {
        double diff = times[i] - stats->avg_us;
        var_sum += diff * diff;
    }
    stats->std_dev_us = sqrt(var_sum / count);
}

// 简化的X25519密钥生成（仅生成EVP_PKEY）
static EVP_PKEY* x25519_keygen_fast() {
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
    if (!ctx) return NULL;

    if (EVP_PKEY_keygen_init(ctx) <= 0) {
        EVP_PKEY_CTX_free(ctx);
        return NULL;
    }

    EVP_PKEY *pkey = NULL;
    if (EVP_PKEY_keygen(ctx, &pkey) <= 0) {
        EVP_PKEY_CTX_free(ctx);
        return NULL;
    }

    EVP_PKEY_CTX_free(ctx);
    return pkey;
}

// 快速DH计算
static int x25519_dh_fast(EVP_PKEY *pkey, EVP_PKEY *peer, uint8_t *shared) {
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(pkey, NULL);
    if (!ctx || EVP_PKEY_derive_init(ctx) <= 0) {
        if (ctx) EVP_PKEY_CTX_free(ctx);
        return -1;
    }

    if (EVP_PKEY_derive_set_peer(ctx, peer) <= 0) {
        EVP_PKEY_CTX_free(ctx);
        return -1;
    }

    size_t shared_len = X25519_KEY_SIZE;
    if (EVP_PKEY_derive(ctx, shared, &shared_len) <= 0) {
        EVP_PKEY_CTX_free(ctx);
        return -1;
    }

    EVP_PKEY_CTX_free(ctx);
    return 0;
}

// 完整握手测试（优化版）
static int benchmark_full_handshake(double *time_us) {
    bench_timer_t timer;
    uint8_t shared[X25519_KEY_SIZE];
    uint8_t auth[32];

    timer_start(&timer);

    // 1. 客户端生成密钥
    EVP_PKEY *client_pkey = x25519_keygen_fast();
    if (!client_pkey) return -1;

    // 2. 服务器生成密钥
    EVP_PKEY *server_pkey = x25519_keygen_fast();
    if (!server_pkey) {
        EVP_PKEY_free(client_pkey);
        return -1;
    }

    // 3. 客户端计算共享密钥
    if (x25519_dh_fast(client_pkey, server_pkey, shared) != 0) {
        EVP_PKEY_free(client_pkey);
        EVP_PKEY_free(server_pkey);
        return -1;
    }

    // 4. HMAC认证
    unsigned int auth_len = 32;
    HMAC(EVP_sha256(), shared, X25519_KEY_SIZE, (uint8_t*)"test", 4, auth, &auth_len);

    *time_us = timer_end_us(&timer);

    EVP_PKEY_free(client_pkey);
    EVP_PKEY_free(server_pkey);
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
    printf("Classic NTOR (X25519) Performance Benchmark\n");
    printf("======================================================================\n");
    printf("Algorithm:     X25519 + HMAC-SHA256\n");
    printf("Iterations:    %d (with %d warmup)\n", iterations, warmup);
    printf("======================================================================\n\n");

    printf("Warming up...\n");
    for (int i = 0; i < warmup; i++) {
        double time_us;
        if (benchmark_full_handshake(&time_us) != 0) {
            fprintf(stderr, "Warmup failed at iteration %d\n", i);
            return 1;
        }
    }

    // 分配时间数组
    double *times = malloc(iterations * sizeof(double));
    if (!times) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    printf("\nBenchmarking: Full handshake...\n");

    int successful = 0;
    for (int i = 0; i < iterations; i++) {
        if (benchmark_full_handshake(&times[successful]) == 0) {
            successful++;
        }

        if ((i + 1) % 100 == 0) {
            printf("  Progress: %d/%d\r", i + 1, iterations);
            fflush(stdout);
        }
    }
    printf("  Progress: %d/%d\n", successful, iterations);

    if (successful == 0) {
        fprintf(stderr, "All iterations failed!\n");
        free(times);
        return 1;
    }

    // 计算统计
    stats_t stats;
    compute_stats(times, successful, &stats);

    printf("\nFull handshake (X25519 + HMAC):\n");
    printf("  avg=  %7.2f μs  median=%7.2f μs  min=%7.2f μs  max=%7.2f μs  stddev=%6.2f μs\n",
           stats.avg_us, stats.median_us, stats.min_us, stats.max_us, stats.std_dev_us);

    printf("\n======================================================================\n");
    printf("Summary (in milliseconds)\n");
    printf("======================================================================\n");
    printf("Operation                      Avg (ms)   Median (ms)   Min (ms)   Max (ms)\n");
    printf("----------------------------------------------------------------------\n");
    printf("FULL HANDSHAKE (total)         %8.3f    %8.3f      %8.3f   %8.3f\n",
           stats.avg_us / 1000.0, stats.median_us / 1000.0,
           stats.min_us / 1000.0, stats.max_us / 1000.0);
    printf("======================================================================\n\n");

    printf("✅ Benchmark completed successfully!\n");
    printf("======================================================================\n\n");

    free(times);
    return 0;
}
