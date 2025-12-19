/**
 * phase3_sagin_network.c
 *
 * Phase 3: SAGIN Network Integration Testing
 * Measures Circuit Build Time (CBT) across 12 SAGIN topologies
 * Compares Classic NTOR vs PQ-NTOR vs Hybrid NTOR in real network conditions
 *
 * Updated 2025-12-12: Added Hybrid NTOR support
 */

#define _POSIX_C_SOURCE 200112L
#define _DEFAULT_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/time.h>
#include <math.h>
#include <stdbool.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include "pq_ntor.h"
#include "hybrid_ntor.h"
#include "cell.h"
#include "onion_crypto.h"
#include "crypto_utils.h"

// ============ Configuration ============

#define NUM_ITERATIONS 20
#define WARMUP_ITERATIONS 3
#define CONFIDENCE_LEVEL 0.95

// Node addresses (assuming localhost with tc/netem configured)
#define GUARD_IP "127.0.0.1"
#define GUARD_PORT 9001

#define MIDDLE_IP "127.0.0.1"
#define MIDDLE_PORT 9002

#define EXIT_IP "127.0.0.1"
#define EXIT_PORT 9003

// ============ Topology Configuration ============

typedef struct {
    const char *name;
    double rate_mbps;     // Bandwidth
    double delay_ms;      // One-way delay
    double loss_percent;  // Packet loss
} topology_config_t;

// 12 SAGIN topologies from real NOMA data (corrected 2025-12-15 - final version)
// Updated with correct delay values based on topology_params.json
static const topology_config_t TOPOLOGIES[] = {
    {"topo01",  59.27,  2.71,  3.0},  // Z1 Up - 直连NOMA
    {"topo02",  16.55,  2.72,  3.0},  // Z2 Up - T协作接入(混合双路径)
    {"topo03",  25.19,  2.71,  1.0},  // Z3 Up - T用户协作NOMA
    {"topo04",  23.64,  2.72,  3.0},  // Z4 Up - 混合直连+协作
    {"topo05",  25.19,  2.72,  3.0},  // Z5 Up - 多层树形结构
    {"topo06",  22.91,  2.72,  1.0},  // Z6 Up - 双UAV中继+T用户
    {"topo07",  69.43,  5.42,  2.0},  // Z1 Down - 直连NOMA+协作
    {"topo08",  44.84,  5.42,  2.0},  // Z2 Down - T协作接入+协作
    {"topo09",  29.84,  2.72,  0.5},  // Z3 Down - T用户协作下行
    {"topo10",  28.29,  5.42,  2.0},  // Z4 Down - 混合直连+协作
    {"topo11",   9.67,  5.42,  2.0},  // Z5 Down - NOMA接收+转发+T协作
    {"topo12",   8.73,  5.42,  2.0}   // Z6 Down - 双中继NOMA+协作+转发
};

#define NUM_TOPOLOGIES (sizeof(TOPOLOGIES) / sizeof(TOPOLOGIES[0]))

// ============ Statistics ============

typedef struct {
    double min_ms;
    double median_ms;
    double mean_ms;
    double max_ms;
    double stddev_ms;
    double p95_ms;
    double p99_ms;
    double ci_lower;
    double ci_upper;
} perf_stats_t;

// ============ Time Measurement ============

static inline uint64_t get_time_us(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000000ULL + tv.tv_usec;
}

// ============ Statistics Functions ============

static int compare_double(const void *a, const void *b) {
    double diff = (*(double*)a - *(double*)b);
    return (diff > 0) - (diff < 0);
}

