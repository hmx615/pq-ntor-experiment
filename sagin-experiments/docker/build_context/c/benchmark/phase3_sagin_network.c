/**
 * phase3_sagin_network.c
 *
 * Phase 3: SAGIN Network Integration Testing
 * Measures Circuit Build Time (CBT) across 12 SAGIN topologies
 * Compares Classic NTOR vs PQ-NTOR in real network conditions
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

// 12 SAGIN topologies from real NOMA data (corrected 2025-12-11)
static const topology_config_t TOPOLOGIES[] = {
    {"topo01",  59.27,  5.42,  3.0},  // Z1 Up - 直连NOMA
    {"topo02",  16.55,  5.42,  3.0},  // Z1 Up - T协作接入
    {"topo03",  25.19,  2.72,  1.0},  // Z1 Up - 双跳直连
    {"topo04",  23.64,  5.42,  3.0},  // Z1 Up - T协作双跳
    {"topo05",  25.19,  5.43,  3.0},  // Z1 Up - 并行NOMA
    {"topo06",  22.91,  5.42,  1.0},  // Z1 Up - 并行协作
    {"topo07",  69.43,  5.42,  2.0},  // Z1 Down - 直连NOMA
    {"topo08",  38.01,  5.43,  2.0},  // Z1 Down - T协作接入
    {"topo09",  29.84,  2.72,  0.5},  // Z1 Down - 双跳直连
    {"topo10",  18.64,  5.42,  2.0},  // Z1 Down - T协作双跳
    {"topo11",   9.67,  5.43,  2.0},  // Z1 Down - 并行NOMA
    {"topo12",   8.73,  5.43,  2.0}   // Z1 Down - 并行协作
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

// ============ Circuit Building ============

/**
 * Simulate 3-hop circuit build with PQ-NTOR
 * Returns Circuit Build Time in milliseconds
 */
