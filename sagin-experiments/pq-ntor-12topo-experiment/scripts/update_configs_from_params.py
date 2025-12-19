#!/usr/bin/env python3
"""
更新12拓扑配置文件，使用最新的topology_params.json参数

作者: Claude Code
日期: 2025-12-15
"""

import json
from pathlib import Path

# 路径配置
SCRIPT_DIR = Path(__file__).parent.absolute()
CONFIG_DIR = SCRIPT_DIR.parent / "configs"
PARAMS_FILE = Path("/home/ccc/pq-ntor-experiment/last_experiment/topology_params.json")

def main():
    # 加载最新拓扑参数
    print(f"📖 加载拓扑参数: {PARAMS_FILE}")
    with open(PARAMS_FILE, 'r') as f:
        params = json.load(f)

    print(f"✅ 已加载 {len(params)} 个拓扑参数\n")

    # 更新每个配置文件
    for topo_id in range(1, 13):
        topo_key = f"topo{topo_id:02d}"
        config_file = CONFIG_DIR / f"{topo_key}_tor_mapping.json"

        if not config_file.exists():
            print(f"⚠️  配置文件不存在: {config_file}")
            continue

        # 读取现有配置
        with open(config_file, 'r') as f:
            config = json.load(f)

        # 获取最新参数
        if topo_key not in params:
            print(f"⚠️  拓扑参数不存在: {topo_key}")
            continue

        topo_params = params[topo_key]
        new_delay = topo_params['end_to_end']['delay_ms']
        new_bw = topo_params['end_to_end']['rate_mbps']
        new_loss = topo_params['end_to_end']['packet_loss_percent']

        # 获取旧参数
        old_params = config['network_simulation']['aggregate_params']
        old_delay = old_params['delay_ms']
        old_bw = old_params['bandwidth_mbps']
        old_loss = old_params['loss_percent']

        # 检查是否需要更新
        need_update = (
            abs(old_delay - new_delay) > 0.01 or
            abs(old_bw - new_bw) > 0.01 or
            abs(old_loss - new_loss) > 0.01
        )

        if need_update:
            print(f"📝 更新 {topo_key}:")
            print(f"   延迟: {old_delay:.2f}ms → {new_delay:.2f}ms")
            print(f"   带宽: {old_bw:.2f}Mbps → {new_bw:.2f}Mbps")
            print(f"   丢包: {old_loss:.2f}% → {new_loss:.2f}%")

            # 更新参数
            config['network_simulation']['aggregate_params'] = {
                'delay_ms': round(new_delay, 2),
                'bandwidth_mbps': round(new_bw, 2),
                'loss_percent': round(new_loss, 2)
            }

            # 更新TC命令
            delay_jitter = round(new_delay * 0.25, 2)  # 25%抖动
            tc_cmd = f"sudo tc qdisc add dev lo root netem delay {new_delay:.2f}ms {delay_jitter:.2f}ms distribution normal rate {new_bw:.2f}mbit loss {new_loss:.2f}%"
            config['network_simulation']['tc_commands'] = [
                "sudo tc qdisc del dev lo root 2>/dev/null || true",
                tc_cmd
            ]

            # 保存更新后的配置
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"   ✅ 已保存")
        else:
            print(f"✓ {topo_key}: 参数已是最新")

    print("\n" + "=" * 60)
    print("✅ 配置文件更新完成!")
    print("=" * 60)

    # 打印参数汇总
    print("\n📊 最新参数汇总:")
    print("-" * 60)
    print(f"{'拓扑':<10} {'带宽(Mbps)':<12} {'延迟(ms)':<12} {'丢包(%)':<10}")
    print("-" * 60)

    for topo_id in range(1, 13):
        topo_key = f"topo{topo_id:02d}"
        if topo_key in params:
            p = params[topo_key]['end_to_end']
            print(f"{topo_key:<10} {p['rate_mbps']:<12.2f} {p['delay_ms']:<12.2f} {p['packet_loss_percent']:<10.1f}")
    print("-" * 60)

if __name__ == "__main__":
    main()