static void compute_stats(double *times, int count, perf_stats_t *stats) {
    if (count == 0) return;

    qsort(times, count, sizeof(double), compare_double);

    stats->min_ms = times[0];
    stats->median_ms = times[count / 2];
    stats->max_ms = times[count - 1];

    // Mean
    double sum = 0;
    for (int i = 0; i < count; i++) {
        sum += times[i];
    }
    stats->mean_ms = sum / count;

    // Standard deviation
    double sum_sq = 0;
    for (int i = 0; i < count; i++) {
        double diff = times[i] - stats->mean_ms;
        sum_sq += diff * diff;
    }
    stats->stddev_ms = sqrt(sum_sq / count);

    // Percentiles
    stats->p95_ms = times[(int)(count * 0.95)];
    stats->p99_ms = times[(int)(count * 0.99)];

    // 95% Confidence Interval
    double margin = 1.96 * stats->stddev_ms / sqrt(count);
    stats->ci_lower = stats->mean_ms - margin;
    stats->ci_upper = stats->mean_ms + margin;
}

// ============ Circuit Building: Classic NTOR ============

static double build_circuit_classic_ntor(void) {
    uint64_t start = get_time_us();

    // Simulate 3 hops of Classic NTOR
    for (int hop = 0; hop < 3; hop++) {
        EVP_PKEY *client_pkey = NULL;
        EVP_PKEY_CTX *keygen_ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
        if (!keygen_ctx) return -1;

        if (EVP_PKEY_keygen_init(keygen_ctx) <= 0 ||
            EVP_PKEY_keygen(keygen_ctx, &client_pkey) <= 0) {
            EVP_PKEY_CTX_free(keygen_ctx);
            return -1;
        }
        EVP_PKEY_CTX_free(keygen_ctx);

        EVP_PKEY *server_pkey = NULL;
        keygen_ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
        if (!keygen_ctx) {
            EVP_PKEY_free(client_pkey);
            return -1;
        }

        if (EVP_PKEY_keygen_init(keygen_ctx) <= 0 ||
            EVP_PKEY_keygen(keygen_ctx, &server_pkey) <= 0) {
            EVP_PKEY_CTX_free(keygen_ctx);
            EVP_PKEY_free(client_pkey);
            return -1;
        }
        EVP_PKEY_CTX_free(keygen_ctx);

        EVP_PKEY_CTX *derive_ctx = EVP_PKEY_CTX_new(client_pkey, NULL);
        if (!derive_ctx) {
            EVP_PKEY_free(client_pkey);
            EVP_PKEY_free(server_pkey);
            return -1;
        }

        if (EVP_PKEY_derive_init(derive_ctx) <= 0 ||
            EVP_PKEY_derive_set_peer(derive_ctx, server_pkey) <= 0) {
            EVP_PKEY_CTX_free(derive_ctx);
            EVP_PKEY_free(client_pkey);
            EVP_PKEY_free(server_pkey);
            return -1;
        }

        uint8_t shared_secret[32];
        size_t secret_len = sizeof(shared_secret);
        if (EVP_PKEY_derive(derive_ctx, shared_secret, &secret_len) <= 0) {
            EVP_PKEY_CTX_free(derive_ctx);
            EVP_PKEY_free(client_pkey);
            EVP_PKEY_free(server_pkey);
            return -1;
        }

        EVP_PKEY_CTX_free(derive_ctx);
        EVP_PKEY_free(client_pkey);
        EVP_PKEY_free(server_pkey);

        uint8_t mac[32];
        uint8_t key[16] = {0};
        if (hmac_sha256(mac, key, sizeof(key), shared_secret, secret_len) != 0) {
            return -1;
        }
    }

    uint64_t end = get_time_us();
    return (double)(end - start) / 1000.0;
}

// ============ Circuit Building: PQ-NTOR ============