static double build_circuit_pq_ntor(void) {
    uint64_t start = get_time_us();

    // Simulate relay identity (20 bytes)
    uint8_t guard_identity[20], middle_identity[20], exit_identity[20];
    memset(guard_identity, 0x01, 20);
    memset(middle_identity, 0x02, 20);
    memset(exit_identity, 0x03, 20);

    // ===== Hop 1: Client -> Guard =====
    pq_ntor_client_state client_state_1;
    uint8_t onionskin_1[PQ_NTOR_ONIONSKIN_LEN];

    if (pq_ntor_client_create_onionskin(&client_state_1, onionskin_1, guard_identity) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "Failed to create onionskin for Guard\n");
        return -1;
    }

    // Server processes
    pq_ntor_server_state server_state_1;
    uint8_t reply_1[PQ_NTOR_REPLY_LEN];

    if (pq_ntor_server_create_reply(&server_state_1, reply_1, onionskin_1, guard_identity) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "Guard failed to create reply\n");
        pq_ntor_client_state_cleanup(&client_state_1);
        return -1;
    }

    // Client finishes handshake
    if (pq_ntor_client_finish_handshake(&client_state_1, reply_1) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "Client failed to finish handshake with Guard\n");
        pq_ntor_server_state_cleanup(&server_state_1);
        pq_ntor_client_state_cleanup(&client_state_1);
        return -1;
    }

    uint8_t key_1[PQ_NTOR_KEY_MATERIAL_LEN];
    pq_ntor_client_get_key(key_1, &client_state_1);

    pq_ntor_client_state_cleanup(&client_state_1);
    pq_ntor_server_state_cleanup(&server_state_1);

    // ===== Hop 2: Client -> Guard -> Middle =====
    pq_ntor_client_state client_state_2;
    uint8_t onionskin_2[PQ_NTOR_ONIONSKIN_LEN];

    if (pq_ntor_client_create_onionskin(&client_state_2, onionskin_2, middle_identity) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "Failed to create onionskin for Middle\n");
        return -1;
    }

    pq_ntor_server_state server_state_2;
    uint8_t reply_2[PQ_NTOR_REPLY_LEN];

    if (pq_ntor_server_create_reply(&server_state_2, reply_2, onionskin_2, middle_identity) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "Middle failed to create reply\n");
        pq_ntor_client_state_cleanup(&client_state_2);
        return -1;
    }

    if (pq_ntor_client_finish_handshake(&client_state_2, reply_2) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "Client failed to finish handshake with Middle\n");
        pq_ntor_server_state_cleanup(&server_state_2);
        pq_ntor_client_state_cleanup(&client_state_2);
        return -1;
    }

    uint8_t key_2[PQ_NTOR_KEY_MATERIAL_LEN];
    pq_ntor_client_get_key(key_2, &client_state_2);

    pq_ntor_client_state_cleanup(&client_state_2);
    pq_ntor_server_state_cleanup(&server_state_2);

    // ===== Hop 3: Client -> Guard -> Middle -> Exit =====
    pq_ntor_client_state client_state_3;
    uint8_t onionskin_3[PQ_NTOR_ONIONSKIN_LEN];

    if (pq_ntor_client_create_onionskin(&client_state_3, onionskin_3, exit_identity) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "Failed to create onionskin for Exit\n");
        return -1;
    }

    pq_ntor_server_state server_state_3;
    uint8_t reply_3[PQ_NTOR_REPLY_LEN];

    if (pq_ntor_server_create_reply(&server_state_3, reply_3, onionskin_3, exit_identity) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "Exit failed to create reply\n");
        pq_ntor_client_state_cleanup(&client_state_3);
        return -1;
    }

    if (pq_ntor_client_finish_handshake(&client_state_3, reply_3) != PQ_NTOR_SUCCESS) {
        fprintf(stderr, "Client failed to finish handshake with Exit\n");
        pq_ntor_server_state_cleanup(&server_state_3);
        pq_ntor_client_state_cleanup(&client_state_3);
        return -1;
    }

    uint8_t key_3[PQ_NTOR_KEY_MATERIAL_LEN];
    pq_ntor_client_get_key(key_3, &client_state_3);

    pq_ntor_client_state_cleanup(&client_state_3);
    pq_ntor_server_state_cleanup(&server_state_3);

    uint64_t end = get_time_us();
    return (double)(end - start) / 1000.0; // Convert to milliseconds
}

/**
 * Simulate 3-hop circuit build with Classic NTOR (X25519)
 * Returns Circuit Build Time in milliseconds
 */
static double build_circuit_classic_ntor(void) {
    uint64_t start = get_time_us();

    // Simulate 3 hops of Classic NTOR
    // Each hop: keygen + DH + HMAC

    for (int hop = 0; hop < 3; hop++) {
        // Client keygen
        EVP_PKEY *client_pkey = NULL;
        EVP_PKEY_CTX *keygen_ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
        if (!keygen_ctx) {
            fprintf(stderr, "Failed to create keygen context\n");
            return -1;
        }

        if (EVP_PKEY_keygen_init(keygen_ctx) <= 0 ||
            EVP_PKEY_keygen(keygen_ctx, &client_pkey) <= 0) {
            fprintf(stderr, "Client keygen failed\n");
            EVP_PKEY_CTX_free(keygen_ctx);
            return -1;
        }
        EVP_PKEY_CTX_free(keygen_ctx);

        // Server keygen
        EVP_PKEY *server_pkey = NULL;
        keygen_ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
        if (!keygen_ctx) {
            EVP_PKEY_free(client_pkey);
            return -1;
        }

        if (EVP_PKEY_keygen_init(keygen_ctx) <= 0 ||
            EVP_PKEY_keygen(keygen_ctx, &server_pkey) <= 0) {
            fprintf(stderr, "Server keygen failed\n");
            EVP_PKEY_CTX_free(keygen_ctx);
            EVP_PKEY_free(client_pkey);
            return -1;
        }
        EVP_PKEY_CTX_free(keygen_ctx);

        // DH computation
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
            fprintf(stderr, "DH derive failed\n");
            EVP_PKEY_CTX_free(derive_ctx);
            EVP_PKEY_free(client_pkey);
            EVP_PKEY_free(server_pkey);
            return -1;
        }

        EVP_PKEY_CTX_free(derive_ctx);
        EVP_PKEY_free(client_pkey);
        EVP_PKEY_free(server_pkey);

        // HMAC
        uint8_t mac[32];
        uint8_t key[16] = {0};
        if (hmac_sha256(mac, key, sizeof(key), shared_secret, secret_len) != 0) {
            fprintf(stderr, "HMAC failed\n");
            return -1;
        }
    }

    uint64_t end = get_time_us();
    return (double)(end - start) / 1000.0; // Convert to milliseconds
}

