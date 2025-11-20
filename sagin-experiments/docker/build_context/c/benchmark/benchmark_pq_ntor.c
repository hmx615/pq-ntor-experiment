/**
 * @file benchmark_pq_ntor.c
 * @brief PQ-Ntor 性能基准测试程序
 *
 * 测量 PQ-Ntor 握手协议的性能指标：
 * - 客户端 onionskin 创建时间
 * - 服务端 reply 创建时间
 * - 客户端握手完成时间
 * - 总握手时间
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include "../src/pq_ntor.h"

// 测试配置
#define NUM_ITERATIONS 1000   // 测试次数
#define WARMUP_ITERATIONS 10  // 预热次数

/**
 * 获取当前时间（微秒）
 */
static inline uint64_t get_time_us(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000000 + tv.tv_usec;
}

/**
 * 性能统计结构
 */
typedef struct {
    double min_us;
    double max_us;
    double avg_us;
    double median_us;
    double std_dev_us;
} perf_stats_t;

/**
 * 比较函数（用于排序）
 */
static int compare_double(const void *a, const void *b) {
    double diff = *(const double*)a - *(const double*)b;
    if (diff < 0) return -1;
    if (diff > 0) return 1;
    return 0;
}

/**
 * 计算性能统计
 */
static void compute_stats(double *times, int count, perf_stats_t *stats) {
    // 排序
    qsort(times, count, sizeof(double), compare_double);

    // 最小、最大、中位数
    stats->min_us = times[0];
    stats->max_us = times[count - 1];
    stats->median_us = times[count / 2];

    // 平均值
    double sum = 0.0;
    for (int i = 0; i < count; i++) {
        sum += times[i];
    }
    stats->avg_us = sum / count;

    // 标准差
    double var_sum = 0.0;
    for (int i = 0; i < count; i++) {
        double diff = times[i] - stats->avg_us;
        var_sum += diff * diff;
    }
    stats->std_dev_us = sqrt(var_sum / count);
}

/**
 * 打印统计结果
 */
static void print_stats(const char *name, const perf_stats_t *stats) {
    printf("%-30s: ", name);
    printf("avg=%8.2f μs  ", stats->avg_us);
    printf("median=%8.2f μs  ", stats->median_us);
    printf("min=%8.2f μs  ", stats->min_us);
    printf("max=%8.2f μs  ", stats->max_us);
    printf("stddev=%7.2f μs\n", stats->std_dev_us);
}

/**
 * 基准测试：客户端创建 onionskin
 */
static void benchmark_client_create_onionskin(double *times, int iterations) {
    uint8_t relay_identity[PQ_NTOR_RELAY_ID_LENGTH];
    memset(relay_identity, 0xAB, sizeof(relay_identity));

    for (int i = 0; i < iterations; i++) {
        pq_ntor_client_state client_state;
        uint8_t onionskin[PQ_NTOR_ONIONSKIN_LEN];

        uint64_t start = get_time_us();
        pq_ntor_client_create_onionskin(&client_state, onionskin, relay_identity);
        uint64_t end = get_time_us();

        times[i] = (double)(end - start);

        pq_ntor_client_state_cleanup(&client_state);
    }
}

/**
 * 基准测试：服务端创建 reply
 */
static void benchmark_server_create_reply(double *times, int iterations) {
    uint8_t relay_identity[PQ_NTOR_RELAY_ID_LENGTH];
    memset(relay_identity, 0xAB, sizeof(relay_identity));

    // 预先生成 onionskin
    pq_ntor_client_state client_state;
    uint8_t onionskin[PQ_NTOR_ONIONSKIN_LEN];
    pq_ntor_client_create_onionskin(&client_state, onionskin, relay_identity);

    for (int i = 0; i < iterations; i++) {
        pq_ntor_server_state server_state;
        uint8_t reply[PQ_NTOR_REPLY_LEN];

        uint64_t start = get_time_us();
        pq_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity);
        uint64_t end = get_time_us();

        times[i] = (double)(end - start);

        pq_ntor_server_state_cleanup(&server_state);
    }

    pq_ntor_client_state_cleanup(&client_state);
}