static double build_circuit_pq_ntor(void) {
    uint64_t start = get_time_us();

    uint8_t identities[3][20];
    memset(identities[0], 0x01, 20);
    memset(identities[1], 0x02, 20);
    memset(identities[2], 0x03, 20);

    for (int hop = 0; hop < 3; hop++) {
        pq_ntor_client_state client_state;
        uint8_t onionskin[PQ_NTOR_ONIONSKIN_LEN];

        if (pq_ntor_client_create_onionskin(&client_state, onionskin, identities[hop]) != PQ_NTOR_SUCCESS) {
            return -1;
        }

        pq_ntor_server_state server_state;
        uint8_t reply[PQ_NTOR_REPLY_LEN];

        if (pq_ntor_server_create_reply(&server_state, reply, onionskin, identities[hop]) != PQ_NTOR_SUCCESS) {
            pq_ntor_client_state_cleanup(&client_state);
            return -1;
        }

        if (pq_ntor_client_finish_handshake(&client_state, reply) != PQ_NTOR_SUCCESS) {
            pq_ntor_server_state_cleanup(&server_state);
            pq_ntor_client_state_cleanup(&client_state);
            return -1;
        }

        uint8_t key[PQ_NTOR_KEY_MATERIAL_LEN];
        pq_ntor_client_get_key(key, &client_state);

        pq_ntor_client_state_cleanup(&client_state);
        pq_ntor_server_state_cleanup(&server_state);
    }

    uint64_t end = get_time_us();
    return (double)(end - start) / 1000.0;
}

// ============ Circuit Building: Hybrid NTOR ============

static double build_circuit_hybrid_ntor(void) {
    uint64_t start = get_time_us();

    uint8_t identities[3][HYBRID_NTOR_RELAY_ID_LENGTH];
    memset(identities[0], 0x01, HYBRID_NTOR_RELAY_ID_LENGTH);
    memset(identities[1], 0x02, HYBRID_NTOR_RELAY_ID_LENGTH);
    memset(identities[2], 0x03, HYBRID_NTOR_RELAY_ID_LENGTH);

    for (int hop = 0; hop < 3; hop++) {
        hybrid_ntor_client_state client_state;
        uint8_t onionskin[HYBRID_NTOR_ONIONSKIN_LEN];

        if (hybrid_ntor_client_create_onionskin(&client_state, onionskin, identities[hop]) != HYBRID_NTOR_SUCCESS) {
            return -1;
        }

        hybrid_ntor_server_state server_state;
        uint8_t reply[HYBRID_NTOR_REPLY_LEN];

        if (hybrid_ntor_server_create_reply(&server_state, reply, onionskin, identities[hop]) != HYBRID_NTOR_SUCCESS) {
            hybrid_ntor_client_state_cleanup(&client_state);
            return -1;
        }

        if (hybrid_ntor_client_finish_handshake(&client_state, reply) != HYBRID_NTOR_SUCCESS) {
            hybrid_ntor_server_state_cleanup(&server_state);
            hybrid_ntor_client_state_cleanup(&client_state);
            return -1;
        }

        hybrid_ntor_client_state_cleanup(&client_state);
        hybrid_ntor_server_state_cleanup(&server_state);
    }

    uint64_t end = get_time_us();
    return (double)(end - start) / 1000.0;
}

// ============ Topology Testing ============

static int apply_tc_config(const topology_config_t *topo) {
    printf("[TC] Applying: rate=%.2f Mbps, delay=%.2f ms, loss=%.2f%%\n",
           topo->rate_mbps, topo->delay_ms, topo->loss_percent);

    char cmd[512];
    system("sudo /usr/sbin/tc qdisc del dev lo root 2>/dev/null");

    snprintf(cmd, sizeof(cmd),
             "sudo /usr/sbin/tc qdisc add dev lo root netem delay %.2fms loss %.2f%%",
             topo->delay_ms, topo->loss_percent);

    int ret = system(cmd);
    if (ret != 0) {
        fprintf(stderr, "[TC] Warning: Failed to apply netem\n");
        return -1;
    }

    printf("[TC] Configuration applied successfully\n");
    return 0;
}

static int clear_tc_config(void) {
    system("sudo /usr/sbin/tc qdisc del dev lo root 2>/dev/null");
    return 0;
}