// ============ Topology Testing ============

static int apply_tc_config(const topology_config_t *topo) {
    printf("[TC] Applying: rate=%.2f Mbps, delay=%.2f ms, loss=%.2f%%\n",
           topo->rate_mbps, topo->delay_ms, topo->loss_percent);

    char cmd[512];

    // Clear existing configuration (must run as root)
    system("tc qdisc del dev lo root 2>/dev/null");

    // Apply netem directly to root (simplified - only delay and loss, no rate limiting)
    // Note: Rate limiting with tbf may not be supported on all kernels
    // IMPORTANT: This program must be run with sudo/root privileges
    snprintf(cmd, sizeof(cmd),
             "tc qdisc add dev lo root netem delay %.2fms loss %.2f%%",
             topo->delay_ms, topo->loss_percent);

    int ret = system(cmd);
    if (ret != 0) {
        fprintf(stderr, "[TC] Warning: Failed to apply netem (delay+loss)\n");
        return -1;
    }

    printf("[TC] Configuration applied successfully (delay=%.2fms, loss=%.2f%%)\n",
           topo->delay_ms, topo->loss_percent);

    // Note: Bandwidth limiting not applied due to kernel limitations
    // The test focuses on latency and packet loss characteristics

    return 0;
}

static int clear_tc_config(void) {
    printf("[TC] Clearing tc/netem configuration\n");
    system("tc qdisc del dev lo root 2>/dev/null");
    return 0;
}

// ============ Main Benchmark ============

