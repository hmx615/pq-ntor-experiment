/**
 * crypto_benchmark.c - Comprehensive cryptographic performance benchmark
 *
 * Tests: Classic NTOR, PQ-NTOR, Hybrid NTOR
 * Metrics: KeyGen, Onionskin, Reply, Finish, Full Handshake, 3-Hop Circuit
 * Statistics: Mean, Median, Min, Max, StdDev, P95, P99, 95% CI
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <sys/time.h>
#include <sys/utsname.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <oqs/oqs.h>

#include "pq_ntor.h"
#include "hybrid_ntor.h"
#include "crypto_utils.h"

#define NUM_ITERATIONS 1000
#define NUM_WARMUP 100

// Timing utility
static inline uint64_t get_time_us(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000000ULL + tv.tv_usec;
}

// Statistics structure
typedef struct {
    double mean;
    double median;
    double min;
    double max;
    double stddev;
    double p95;
    double p99;
    double ci_lower;
    double ci_upper;
} stats_t;

// Compare function for qsort
static int compare_double(const void *a, const void *b) {
    double da = *(const double*)a;
    double db = *(const double*)b;
    return (da > db) - (da < db);
}

// Calculate statistics
static void calculate_stats(double *samples, int n, stats_t *stats) {
    // Sort for percentiles
    qsort(samples, n, sizeof(double), compare_double);

    // Min/Max
    stats->min = samples[0];
    stats->max = samples[n-1];

    // Median
    if (n % 2 == 0) {
        stats->median = (samples[n/2 - 1] + samples[n/2]) / 2.0;
    } else {
        stats->median = samples[n/2];
    }

    // Mean
    double sum = 0;
    for (int i = 0; i < n; i++) {
        sum += samples[i];
    }
    stats->mean = sum / n;

    // StdDev
    double sq_sum = 0;
    for (int i = 0; i < n; i++) {
        sq_sum += (samples[i] - stats->mean) * (samples[i] - stats->mean);
    }
    stats->stddev = sqrt(sq_sum / n);

    // Percentiles
    stats->p95 = samples[(int)(n * 0.95)];
    stats->p99 = samples[(int)(n * 0.99)];

    // 95% CI (using z=1.96)
    double se = stats->stddev / sqrt(n);
    stats->ci_lower = stats->mean - 1.96 * se;
    stats->ci_upper = stats->mean + 1.96 * se;
}

// ============================================================================
// Classic NTOR benchmarks
// ============================================================================

static double bench_classic_keygen(void) {
    uint64_t start = get_time_us();

    EVP_PKEY *pkey = NULL;
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
    EVP_PKEY_keygen_init(ctx);
    EVP_PKEY_keygen(ctx, &pkey);
    EVP_PKEY_CTX_free(ctx);
    EVP_PKEY_free(pkey);

    return (double)(get_time_us() - start);
}

static double bench_classic_full_handshake(void) {
    uint64_t start = get_time_us();

    // Client keygen
    EVP_PKEY *client_pkey = NULL;
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
    EVP_PKEY_keygen_init(ctx);
    EVP_PKEY_keygen(ctx, &client_pkey);
    EVP_PKEY_CTX_free(ctx);

    // Server keygen
    EVP_PKEY *server_pkey = NULL;
    ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
    EVP_PKEY_keygen_init(ctx);
    EVP_PKEY_keygen(ctx, &server_pkey);
    EVP_PKEY_CTX_free(ctx);

    // ECDH
    ctx = EVP_PKEY_CTX_new(client_pkey, NULL);
    EVP_PKEY_derive_init(ctx);
    EVP_PKEY_derive_set_peer(ctx, server_pkey);
    uint8_t ss[32]; size_t ss_len = 32;
    EVP_PKEY_derive(ctx, ss, &ss_len);
    EVP_PKEY_CTX_free(ctx);

    // HMAC for auth
    uint8_t mac[32], key[16] = {0};
    hmac_sha256(mac, key, 16, ss, 32);

    EVP_PKEY_free(client_pkey);
    EVP_PKEY_free(server_pkey);

    return (double)(get_time_us() - start);
}

static double bench_classic_3hop(void) {
    uint64_t start = get_time_us();

    for (int hop = 0; hop < 3; hop++) {
        EVP_PKEY *client_pkey = NULL, *server_pkey = NULL;
        EVP_PKEY_CTX *ctx;

        ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
        EVP_PKEY_keygen_init(ctx);
        EVP_PKEY_keygen(ctx, &client_pkey);
        EVP_PKEY_CTX_free(ctx);

        ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
        EVP_PKEY_keygen_init(ctx);
        EVP_PKEY_keygen(ctx, &server_pkey);
        EVP_PKEY_CTX_free(ctx);

        ctx = EVP_PKEY_CTX_new(client_pkey, NULL);
        EVP_PKEY_derive_init(ctx);
        EVP_PKEY_derive_set_peer(ctx, server_pkey);
        uint8_t ss[32]; size_t ss_len = 32;
        EVP_PKEY_derive(ctx, ss, &ss_len);
        EVP_PKEY_CTX_free(ctx);

        EVP_PKEY_free(client_pkey);
        EVP_PKEY_free(server_pkey);

        uint8_t mac[32], key[16] = {0};
        hmac_sha256(mac, key, 16, ss, 32);
    }

    return (double)(get_time_us() - start);
}

// ============================================================================
// PQ-NTOR benchmarks
// ============================================================================

static double bench_pq_keygen(void) {
    uint64_t start = get_time_us();

    OQS_KEM *kem = OQS_KEM_new(OQS_KEM_alg_kyber_512);
    uint8_t pk[800], sk[1632];
    OQS_KEM_keypair(kem, pk, sk);
    OQS_KEM_free(kem);

    return (double)(get_time_us() - start);
}

static double bench_pq_client_create(void) {
    pq_ntor_client_state cs;
    uint8_t onion[PQ_NTOR_ONIONSKIN_LEN];
    uint8_t id[20] = {0x42};

    uint64_t start = get_time_us();
    pq_ntor_client_create_onionskin(&cs, onion, id);
    double elapsed = (double)(get_time_us() - start);

    pq_ntor_client_state_cleanup(&cs);
    return elapsed;
}

static double bench_pq_server_reply(void) {
    pq_ntor_client_state cs;
    pq_ntor_server_state ss;
    uint8_t onion[PQ_NTOR_ONIONSKIN_LEN], reply[PQ_NTOR_REPLY_LEN];
    uint8_t id[20] = {0x42};

    pq_ntor_client_create_onionskin(&cs, onion, id);

    uint64_t start = get_time_us();
    pq_ntor_server_create_reply(&ss, reply, onion, id);
    double elapsed = (double)(get_time_us() - start);

    pq_ntor_client_state_cleanup(&cs);
    pq_ntor_server_state_cleanup(&ss);
    return elapsed;
}

static double bench_pq_client_finish(void) {
    pq_ntor_client_state cs;
    pq_ntor_server_state ss;
    uint8_t onion[PQ_NTOR_ONIONSKIN_LEN], reply[PQ_NTOR_REPLY_LEN];
    uint8_t id[20] = {0x42};

    pq_ntor_client_create_onionskin(&cs, onion, id);
    pq_ntor_server_create_reply(&ss, reply, onion, id);

    uint64_t start = get_time_us();
    pq_ntor_client_finish_handshake(&cs, reply);
    double elapsed = (double)(get_time_us() - start);

    pq_ntor_client_state_cleanup(&cs);
    pq_ntor_server_state_cleanup(&ss);
    return elapsed;
}

static double bench_pq_full_handshake(void) {
    pq_ntor_client_state cs;
    pq_ntor_server_state ss;
    uint8_t onion[PQ_NTOR_ONIONSKIN_LEN], reply[PQ_NTOR_REPLY_LEN];
    uint8_t id[20] = {0x42};

    uint64_t start = get_time_us();
    pq_ntor_client_create_onionskin(&cs, onion, id);
    pq_ntor_server_create_reply(&ss, reply, onion, id);
    pq_ntor_client_finish_handshake(&cs, reply);
    double elapsed = (double)(get_time_us() - start);

    pq_ntor_client_state_cleanup(&cs);
    pq_ntor_server_state_cleanup(&ss);
    return elapsed;
}

static double bench_pq_3hop(void) {
    uint8_t id[20] = {0x42};

    uint64_t start = get_time_us();
    for (int hop = 0; hop < 3; hop++) {
        pq_ntor_client_state cs;
        pq_ntor_server_state ss;
        uint8_t onion[PQ_NTOR_ONIONSKIN_LEN], reply[PQ_NTOR_REPLY_LEN];

        pq_ntor_client_create_onionskin(&cs, onion, id);
        pq_ntor_server_create_reply(&ss, reply, onion, id);
        pq_ntor_client_finish_handshake(&cs, reply);

        pq_ntor_client_state_cleanup(&cs);
        pq_ntor_server_state_cleanup(&ss);
    }
    return (double)(get_time_us() - start);
}

// ============================================================================
// Hybrid NTOR benchmarks
// ============================================================================

static double bench_hybrid_keygen(void) {
    uint64_t start = get_time_us();

    // Kyber keygen
    OQS_KEM *kem = OQS_KEM_new(OQS_KEM_alg_kyber_512);
    uint8_t pk[800], sk[1632];
    OQS_KEM_keypair(kem, pk, sk);
    OQS_KEM_free(kem);

    // X25519 keygen
    EVP_PKEY *pkey = NULL;
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
    EVP_PKEY_keygen_init(ctx);
    EVP_PKEY_keygen(ctx, &pkey);
    EVP_PKEY_CTX_free(ctx);
    EVP_PKEY_free(pkey);

    return (double)(get_time_us() - start);
}

static double bench_hybrid_client_create(void) {
    hybrid_ntor_client_state cs;
    uint8_t onion[HYBRID_NTOR_ONIONSKIN_LEN];
    uint8_t id[HYBRID_NTOR_RELAY_ID_LENGTH] = {0x42};

    uint64_t start = get_time_us();
    hybrid_ntor_client_create_onionskin(&cs, onion, id);
    double elapsed = (double)(get_time_us() - start);

    hybrid_ntor_client_state_cleanup(&cs);
    return elapsed;
}

static double bench_hybrid_server_reply(void) {
    hybrid_ntor_client_state cs;
    hybrid_ntor_server_state ss;
    uint8_t onion[HYBRID_NTOR_ONIONSKIN_LEN], reply[HYBRID_NTOR_REPLY_LEN];
    uint8_t id[HYBRID_NTOR_RELAY_ID_LENGTH] = {0x42};

    hybrid_ntor_client_create_onionskin(&cs, onion, id);

    uint64_t start = get_time_us();
    hybrid_ntor_server_create_reply(&ss, reply, onion, id);
    double elapsed = (double)(get_time_us() - start);

    hybrid_ntor_client_state_cleanup(&cs);
    hybrid_ntor_server_state_cleanup(&ss);
    return elapsed;
}

static double bench_hybrid_client_finish(void) {
    hybrid_ntor_client_state cs;
    hybrid_ntor_server_state ss;
    uint8_t onion[HYBRID_NTOR_ONIONSKIN_LEN], reply[HYBRID_NTOR_REPLY_LEN];
    uint8_t id[HYBRID_NTOR_RELAY_ID_LENGTH] = {0x42};

    hybrid_ntor_client_create_onionskin(&cs, onion, id);
    hybrid_ntor_server_create_reply(&ss, reply, onion, id);

    uint64_t start = get_time_us();
    hybrid_ntor_client_finish_handshake(&cs, reply);
    double elapsed = (double)(get_time_us() - start);

    hybrid_ntor_client_state_cleanup(&cs);
    hybrid_ntor_server_state_cleanup(&ss);
    return elapsed;
}

static double bench_hybrid_full_handshake(void) {
    hybrid_ntor_client_state cs;
    hybrid_ntor_server_state ss;
    uint8_t onion[HYBRID_NTOR_ONIONSKIN_LEN], reply[HYBRID_NTOR_REPLY_LEN];
    uint8_t id[HYBRID_NTOR_RELAY_ID_LENGTH] = {0x42};

    uint64_t start = get_time_us();
    hybrid_ntor_client_create_onionskin(&cs, onion, id);
    hybrid_ntor_server_create_reply(&ss, reply, onion, id);
    hybrid_ntor_client_finish_handshake(&cs, reply);
    double elapsed = (double)(get_time_us() - start);

    hybrid_ntor_client_state_cleanup(&cs);
    hybrid_ntor_server_state_cleanup(&ss);
    return elapsed;
}

static double bench_hybrid_3hop(void) {
    uint8_t id[HYBRID_NTOR_RELAY_ID_LENGTH] = {0x42};

    uint64_t start = get_time_us();
    for (int hop = 0; hop < 3; hop++) {
        hybrid_ntor_client_state cs;
        hybrid_ntor_server_state ss;
        uint8_t onion[HYBRID_NTOR_ONIONSKIN_LEN], reply[HYBRID_NTOR_REPLY_LEN];

        hybrid_ntor_client_create_onionskin(&cs, onion, id);
        hybrid_ntor_server_create_reply(&ss, reply, onion, id);
        hybrid_ntor_client_finish_handshake(&cs, reply);

        hybrid_ntor_client_state_cleanup(&cs);
        hybrid_ntor_server_state_cleanup(&ss);
    }
    return (double)(get_time_us() - start);
}

// ============================================================================
// Main benchmark runner
// ============================================================================

typedef double (*bench_func_t)(void);

static void run_benchmark(const char *protocol, const char *operation,
                          bench_func_t func, FILE *csv) {
    double *samples = malloc(NUM_ITERATIONS * sizeof(double));

    // Warmup
    for (int i = 0; i < NUM_WARMUP; i++) {
        func();
    }

    // Benchmark
    for (int i = 0; i < NUM_ITERATIONS; i++) {
        samples[i] = func();
    }

    stats_t stats;
    calculate_stats(samples, NUM_ITERATIONS, &stats);

    printf("  %-20s %8.2f %8.2f %8.2f %8.2f %7.2f %8.2f %8.2f\n",
           operation, stats.mean, stats.median, stats.min, stats.max,
           stats.stddev, stats.p95, stats.p99);

    fprintf(csv, "%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n",
            protocol, operation, stats.mean, stats.median, stats.min, stats.max,
            stats.stddev, stats.p95, stats.p99, stats.ci_lower, stats.ci_upper);

    free(samples);
}

int main(void) {
    // Get platform info
    struct utsname uts;
    uname(&uts);

    printf("================================================================\n");
    printf("Cryptographic Performance Benchmark\n");
    printf("================================================================\n");
    printf("Platform: %s %s (%s)\n", uts.sysname, uts.release, uts.machine);
    printf("Iterations: %d (warmup: %d)\n", NUM_ITERATIONS, NUM_WARMUP);
    printf("================================================================\n\n");

    // Open CSV file
    char csv_filename[256];
    snprintf(csv_filename, sizeof(csv_filename), "crypto_benchmark_%s.csv", uts.machine);
    FILE *csv = fopen(csv_filename, "w");
    fprintf(csv, "Protocol,Operation,Mean_us,Median_us,Min_us,Max_us,StdDev_us,P95_us,P99_us,CI_Lower,CI_Upper\n");

    // Header
    printf("%-24s %8s %8s %8s %8s %7s %8s %8s\n",
           "Operation", "Mean", "Median", "Min", "Max", "StdDev", "P95", "P99");
    printf("--------------------------------------------------------------------------------\n");

    // Classic NTOR
    printf("\n[Classic NTOR - X25519]\n");
    run_benchmark("Classic NTOR", "KeyGen", bench_classic_keygen, csv);
    run_benchmark("Classic NTOR", "Full Handshake", bench_classic_full_handshake, csv);
    run_benchmark("Classic NTOR", "3-Hop Circuit", bench_classic_3hop, csv);

    // PQ-NTOR
    printf("\n[PQ-NTOR - Kyber-512]\n");
    run_benchmark("PQ-NTOR", "KeyGen", bench_pq_keygen, csv);
    run_benchmark("PQ-NTOR", "Client Create", bench_pq_client_create, csv);
    run_benchmark("PQ-NTOR", "Server Reply", bench_pq_server_reply, csv);
    run_benchmark("PQ-NTOR", "Client Finish", bench_pq_client_finish, csv);
    run_benchmark("PQ-NTOR", "Full Handshake", bench_pq_full_handshake, csv);
    run_benchmark("PQ-NTOR", "3-Hop Circuit", bench_pq_3hop, csv);

    // Hybrid NTOR
    printf("\n[Hybrid NTOR - Kyber-512 + X25519]\n");
    run_benchmark("Hybrid NTOR", "KeyGen", bench_hybrid_keygen, csv);
    run_benchmark("Hybrid NTOR", "Client Create", bench_hybrid_client_create, csv);
    run_benchmark("Hybrid NTOR", "Server Reply", bench_hybrid_server_reply, csv);
    run_benchmark("Hybrid NTOR", "Client Finish", bench_hybrid_client_finish, csv);
    run_benchmark("Hybrid NTOR", "Full Handshake", bench_hybrid_full_handshake, csv);
    run_benchmark("Hybrid NTOR", "3-Hop Circuit", bench_hybrid_3hop, csv);

    fclose(csv);

    // Message sizes
    printf("\n================================================================\n");
    printf("Message Sizes (bytes per hop)\n");
    printf("================================================================\n");
    printf("Protocol          Onionskin    Reply      Total\n");
    printf("----------------------------------------------------------------\n");
    printf("Classic NTOR      %5d        %5d      %5d\n", 32+20, 32+32, 116);
    printf("PQ-NTOR           %5d        %5d      %5d\n",
           PQ_NTOR_ONIONSKIN_LEN, PQ_NTOR_REPLY_LEN,
           PQ_NTOR_ONIONSKIN_LEN + PQ_NTOR_REPLY_LEN);
    printf("Hybrid NTOR       %5d        %5d      %5d\n",
           HYBRID_NTOR_ONIONSKIN_LEN, HYBRID_NTOR_REPLY_LEN,
           HYBRID_NTOR_ONIONSKIN_LEN + HYBRID_NTOR_REPLY_LEN);

    printf("\n================================================================\n");
    printf("Results saved to: %s\n", csv_filename);
    printf("================================================================\n");

    return 0;
}