/**
 * 基准测试：客户端完成握手
 */
static void benchmark_client_finish_handshake(double *times, int iterations) {
    uint8_t relay_identity[PQ_NTOR_RELAY_ID_LENGTH];
    memset(relay_identity, 0xAB, sizeof(relay_identity));

    for (int i = 0; i < iterations; i++) {
        // 完整握手流程准备
        pq_ntor_client_state client_state;
        pq_ntor_server_state server_state;
        uint8_t onionskin[PQ_NTOR_ONIONSKIN_LEN];
        uint8_t reply[PQ_NTOR_REPLY_LEN];

        pq_ntor_client_create_onionskin(&client_state, onionskin, relay_identity);
        pq_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity);

        uint64_t start = get_time_us();
        pq_ntor_client_finish_handshake(&client_state, reply);
        uint64_t end = get_time_us();

        times[i] = (double)(end - start);

        pq_ntor_client_state_cleanup(&client_state);
        pq_ntor_server_state_cleanup(&server_state);
    }
}

/**
 * 基准测试：完整握手
 */
static void benchmark_full_handshake(double *times, int iterations) {
    uint8_t relay_identity[PQ_NTOR_RELAY_ID_LENGTH];
    memset(relay_identity, 0xAB, sizeof(relay_identity));

    for (int i = 0; i < iterations; i++) {
        pq_ntor_client_state client_state;
        pq_ntor_server_state server_state;
        uint8_t onionskin[PQ_NTOR_ONIONSKIN_LEN];
        uint8_t reply[PQ_NTOR_REPLY_LEN];

        uint64_t start = get_time_us();

        pq_ntor_client_create_onionskin(&client_state, onionskin, relay_identity);
        pq_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity);
        pq_ntor_client_finish_handshake(&client_state, reply);

        uint64_t end = get_time_us();

        times[i] = (double)(end - start);

        pq_ntor_client_state_cleanup(&client_state);
        pq_ntor_server_state_cleanup(&server_state);
    }
}

/**
 * 输出 CSV 格式的数据
 */
static void output_csv(const char *filename,
                       const perf_stats_t *client_create,
                       const perf_stats_t *server_reply,
                       const perf_stats_t *client_finish,
                       const perf_stats_t *full_handshake) {
    FILE *fp = fopen(filename, "w");
    if (!fp) {
        fprintf(stderr, "Error: Cannot create CSV file: %s\n", filename);
        return;
    }

    fprintf(fp, "Operation,Min(μs),Max(μs),Avg(μs),Median(μs),StdDev(μs),Min(ms),Avg(ms)\n");
    fprintf(fp, "Client Create Onionskin,%.2f,%.2f,%.2f,%.2f,%.2f,%.3f,%.3f\n",
            client_create->min_us, client_create->max_us, client_create->avg_us,
            client_create->median_us, client_create->std_dev_us,
            client_create->min_us / 1000.0, client_create->avg_us / 1000.0);

    fprintf(fp, "Server Create Reply,%.2f,%.2f,%.2f,%.2f,%.2f,%.3f,%.3f\n",
            server_reply->min_us, server_reply->max_us, server_reply->avg_us,
            server_reply->median_us, server_reply->std_dev_us,
            server_reply->min_us / 1000.0, server_reply->avg_us / 1000.0);

    fprintf(fp, "Client Finish Handshake,%.2f,%.2f,%.2f,%.2f,%.2f,%.3f,%.3f\n",
            client_finish->min_us, client_finish->max_us, client_finish->avg_us,
            client_finish->median_us, client_finish->std_dev_us,
            client_finish->min_us / 1000.0, client_finish->avg_us / 1000.0);

    fprintf(fp, "Full Handshake,%.2f,%.2f,%.2f,%.2f,%.2f,%.3f,%.3f\n",
            full_handshake->min_us, full_handshake->max_us, full_handshake->avg_us,
            full_handshake->median_us, full_handshake->std_dev_us,
            full_handshake->min_us / 1000.0, full_handshake->avg_us / 1000.0);

    fclose(fp);
    printf("\n✓ CSV data saved to: %s\n", filename);
}