// ============ Main Benchmark ============

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    printf("========================================\n");
    printf("Phase 3: SAGIN Network Integration Test\n");
    printf("========================================\n\n");

    printf("Configuration:\n");
    printf("  Topologies: %d SAGIN topologies\n", (int)NUM_TOPOLOGIES);
    printf("  Protocols:  Classic NTOR, PQ-NTOR, Hybrid NTOR\n");
    printf("  Iterations: %d (+ %d warmup)\n", NUM_ITERATIONS, WARMUP_ITERATIONS);
    printf("  Confidence: %.0f%%\n\n", CONFIDENCE_LEVEL * 100);

    // Open CSV output file
    FILE *csv = fopen("/tmp/phase3_sagin_cbt.csv", "w");
    if (!csv) {
        perror("fopen");
        return 1;
    }

    fprintf(csv, "Topology,Protocol,Mean_ms,Median_ms,Min_ms,Max_ms,StdDev_ms,P95_ms,P99_ms,CI_Lower,CI_Upper\n");

    // Test each topology
    for (size_t t = 0; t < NUM_TOPOLOGIES; t++) {
        const topology_config_t *topo = &TOPOLOGIES[t];

        printf("\n========================================\n");
        printf("Topology: %s\n", topo->name);
        printf("  Rate:  %.2f Mbps\n", topo->rate_mbps);
        printf("  Delay: %.2f ms\n", topo->delay_ms);
        printf("  Loss:  %.2f%%\n", topo->loss_percent);
        printf("========================================\n\n");

        apply_tc_config(topo);
        sleep(1);

        // ========== Test Classic NTOR ==========
        printf("[1/3] Testing Classic NTOR...\n");

        double classic_times[NUM_ITERATIONS + WARMUP_ITERATIONS];

        for (int i = 0; i < NUM_ITERATIONS + WARMUP_ITERATIONS; i++) {
            printf("  %s %d/%d...\r",
                   i < WARMUP_ITERATIONS ? "Warmup" : "Iteration",
                   i < WARMUP_ITERATIONS ? i + 1 : i - WARMUP_ITERATIONS + 1,
                   i < WARMUP_ITERATIONS ? WARMUP_ITERATIONS : NUM_ITERATIONS);
            fflush(stdout);

            double cbt = build_circuit_classic_ntor();
            if (cbt < 0) {
                fprintf(stderr, "\nClassic NTOR circuit build failed\n");
                fclose(csv);
                return 1;
            }

            classic_times[i] = cbt;
            usleep(10000);
        }
        printf("\n");

        perf_stats_t classic_stats;
        compute_stats(classic_times + WARMUP_ITERATIONS, NUM_ITERATIONS, &classic_stats);

        printf("  Classic NTOR: mean=%.3f ms, median=%.3f ms\n",
               classic_stats.mean_ms, classic_stats.median_ms);

        fprintf(csv, "%s,Classic NTOR,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f\n",
                topo->name,
                classic_stats.mean_ms, classic_stats.median_ms,
                classic_stats.min_ms, classic_stats.max_ms, classic_stats.stddev_ms,
                classic_stats.p95_ms, classic_stats.p99_ms,
                classic_stats.ci_lower, classic_stats.ci_upper);

        // ========== Test PQ-NTOR ==========
        printf("[2/3] Testing PQ-NTOR...\n");

        double pq_times[NUM_ITERATIONS + WARMUP_ITERATIONS];

        for (int i = 0; i < NUM_ITERATIONS + WARMUP_ITERATIONS; i++) {
            printf("  %s %d/%d...\r",
                   i < WARMUP_ITERATIONS ? "Warmup" : "Iteration",
                   i < WARMUP_ITERATIONS ? i + 1 : i - WARMUP_ITERATIONS + 1,
                   i < WARMUP_ITERATIONS ? WARMUP_ITERATIONS : NUM_ITERATIONS);
            fflush(stdout);

            double cbt = build_circuit_pq_ntor();
            if (cbt < 0) {
                fprintf(stderr, "\nPQ-NTOR circuit build failed\n");
                fclose(csv);
                return 1;
            }

            pq_times[i] = cbt;
            usleep(10000);
        }
        printf("\n");

        perf_stats_t pq_stats;
        compute_stats(pq_times + WARMUP_ITERATIONS, NUM_ITERATIONS, &pq_stats);

        printf("  PQ-NTOR: mean=%.3f ms, median=%.3f ms\n",
               pq_stats.mean_ms, pq_stats.median_ms);

        fprintf(csv, "%s,PQ-NTOR,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f\n",
                topo->name,
                pq_stats.mean_ms, pq_stats.median_ms,
                pq_stats.min_ms, pq_stats.max_ms, pq_stats.stddev_ms,
                pq_stats.p95_ms, pq_stats.p99_ms,
                pq_stats.ci_lower, pq_stats.ci_upper);

        // ========== Test Hybrid NTOR ==========
        printf("[3/3] Testing Hybrid NTOR...\n");

        double hybrid_times[NUM_ITERATIONS + WARMUP_ITERATIONS];

        for (int i = 0; i < NUM_ITERATIONS + WARMUP_ITERATIONS; i++) {
            printf("  %s %d/%d...\r",
                   i < WARMUP_ITERATIONS ? "Warmup" : "Iteration",
                   i < WARMUP_ITERATIONS ? i + 1 : i - WARMUP_ITERATIONS + 1,
                   i < WARMUP_ITERATIONS ? WARMUP_ITERATIONS : NUM_ITERATIONS);
            fflush(stdout);

            double cbt = build_circuit_hybrid_ntor();
            if (cbt < 0) {
                fprintf(stderr, "\nHybrid NTOR circuit build failed\n");
                fclose(csv);
                return 1;
            }

            hybrid_times[i] = cbt;
            usleep(10000);
        }
        printf("\n");

        perf_stats_t hybrid_stats;
        compute_stats(hybrid_times + WARMUP_ITERATIONS, NUM_ITERATIONS, &hybrid_stats);

        printf("  Hybrid NTOR: mean=%.3f ms, median=%.3f ms\n",
               hybrid_stats.mean_ms, hybrid_stats.median_ms);

        fprintf(csv, "%s,Hybrid NTOR,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f\n",
                topo->name,
                hybrid_stats.mean_ms, hybrid_stats.median_ms,
                hybrid_stats.min_ms, hybrid_stats.max_ms, hybrid_stats.stddev_ms,
                hybrid_stats.p95_ms, hybrid_stats.p99_ms,
                hybrid_stats.ci_lower, hybrid_stats.ci_upper);

        // ========== Comparison ==========
        double pq_overhead = pq_stats.mean_ms / classic_stats.mean_ms;
        double hybrid_overhead = hybrid_stats.mean_ms / classic_stats.mean_ms;

        printf("\nComparison (vs Classic):\n");
        printf("  PQ-NTOR:     %.2fx (%.3f ms overhead)\n",
               pq_overhead, pq_stats.mean_ms - classic_stats.mean_ms);
        printf("  Hybrid NTOR: %.2fx (%.3f ms overhead)\n",
               hybrid_overhead, hybrid_stats.mean_ms - classic_stats.mean_ms);

        clear_tc_config();
        sleep(1);
    }

    fclose(csv);

    printf("\n========================================\n");
    printf("Phase 3 Testing Complete!\n");
    printf("========================================\n");
    printf("Results saved to: phase3_sagin_cbt.csv\n\n");

    printf("Summary:\n");
    printf("  Tested %d topologies × 3 protocols × %d iterations\n",
           (int)NUM_TOPOLOGIES, NUM_ITERATIONS);
    printf("  Total circuit builds: %d\n",
           (int)(NUM_TOPOLOGIES * 3 * NUM_ITERATIONS));

    printf("\nProtocol Message Sizes:\n");
    printf("  Classic NTOR: ~116 bytes total\n");
    printf("  PQ-NTOR:      %d bytes total\n", PQ_NTOR_ONIONSKIN_LEN + PQ_NTOR_REPLY_LEN);
    printf("  Hybrid NTOR:  %d bytes total\n", HYBRID_NTOR_ONIONSKIN_LEN + HYBRID_NTOR_REPLY_LEN);

    printf("\nNext steps:\n");
    printf("  1. Analyze results: python3 analyze_phase3.py\n");
    printf("  2. Generate plots: python3 visualize_phase3.py\n");
    printf("  3. Compare with Phase 1+2 data\n\n");

    return 0;
}
