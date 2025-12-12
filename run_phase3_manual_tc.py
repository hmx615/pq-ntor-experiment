#!/usr/bin/env python3
"""
Phase 3运行脚本 - 手动TC配置版本
解决WSL2后台sudo密码问题
"""
import subprocess
import json
import time
import sys

# 12个拓扑配置
TOPOLOGIES = [
    {"name": "topo01", "rate_mbps": 59.27, "delay_ms": 5.42, "loss_percent": 3.0},
    {"name": "topo02", "rate_mbps": 16.55, "delay_ms": 5.42, "loss_percent": 3.0},
    {"name": "topo03", "rate_mbps": 25.19, "delay_ms": 2.72, "loss_percent": 1.0},
    {"name": "topo04", "rate_mbps": 23.64, "delay_ms": 5.42, "loss_percent": 3.0},
    {"name": "topo05", "rate_mbps": 25.19, "delay_ms": 5.43, "loss_percent": 3.0},
    {"name": "topo06", "rate_mbps": 22.91, "delay_ms": 5.42, "loss_percent": 1.0},
    {"name": "topo07", "rate_mbps": 69.43, "delay_ms": 5.42, "loss_percent": 2.0},
    {"name": "topo08", "rate_mbps": 38.01, "delay_ms": 5.43, "loss_percent": 2.0},
    {"name": "topo09", "rate_mbps": 29.84, "delay_ms": 2.72, "loss_percent": 0.5},
    {"name": "topo10", "rate_mbps": 18.64, "delay_ms": 5.42, "loss_percent": 2.0},
    {"name": "topo11", "rate_mbps":  9.67, "delay_ms": 5.43, "loss_percent": 2.0},
    {"name": "topo12", "rate_mbps":  8.73, "delay_ms": 5.43, "loss_percent": 2.0},
]

WORK_DIR = "/home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c"
PHASE3_BIN = f"{WORK_DIR}/phase3_sagin_network"
OUTPUT_CSV = f"{WORK_DIR}/phase3_sagin_cbt_manual.csv"
NUM_ITERATIONS = 100  # 每个拓扑每个协议的测试次数

def clear_tc():
    """清理TC配置"""
    subprocess.run(["sudo", "tc", "qdisc", "del", "dev", "lo", "root"],
                   stderr=subprocess.DEVNULL, check=False)

def apply_tc(topo):
    """应用TC配置"""
    clear_tc()

    # 使用netem配置延迟和丢包
    cmd = [
        "sudo", "tc", "qdisc", "add", "dev", "lo", "root", "netem",
        "delay", f"{topo['delay_ms']}ms",
        "loss", f"{topo['loss_percent']}%",
        "rate", f"{topo['rate_mbps']}mbit"
    ]

    print(f"[TC] Applying: {topo['name']} - rate={topo['rate_mbps']}Mbps, delay={topo['delay_ms']}ms, loss={topo['loss_percent']}%")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: TC config failed: {result.stderr}")
        return False

    time.sleep(1)  # 让配置生效
    return True

def run_benchmark_for_topo(topo):
    """为单个拓扑运行benchmark（这里简化版 - 直接返回，因为实际上Phase3程序会遍历所有拓扑）"""
    pass

def main():
    print("=" * 70)
    print("Phase 3: SAGIN Network Integration Test (Manual TC Version)")
    print("=" * 70)
    print(f"Topologies: {len(TOPOLOGIES)}")
    print(f"Iterations per topology: {NUM_ITERATIONS}")
    print("")

    # 说明：Phase3程序本身已经内置了12拓扑循环，但它需要TC权限
    # 这个脚本的目的是验证TC配置是否工作
    # 实际运行时，我们需要修改Phase3程序或者单独测试每个拓扑

    print("Testing TC configuration for all topologies...")
    for i, topo in enumerate(TOPOLOGIES, 1):
        print(f"\n[{i}/12] Testing {topo['name']}...")
        if not apply_tc(topo):
            print(f"  ❌ Failed to apply TC for {topo['name']}")
            continue

        # 验证TC配置
        result = subprocess.run(["sudo", "tc", "qdisc", "show", "dev", "lo"],
                              capture_output=True, text=True)
        if "netem" in result.stdout:
            print(f"  ✅ TC configured successfully")
        else:
            print(f"  ⚠️ TC may not be applied correctly")

        time.sleep(0.5)

    clear_tc()
    print("\n" + "=" * 70)
    print("TC配置测试完成！")
    print("=" * 70)
    print("\n说明：Phase 3程序需要在整个sudo环境下运行。")
    print("由于WSL2后台任务的sudo限制，建议使用前台运行：")
    print(f"  sudo {PHASE3_BIN}")
    print("")

if __name__ == "__main__":
    main()