int main(void) {
    printf("======================================================================\n");
    printf("PQ-Ntor Performance Benchmark\n");
    printf("======================================================================\n");
    printf("Algorithm:     %s\n", kyber_get_algorithm_name());
    printf("Iterations:    %d (with %d warmup)\n", NUM_ITERATIONS, WARMUP_ITERATIONS);
    printf("======================================================================\n\n");

    // 分配时间数组
    double *times = malloc(sizeof(double) * (NUM_ITERATIONS + WARMUP_ITERATIONS));
    if (!times) {
        fprintf(stderr, "Error: Memory allocation failed\n");
        return 1;
    }

    perf_stats_t stats;

    // ===== 预热 =====
    printf("Warming up...\n");
    benchmark_full_handshake(times, WARMUP_ITERATIONS);

    // ===== 测试 1: 客户端创建 onionskin =====
    printf("\n[1/4] Benchmarking: Client create onionskin...\n");
    benchmark_client_create_onionskin(times, NUM_ITERATIONS);
    compute_stats(times, NUM_ITERATIONS, &stats);
    print_stats("Client create onionskin", &stats);
    perf_stats_t client_create_stats = stats;

    // ===== 测试 2: 服务端创建 reply =====
    printf("\n[2/4] Benchmarking: Server create reply...\n");
    benchmark_server_create_reply(times, NUM_ITERATIONS);
    compute_stats(times, NUM_ITERATIONS, &stats);
    print_stats("Server create reply", &stats);
    perf_stats_t server_reply_stats = stats;

    // ===== 测试 3: 客户端完成握手 =====
    printf("\n[3/4] Benchmarking: Client finish handshake...\n");
    benchmark_client_finish_handshake(times, NUM_ITERATIONS);
    compute_stats(times, NUM_ITERATIONS, &stats);
    print_stats("Client finish handshake", &stats);
    perf_stats_t client_finish_stats = stats;

    // ===== 测试 4: 完整握手 =====
    printf("\n[4/4] Benchmarking: Full handshake...\n");
    benchmark_full_handshake(times, NUM_ITERATIONS);
    compute_stats(times, NUM_ITERATIONS, &stats);
    print_stats("Full handshake", &stats);
    perf_stats_t full_handshake_stats = stats;

    // ===== 输出汇总 =====
    printf("\n======================================================================\n");
    printf("Summary (in milliseconds)\n");
    printf("======================================================================\n");
    printf("Operation                      Avg (ms)   Median (ms)   Min (ms)   Max (ms)\n");
    printf("----------------------------------------------------------------------\n");
    printf("Client create onionskin        %8.3f   %8.3f      %8.3f   %8.3f\n",
           client_create_stats.avg_us / 1000.0, client_create_stats.median_us / 1000.0,
           client_create_stats.min_us / 1000.0, client_create_stats.max_us / 1000.0);
    printf("Server create reply            %8.3f   %8.3f      %8.3f   %8.3f\n",
           server_reply_stats.avg_us / 1000.0, server_reply_stats.median_us / 1000.0,
           server_reply_stats.min_us / 1000.0, server_reply_stats.max_us / 1000.0);
    printf("Client finish handshake        %8.3f   %8.3f      %8.3f   %8.3f\n",
           client_finish_stats.avg_us / 1000.0, client_finish_stats.median_us / 1000.0,
           client_finish_stats.min_us / 1000.0, client_finish_stats.max_us / 1000.0);
    printf("----------------------------------------------------------------------\n");
    printf("FULL HANDSHAKE (total)         %8.3f   %8.3f      %8.3f   %8.3f\n",
           full_handshake_stats.avg_us / 1000.0, full_handshake_stats.median_us / 1000.0,
           full_handshake_stats.min_us / 1000.0, full_handshake_stats.max_us / 1000.0);
    printf("======================================================================\n");

    // 输出 CSV
    output_csv("benchmark_results.csv",
               &client_create_stats, &server_reply_stats,
               &client_finish_stats, &full_handshake_stats);

    // 清理
    free(times);

    printf("\n✅ Benchmark completed successfully!\n");
    printf("======================================================================\n");

    return 0;
}
