#!/usr/bin/env python3
import paramiko

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
    sftp = ssh.open_sftp()

    print("📥 下载飞腾派实验数据...")

    # 下载CSV
    remote_csv = "/home/user/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi/benchmark_results_arm64_20251127_153211.csv"
    local_csv = "/home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/实验结果汇总/飞腾派_benchmark_results.csv"

    sftp.get(remote_csv, local_csv)
    print(f"✅ CSV已下载: {local_csv}")

    # 下载JSON
    remote_json = "/home/user/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/results/phytium_pi/benchmark_summary.json"
    local_json = "/home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/实验结果汇总/飞腾派_benchmark_summary.json"

    sftp.get(remote_json, local_json)
    print(f"✅ JSON已下载: {local_json}")

    sftp.close()

finally:
    ssh.close()