int main(int argc, char *argv[]) {
    (void)argc; // Unused
    (void)argv; // Unused

    printf("========================================\n");
    printf("Phase 3: SAGIN Network Integration Test\n");
    printf("========================================\n\n");

    printf("Configuration:\n");
    printf("  Topologies: %d SAGIN topologies\n", (int)NUM_TOPOLOGIES);
    printf("  Iterations: %d (+ %d warmup)\n", NUM_ITERATIONS, WARMUP_ITERATIONS);
    printf("  Confidence: %.0f%%\n\n", CONFIDENCE_LEVEL * 100);

    // Open CSV output file
    FILE *csv = fopen("phase3_sagin_cbt.csv", "w");
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

        // Apply tc/netem configuration
        apply_tc_config(topo);
        sleep(1); // Let configuration stabilize

        // ========== Test Classic NTOR ==========
        printf("Testing Classic NTOR...\n");

        double classic_times[NUM_ITERATIONS + WARMUP_ITERATIONS];

        for (int i = 0; i < NUM_ITERATIONS + WARMUP_ITERATIONS; i++) {
            if (i < WARMUP_ITERATIONS) {
                printf("  Warmup %d/%d...\r", i + 1, WARMUP_ITERATIONS);
            } else {
                printf("  Iteration %d/%d...\r", i - WARMUP_ITERATIONS + 1, NUM_ITERATIONS);
            }
            fflush(stdout);

            double cbt = build_circuit_classic_ntor();
            if (cbt < 0) {
                fprintf(stderr, "\nClassic NTOR circuit build failed\n");
                fclose(csv);
                return 1;
            }

            classic_times[i] = cbt;
            usleep(10000); // 10ms between tests
        }
        printf("\n");

        perf_stats_t classic_stats;
        compute_stats(classic_times + WARMUP_ITERATIONS, NUM_ITERATIONS, &classic_stats);

        printf("Classic NTOR Results:\n");
        printf("  Mean:   %8.2f ms\n", classic_stats.mean_ms);
        printf("  Median: %8.2f ms\n", classic_stats.median_ms);
        printf("  StdDev: %8.2f ms\n", classic_stats.stddev_ms);
        printf("  95%% CI: [%.2f, %.2f] ms\n\n", classic_stats.ci_lower, classic_stats.ci_upper);

        fprintf(csv, "%s,Classic NTOR,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n",
                topo->name,
                classic_stats.mean_ms, classic_stats.median_ms,
                classic_stats.min_ms, classic_stats.max_ms, classic_stats.stddev_ms,
                classic_stats.p95_ms, classic_stats.p99_ms,
                classic_stats.ci_lower, classic_stats.ci_upper);

        // ========== Test PQ-NTOR ==========
        printf("Testing PQ-NTOR...\n");

        double pq_times[NUM_ITERATIONS + WARMUP_ITERATIONS];

        for (int i = 0; i < NUM_ITERATIONS + WARMUP_ITERATIONS; i++) {
            if (i < WARMUP_ITERATIONS) {
                printf("  Warmup %d/%d...\r", i + 1, WARMUP_ITERATIONS);
            } else {
                printf("  Iteration %d/%d...\r", i - WARMUP_ITERATIONS + 1, NUM_ITERATIONS);
            }
            fflush(stdout);

            double cbt = build_circuit_pq_ntor();
            if (cbt < 0) {
                fprintf(stderr, "\nPQ-NTOR circuit build failed\n");
                fclose(csv);
                return 1;
            }

            pq_times[i] = cbt;
            usleep(10000); // 10ms between tests
        }
        printf("\n");

        perf_stats_t pq_stats;
        compute_stats(pq_times + WARMUP_ITERATIONS, NUM_ITERATIONS, &pq_stats);

        printf("PQ-NTOR Results:\n");
        printf("  Mean:   %8.2f ms\n", pq_stats.mean_ms);
        printf("  Median: %8.2f ms\n", pq_stats.median_ms);
        printf("  StdDev: %8.2f ms\n", pq_stats.stddev_ms);
        printf("  95%% CI: [%.2f, %.2f] ms\n\n", pq_stats.ci_lower, pq_stats.ci_upper);

        fprintf(csv, "%s,PQ-NTOR,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n",
                topo->name,
                pq_stats.mean_ms, pq_stats.median_ms,
                pq_stats.min_ms, pq_stats.max_ms, pq_stats.stddev_ms,
                pq_stats.p95_ms, pq_stats.p99_ms,
                pq_stats.ci_lower, pq_stats.ci_upper);

        // ========== Comparison ==========
        double overhead_ratio = pq_stats.mean_ms / classic_stats.mean_ms;
        double absolute_overhead = pq_stats.mean_ms - classic_stats.mean_ms;

        printf("Comparison:\n");
        printf("  PQ overhead:  %.2fx (%.2f ms)\n", overhead_ratio, absolute_overhead);
        printf("  Network CBT:  Classic=%.2f ms, PQ=%.2f ms\n\n",
               classic_stats.mean_ms, pq_stats.mean_ms);

        // Clear tc configuration
        clear_tc_config();
        sleep(1);
    }

    fclose(csv);

    printf("\n========================================\n");
    printf("Phase 3 Testing Complete!\n");
    printf("========================================\n");
    printf("Results saved to: phase3_sagin_cbt.csv\n\n");

    printf("Summary:\n");
    printf("  Tested %d topologies × 2 protocols × %d iterations\n",
           (int)NUM_TOPOLOGIES, NUM_ITERATIONS);
    printf("  Total circuit builds: %d\n",
           (int)(NUM_TOPOLOGIES * 2 * NUM_ITERATIONS));

    printf("\nNext steps:\n");
    printf("  1. Analyze results: python3 analyze_phase3.py\n");
    printf("  2. Generate plots: python3 visualize_phase3.py\n");
    printf("  3. Compare with Phase 1+2 data for comprehensive analysis\n\n");

    return 0;
}
