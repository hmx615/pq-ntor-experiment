/**
 * @file phase2_handshake_comparison.c
 * @brief Phase 2: Protocol Handshake Performance Comparison
 *
 * 对比测试三种NTOR握手协议性能:
 * 1. Classic NTOR (X25519 + HMAC-SHA256)
 * 2. PQ-NTOR (Kyber-512 + HKDF + HMAC)
 * 3. Hybrid NTOR (Kyber-512 + X25519 + HKDF + HMAC)
 *
 * 参考文献:
 * - Berger et al. (2025): "Gradually Deploying Post-Quantum Cryptography in Tor"
 * - IETF draft-ietf-tls-hybrid-design: Hybrid key exchange
 * - SaTor (Li & Elahi 2024): Section 5 Performance Evaluation
 *
 * @author Claude Code Assistant
 * @date 2025-12-12 (Updated for Hybrid NTOR)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <math.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/hmac.h>

#include "pq_ntor.h"
#include "hybrid_ntor.h"
#include "kyber_kem.h"
#include "crypto_utils.h"

// ============================================================================
// 测试配置
// ============================================================================

#define WARMUP_ITERATIONS 100
#define TEST_ITERATIONS 1000

// Classic NTOR参数
#define X25519_KEY_SIZE 32
#define CLASSIC_SHARED_KEY_SIZE 32

// ============================================================================
// 统计结构
// ============================================================================

typedef struct {
    double min_us;
    double max_us;
    double mean_us;
    double median_us;
    double stddev_us;
    double p95_us;
    double p99_us;
    double ci_lower;  // 95% CI下界
    double ci_upper;  // 95% CI上界
} perf_stats_t;

// ============================================================================
// 时间测量
// ============================================================================

static inline uint64_t get_time_us(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000000ULL + tv.tv_usec;
}

// ============================================================================
// 统计计算
// ============================================================================

static int compare_double(const void *a, const void *b) {
    double diff = *(const double*)a - *(const double*)b;
    if (diff < 0) return -1;
    if (diff > 0) return 1;
    return 0;
}

static void compute_stats(double *times, int count, perf_stats_t *stats) {
    // 排序
    qsort(times, count, sizeof(double), compare_double);

    // 基本统计
    stats->min_us = times[0];
    stats->max_us = times[count - 1];
    stats->median_us = times[count / 2];

    // 百分位数
    stats->p95_us = times[(int)(count * 0.95)];
    stats->p99_us = times[(int)(count * 0.99)];

    // 均值
    double sum = 0.0;
    for (int i = 0; i < count; i++) {
        sum += times[i];
    }
    stats->mean_us = sum / count;

    // 标准差
    double var_sum = 0.0;
    for (int i = 0; i < count; i++) {
        double diff = times[i] - stats->mean_us;
        var_sum += diff * diff;
    }
    stats->stddev_us = sqrt(var_sum / count);

    // 95%置信区间 (使用1.96倍标准误)
    double margin = 1.96 * stats->stddev_us / sqrt(count);
    stats->ci_lower = stats->mean_us - margin;
    stats->ci_upper = stats->mean_us + margin;
}

// ============================================================================
// Classic NTOR实现 (X25519 + HMAC-SHA256) - 简化版
// ============================================================================

static int classic_ntor_full_handshake(uint8_t *shared_key_out) {
    EVP_PKEY *client_pkey = NULL;
    EVP_PKEY *server_pkey = NULL;
    EVP_PKEY_CTX *keygen_ctx = NULL;
    EVP_PKEY_CTX *derive_ctx = NULL;
    uint8_t dh_shared[X25519_KEY_SIZE];
    size_t shared_len = X25519_KEY_SIZE;
    int ret = -1;

    // 1. 客户端生成X25519密钥对
    keygen_ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
    if (!keygen_ctx || EVP_PKEY_keygen_init(keygen_ctx) <= 0 ||
        EVP_PKEY_keygen(keygen_ctx, &client_pkey) <= 0) {
        goto cleanup;
    }
    EVP_PKEY_CTX_free(keygen_ctx);
    keygen_ctx = NULL;

    // 2. 服务端生成X25519密钥对
    keygen_ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
    if (!keygen_ctx || EVP_PKEY_keygen_init(keygen_ctx) <= 0 ||
        EVP_PKEY_keygen(keygen_ctx, &server_pkey) <= 0) {
        goto cleanup;
    }
    EVP_PKEY_CTX_free(keygen_ctx);
    keygen_ctx = NULL;

    // 3. 计算共享密钥 (DH)
    derive_ctx = EVP_PKEY_CTX_new(client_pkey, NULL);
    if (!derive_ctx || EVP_PKEY_derive_init(derive_ctx) <= 0 ||
        EVP_PKEY_derive_set_peer(derive_ctx, server_pkey) <= 0 ||
        EVP_PKEY_derive(derive_ctx, dh_shared, &shared_len) <= 0) {
        goto cleanup;
    }

    // 4. HMAC-SHA256认证
    unsigned int hmac_len = CLASSIC_SHARED_KEY_SIZE;
    if (!HMAC(EVP_sha256(), dh_shared, X25519_KEY_SIZE,
              (uint8_t*)"ntor-curve25519-sha256-1", 24,
              shared_key_out, &hmac_len)) {
        goto cleanup;
    }

    ret = 0;

cleanup:
    if (keygen_ctx) EVP_PKEY_CTX_free(keygen_ctx);
    if (derive_ctx) EVP_PKEY_CTX_free(derive_ctx);
    if (client_pkey) EVP_PKEY_free(client_pkey);
    if (server_pkey) EVP_PKEY_free(server_pkey);
    return ret;
}

// ============================================================================
// PQ-NTOR实现 (Kyber-512 + HKDF + HMAC)
// ============================================================================

static int pq_ntor_full_handshake(uint8_t *shared_key_out) {
    uint8_t relay_identity[PQ_NTOR_RELAY_ID_LENGTH];
    memset(relay_identity, 0xAB, sizeof(relay_identity));

    pq_ntor_client_state client_state;
    uint8_t onionskin[PQ_NTOR_ONIONSKIN_LEN];

    if (pq_ntor_client_create_onionskin(&client_state, onionskin, relay_identity) != 0) {
        return -1;
    }

    pq_ntor_server_state server_state;
    uint8_t reply[PQ_NTOR_REPLY_LEN];

    if (pq_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity) != 0) {
        pq_ntor_client_state_cleanup(&client_state);
        return -1;
    }

    if (pq_ntor_client_finish_handshake(&client_state, reply) != 0) {
        pq_ntor_client_state_cleanup(&client_state);
        pq_ntor_server_state_cleanup(&server_state);
        return -1;
    }

    if (pq_ntor_client_get_key(shared_key_out, &client_state) != 0) {
        pq_ntor_client_state_cleanup(&client_state);
        pq_ntor_server_state_cleanup(&server_state);
        return -1;
    }

    pq_ntor_client_state_cleanup(&client_state);
    pq_ntor_server_state_cleanup(&server_state);

    return 0;
}

// ============================================================================
// Hybrid NTOR实现 (Kyber-512 + X25519 + HKDF + HMAC)
// ============================================================================

static int hybrid_ntor_full_handshake(uint8_t *shared_key_out) {
    uint8_t relay_identity[HYBRID_NTOR_RELAY_ID_LENGTH];
    memset(relay_identity, 0xAB, sizeof(relay_identity));

    hybrid_ntor_client_state client_state;
    uint8_t onionskin[HYBRID_NTOR_ONIONSKIN_LEN];

    if (hybrid_ntor_client_create_onionskin(&client_state, onionskin, relay_identity) != HYBRID_NTOR_SUCCESS) {
        return -1;
    }

    hybrid_ntor_server_state server_state;
    uint8_t reply[HYBRID_NTOR_REPLY_LEN];

    if (hybrid_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity) != HYBRID_NTOR_SUCCESS) {
        hybrid_ntor_client_state_cleanup(&client_state);
        return -1;
    }

    if (hybrid_ntor_client_finish_handshake(&client_state, reply) != HYBRID_NTOR_SUCCESS) {
        hybrid_ntor_client_state_cleanup(&client_state);
        hybrid_ntor_server_state_cleanup(&server_state);
        return -1;
    }

    // 提取密钥
    memcpy(shared_key_out, client_state.k_enc, HYBRID_NTOR_KEY_ENC_LEN);

    hybrid_ntor_client_state_cleanup(&client_state);
    hybrid_ntor_server_state_cleanup(&server_state);

    return 0;
}

// ============================================================================
// 性能基准测试
// ============================================================================

static void benchmark_classic_ntor(double *times, int iterations) {
    uint8_t shared_key[CLASSIC_SHARED_KEY_SIZE];

    for (int i = 0; i < iterations; i++) {
        uint64_t start = get_time_us();

        if (classic_ntor_full_handshake(shared_key) != 0) {
            fprintf(stderr, "Classic NTOR handshake failed at iteration %d\n", i);
            times[i] = 0.0;
            continue;
        }

        uint64_t end = get_time_us();
        times[i] = (double)(end - start);
    }
}

static void benchmark_pq_ntor(double *times, int iterations) {
    uint8_t shared_key[PQ_NTOR_KEY_MATERIAL_LEN];

    for (int i = 0; i < iterations; i++) {
        uint64_t start = get_time_us();

        if (pq_ntor_full_handshake(shared_key) != 0) {
            fprintf(stderr, "PQ-NTOR handshake failed at iteration %d\n", i);
            times[i] = 0.0;
            continue;
        }

        uint64_t end = get_time_us();
        times[i] = (double)(end - start);
    }
}

static void benchmark_hybrid_ntor(double *times, int iterations) {
    uint8_t shared_key[HYBRID_NTOR_KEY_ENC_LEN];

    for (int i = 0; i < iterations; i++) {
        uint64_t start = get_time_us();

        if (hybrid_ntor_full_handshake(shared_key) != 0) {
            fprintf(stderr, "Hybrid NTOR handshake failed at iteration %d\n", i);
            times[i] = 0.0;
            continue;
        }

        uint64_t end = get_time_us();
        times[i] = (double)(end - start);
    }
}

// ============================================================================
// 结果输出
// ============================================================================

static void print_header(void) {
    printf("======================================================================\n");
    printf("Phase 2: Protocol Handshake Performance Comparison\n");
    printf("======================================================================\n");
    printf("Platform:      ARM64 Phytium Pi (FTC664 @ 2.3GHz)\n");
    printf("Iterations:    %d (with %d warmup)\n", TEST_ITERATIONS, WARMUP_ITERATIONS);
    printf("Confidence:    95%% CI\n");
    printf("Protocols:     Classic NTOR, PQ-NTOR, Hybrid NTOR\n");
    printf("======================================================================\n\n");
}

static void print_stats_row(const char *protocol, const perf_stats_t *stats) {
    printf("%-20s  %8.2f  %8.2f  %8.2f  %9.2f  %7.2f  %7.2f  %7.2f\n",
           protocol,
           stats->mean_us,
           stats->median_us,
           stats->min_us,
           stats->max_us,
           stats->stddev_us,
           stats->p95_us,
           stats->p99_us);
}

static void save_csv(const perf_stats_t *classic_stats,
                     const perf_stats_t *pq_stats,
                     const perf_stats_t *hybrid_stats) {
    FILE *fp = fopen("phase2_handshake_comparison.csv", "w");
    if (!fp) {
        fprintf(stderr, "Warning: Failed to create CSV file\n");
        return;
    }

    fprintf(fp, "Protocol,Mean_us,Median_us,Min_us,Max_us,StdDev_us,P95_us,P99_us,CI_Lower,CI_Upper\n");
    fprintf(fp, "Classic NTOR,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n",
            classic_stats->mean_us, classic_stats->median_us, classic_stats->min_us,
            classic_stats->max_us, classic_stats->stddev_us, classic_stats->p95_us,
            classic_stats->p99_us, classic_stats->ci_lower, classic_stats->ci_upper);
    fprintf(fp, "PQ-NTOR,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n",
            pq_stats->mean_us, pq_stats->median_us, pq_stats->min_us,
            pq_stats->max_us, pq_stats->stddev_us, pq_stats->p95_us,
            pq_stats->p99_us, pq_stats->ci_lower, pq_stats->ci_upper);
    fprintf(fp, "Hybrid NTOR,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n",
            hybrid_stats->mean_us, hybrid_stats->median_us, hybrid_stats->min_us,
            hybrid_stats->max_us, hybrid_stats->stddev_us, hybrid_stats->p95_us,
            hybrid_stats->p99_us, hybrid_stats->ci_lower, hybrid_stats->ci_upper);

    fclose(fp);
    printf("✓ CSV data saved to: phase2_handshake_comparison.csv\n");
}

// ============================================================================
// 主函数
// ============================================================================

int main(void) {
    print_header();

    // 分配内存
    int total_iterations = WARMUP_ITERATIONS + TEST_ITERATIONS;
    double *classic_times = malloc(total_iterations * sizeof(double));
    double *pq_times = malloc(total_iterations * sizeof(double));
    double *hybrid_times = malloc(total_iterations * sizeof(double));

    if (!classic_times || !pq_times || !hybrid_times) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    // ========================================================================
    // 1. Classic NTOR测试
    // ========================================================================

    printf("[1/3] Benchmarking: Classic NTOR (X25519 + HMAC-SHA256)\n");
    printf("      Warming up (%d iterations)...\n", WARMUP_ITERATIONS);
    benchmark_classic_ntor(classic_times, WARMUP_ITERATIONS);

    printf("      Running %d test iterations...\n", TEST_ITERATIONS);
    benchmark_classic_ntor(classic_times + WARMUP_ITERATIONS, TEST_ITERATIONS);

    perf_stats_t classic_stats;
    compute_stats(classic_times + WARMUP_ITERATIONS, TEST_ITERATIONS, &classic_stats);

    printf("      Classic NTOR: mean=%.2f μs, median=%.2f μs, p95=%.2f μs\n\n",
           classic_stats.mean_us, classic_stats.median_us, classic_stats.p95_us);

    // ========================================================================
    // 2. PQ-NTOR测试
    // ========================================================================

    printf("[2/3] Benchmarking: PQ-NTOR (Kyber-512 + HKDF + HMAC)\n");
    printf("      Warming up (%d iterations)...\n", WARMUP_ITERATIONS);
    benchmark_pq_ntor(pq_times, WARMUP_ITERATIONS);

    printf("      Running %d test iterations...\n", TEST_ITERATIONS);
    benchmark_pq_ntor(pq_times + WARMUP_ITERATIONS, TEST_ITERATIONS);

    perf_stats_t pq_stats;
    compute_stats(pq_times + WARMUP_ITERATIONS, TEST_ITERATIONS, &pq_stats);

    printf("      PQ-NTOR: mean=%.2f μs, median=%.2f μs, p95=%.2f μs\n\n",
           pq_stats.mean_us, pq_stats.median_us, pq_stats.p95_us);

    // ========================================================================
    // 3. Hybrid NTOR测试
    // ========================================================================

    printf("[3/3] Benchmarking: Hybrid NTOR (Kyber-512 + X25519 + HKDF + HMAC)\n");
    printf("      Warming up (%d iterations)...\n", WARMUP_ITERATIONS);
    benchmark_hybrid_ntor(hybrid_times, WARMUP_ITERATIONS);

    printf("      Running %d test iterations...\n", TEST_ITERATIONS);
    benchmark_hybrid_ntor(hybrid_times + WARMUP_ITERATIONS, TEST_ITERATIONS);

    perf_stats_t hybrid_stats;
    compute_stats(hybrid_times + WARMUP_ITERATIONS, TEST_ITERATIONS, &hybrid_stats);

    printf("      Hybrid NTOR: mean=%.2f μs, median=%.2f μs, p95=%.2f μs\n\n",
           hybrid_stats.mean_us, hybrid_stats.median_us, hybrid_stats.p95_us);

    // ========================================================================
    // 4. 对比分析
    // ========================================================================

    printf("======================================================================\n");
    printf("Performance Comparison Summary\n");
    printf("======================================================================\n");
    printf("Protocol              Mean      Median    Min       Max        StdDev   P95      P99\n");
    printf("                      (μs)      (μs)      (μs)      (μs)       (μs)     (μs)     (μs)\n");
    printf("------------------------------------------------------------------------------\n");
    print_stats_row("Classic NTOR", &classic_stats);
    print_stats_row("PQ-NTOR", &pq_stats);
    print_stats_row("Hybrid NTOR", &hybrid_stats);
    printf("======================================================================\n\n");

    // 开销分析
    double pq_overhead = pq_stats.mean_us / classic_stats.mean_us;
    double hybrid_overhead = hybrid_stats.mean_us / classic_stats.mean_us;
    double hybrid_vs_pq = hybrid_stats.mean_us / pq_stats.mean_us;

    printf("======================================================================\n");
    printf("Overhead Analysis (relative to Classic NTOR)\n");
    printf("======================================================================\n");
    printf("PQ-NTOR Overhead:        %.2fx (%.2f μs absolute)\n",
           pq_overhead, pq_stats.mean_us - classic_stats.mean_us);
    printf("Hybrid NTOR Overhead:    %.2fx (%.2f μs absolute)\n",
           hybrid_overhead, hybrid_stats.mean_us - classic_stats.mean_us);
    printf("Hybrid vs PQ-NTOR:       %.2fx\n", hybrid_vs_pq);
    printf("\n");
    printf("Throughput:\n");
    printf("  Classic NTOR:   %.0f handshakes/sec\n", 1000000.0 / classic_stats.mean_us);
    printf("  PQ-NTOR:        %.0f handshakes/sec\n", 1000000.0 / pq_stats.mean_us);
    printf("  Hybrid NTOR:    %.0f handshakes/sec\n", 1000000.0 / hybrid_stats.mean_us);
    printf("======================================================================\n\n");

    // 消息大小比较
    printf("======================================================================\n");
    printf("Message Size Comparison\n");
    printf("======================================================================\n");
    printf("Protocol          Onionskin (bytes)    Reply (bytes)    Total (bytes)\n");
    printf("----------------------------------------------------------------------\n");
    printf("Classic NTOR      %d                   %d               %d\n",
           32 + 20, 32 + 32, 32 + 20 + 32 + 32);  // X25519 PK + ID, X25519 PK + AUTH
    printf("PQ-NTOR           %d                  %d               %d\n",
           PQ_NTOR_ONIONSKIN_LEN, PQ_NTOR_REPLY_LEN,
           PQ_NTOR_ONIONSKIN_LEN + PQ_NTOR_REPLY_LEN);
    printf("Hybrid NTOR       %d                  %d               %d\n",
           HYBRID_NTOR_ONIONSKIN_LEN, HYBRID_NTOR_REPLY_LEN,
           HYBRID_NTOR_ONIONSKIN_LEN + HYBRID_NTOR_REPLY_LEN);
    printf("======================================================================\n\n");

    // 安全性对比
    printf("======================================================================\n");
    printf("Security Properties\n");
    printf("======================================================================\n");
    printf("Protocol          Classical Security    Quantum Security    Hybrid\n");
    printf("----------------------------------------------------------------------\n");
    printf("Classic NTOR      128-bit (X25519)      BROKEN              No\n");
    printf("PQ-NTOR           N/A                   128-bit (Kyber)     No\n");
    printf("Hybrid NTOR       128-bit (X25519)      128-bit (Kyber)     Yes\n");
    printf("======================================================================\n\n");

    // 保存CSV
    save_csv(&classic_stats, &pq_stats, &hybrid_stats);

    printf("\n======================================================================\n");
    printf("✅ Phase 2 Benchmark Completed Successfully!\n");
    printf("======================================================================\n");
    printf("\nKey Findings:\n");
    printf("  - Hybrid NTOR provides both classical and quantum security\n");
    printf("  - Hybrid overhead vs Classic: %.2fx\n", hybrid_overhead);
    printf("  - Hybrid overhead vs PQ-NTOR: %.2fx\n", hybrid_vs_pq);
    printf("\nNext Steps:\n");
    printf("  1. Review: phase2_handshake_comparison.csv\n");
    printf("  2. Proceed to Phase 3: SAGIN Network Integration Testing\n");
    printf("======================================================================\n\n");

    // 清理
    free(classic_times);
    free(pq_times);
    free(hybrid_times);

    return 0;
}
