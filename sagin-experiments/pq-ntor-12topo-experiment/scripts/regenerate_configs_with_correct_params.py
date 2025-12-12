#!/usr/bin/env python3
"""
重新生成12拓扑配置文件 - 使用topology_params.json中的正确网络参数
修复TC命令与aggregate_params不匹配的问题

作者: Claude Code
日期: 2025-12-10
"""

import json
import os
from pathlib import Path

# 路径配置
SCRIPT_DIR = Path(__file__).parent
EXP_DIR = SCRIPT_DIR.parent
CONFIG_DIR = EXP_DIR / "configs"
TOPOLOGY_PARAMS_FILE = Path("/home/ccc/pq-ntor-experiment/last_experiment/topology_params.json")

# 加载正确的拓扑参数
print(f"📖 加载拓扑参数: {TOPOLOGY_PARAMS_FILE}")
with open(TOPOLOGY_PARAMS_FILE, 'r') as f:
    TOPOLOGY_PARAMS = json.load(f)

print(f"✅ 加载了 {len(TOPOLOGY_PARAMS)} 个拓扑配置\n")

# 12种拓扑的物理链路定义
TOPOLOGIES_PHYSICAL = {
    1: {
        "name": "Z1 Up - 直连NOMA",
        "direction": "uplink",
        "links": [
            {"source": "UAV2", "target": "SAT", "rssi": "high"},
            {"source": "Ground2", "target": "SAT", "rssi": "low"}
        ],
        "tor_circuit": {
            "client": "Ground2",
            "guard": "UAV2",
            "middle": "SAT",
            "exit": "SAT"
        }
    },
    2: {
        "name": "Z1 Up - T协作接入(混合双路径)",
        "direction": "uplink",
        "links": [
            {"source": "Ground3", "target": "Ground2", "rssi": "high"},
            {"source": "Ground2", "target": "SAT", "rssi": "low"},
            {"source": "Ground3", "target": "UAV2", "rssi": "low"},
            {"source": "UAV2", "target": "SAT", "rssi": "high"}
        ],
        "tor_circuit": {
            "client": "Ground3",
            "guard": "UAV2",
            "middle": "SAT",
            "exit": "SAT"
        }
    },
    3: {
        "name": "Z3 Up - T用户协作NOMA",
        "direction": "uplink",
        "links": [
            {"source": "Ground1", "target": "UAV1", "rssi": "high"},
            {"source": "Ground2", "target": "UAV1", "rssi": "low"},
            {"source": "UAV1", "target": "SAT", "rssi": "high"}
        ],
        "tor_circuit": {
            "client": "Ground1",
            "guard": "UAV1",
            "middle": "SAT",
            "exit": "SAT"
        }
    },
    4: {
        "name": "Z4 Up - 混合直连+协作",
        "direction": "uplink",
        "links": [
            {"source": "Ground2", "target": "SAT", "rssi": "low"},
            {"source": "Ground3", "target": "UAV2", "rssi": "high"},
            {"source": "UAV2", "target": "SAT", "rssi": "high"}
        ],
        "tor_circuit": {
            "client": "Ground3",
            "guard": "UAV2",
            "middle": "SAT",
            "exit": "SAT"
        }
    },
    5: {
        "name": "Z5 Up - 多层树形",
        "direction": "uplink",
        "links": [
            {"source": "Ground2", "target": "SAT", "rssi": "low"},
            {"source": "UAV2", "target": "SAT", "rssi": "high"},
            {"source": "Ground1", "target": "UAV2", "rssi": "high"},
            {"source": "Ground3", "target": "UAV2", "rssi": "low"}
        ],
        "tor_circuit": {
            "client": "Ground1",
            "guard": "UAV2",
            "middle": "SAT",
            "exit": "SAT"
        }
    },
    6: {
        "name": "Z6 Up - 无人机+终端双中继",
        "direction": "uplink",
        "links": [
            {"source": "Ground1", "target": "UAV1", "rssi": "high"},
            {"source": "UAV1", "target": "SAT", "rssi": "high"},
            {"source": "Ground3", "target": "Ground2", "rssi": "low"},
            {"source": "Ground2", "target": "SAT", "rssi": "low"}
        ],
        "tor_circuit": {
            "client": "Ground1",
            "guard": "UAV1",
            "middle": "SAT",
            "exit": "SAT"
        }
    },
    7: {
        "name": "Z1 Down - 直连NOMA+协作",
        "direction": "downlink",
        "links": [
            {"source": "SAT", "target": "UAV2", "rssi": "high"},
            {"source": "SAT", "target": "Ground2", "rssi": "low"},
            {"source": "UAV2", "target": "Ground2", "rssi": "coop"}
        ],
        "tor_circuit": {
            "client": "Ground2",
            "guard": "SAT",
            "middle": "SAT",
            "exit": "UAV2"
        }
    },
    8: {
        "name": "Z2 Down - 多跳协作下行",
        "direction": "downlink",
        "links": [
            {"source": "SAT", "target": "UAV2", "rssi": "high"},
            {"source": "SAT", "target": "Ground2", "rssi": "low"},
            {"source": "UAV2", "target": "Ground2", "rssi": "coop"},
            {"source": "UAV2", "target": "Ground3", "rssi": "low"},
            {"source": "Ground2", "target": "Ground3", "rssi": "high"}
        ],
        "tor_circuit": {
            "client": "Ground3",
            "guard": "SAT",
            "middle": "SAT",
            "exit": "UAV2"
        }
    },
    9: {
        "name": "Z3 Down - T用户协作下行",
        "direction": "downlink",
        "links": [
            {"source": "SAT", "target": "UAV1", "rssi": "high"},
            {"source": "UAV1", "target": "Ground1", "rssi": "high"},
            {"source": "UAV1", "target": "Ground2", "rssi": "low"},
            {"source": "Ground1", "target": "Ground2", "rssi": "coop"}
        ],
        "tor_circuit": {
            "client": "Ground2",
            "guard": "SAT",
            "middle": "SAT",
            "exit": "UAV1"
        }
    },
    10: {
        "name": "Z4 Down - 混合下行+协作",
        "direction": "downlink",
        "links": [
            {"source": "SAT", "target": "Ground2", "rssi": "low"},
            {"source": "SAT", "target": "UAV2", "rssi": "high"},
            {"source": "UAV2", "target": "Ground3", "rssi": "high"},
            {"source": "Ground2", "target": "Ground3", "rssi": "coop"}
        ],
        "tor_circuit": {
            "client": "Ground3",
            "guard": "SAT",
            "middle": "SAT",
            "exit": "UAV2"
        }
    },
    11: {
        "name": "Z5 Down - 复杂多层协作",
        "direction": "downlink",
        "links": [
            {"source": "SAT", "target": "Ground2", "rssi": "low"},
            {"source": "SAT", "target": "UAV2", "rssi": "high"},
            {"source": "UAV2", "target": "Ground1", "rssi": "high"},
            {"source": "UAV2", "target": "Ground3", "rssi": "low"},
            {"source": "Ground2", "target": "Ground3", "rssi": "coop"},
            {"source": "Ground1", "target": "Ground3", "rssi": "high"}
        ],
        "tor_circuit": {
            "client": "Ground3",
            "guard": "SAT",
            "middle": "SAT",
            "exit": "UAV2"
        }
    },
    12: {
        "name": "Z6 Down - 终端协作下行",
        "direction": "downlink",
        "links": [
            {"source": "SAT", "target": "UAV1", "rssi": "high"},
            {"source": "UAV1", "target": "Ground1", "rssi": "high"},
            {"source": "SAT", "target": "Ground2", "rssi": "low"},
            {"source": "Ground2", "target": "Ground3", "rssi": "low"},
            {"source": "Ground1", "target": "Ground3", "rssi": "coop"}
        ],
        "tor_circuit": {
            "client": "Ground3",
            "guard": "SAT",
            "middle": "SAT",
            "exit": "UAV1"
        }
    }
}


def generate_tc_commands(delay_ms, bandwidth_mbps, loss_percent):
    """生成TC命令"""
    # netem参数：使用基础延迟的±25%作为抖动
    delay_variation = max(1, delay_ms * 0.25)

    tc_cmd = (
        f"sudo tc qdisc add dev lo root netem "
        f"delay {delay_ms:.2f}ms {delay_variation:.2f}ms distribution normal "
        f"rate {bandwidth_mbps:.2f}mbit "
        f"loss {loss_percent:.2f}%"
    )

    return [
        "sudo tc qdisc del dev lo root 2>/dev/null || true",
        tc_cmd
    ]


def generate_tor_mapping(topo_id):
    """为单个拓扑生成完整的Tor映射配置"""

    if topo_id not in TOPOLOGIES_PHYSICAL:
        print(f"❌ 拓扑 {topo_id} 未定义")
        return None

    phys = TOPOLOGIES_PHYSICAL[topo_id]
    topo_key = f"topo{topo_id:02d}"

    if topo_key not in TOPOLOGY_PARAMS:
        print(f"❌ 拓扑 {topo_key} 的网络参数未找到")
        return None

    params = TOPOLOGY_PARAMS[topo_key]

    # 从topology_params.json提取正确的网络参数
    end_to_end = params['end_to_end']
    delay_ms = end_to_end['delay_ms']
    bandwidth_mbps = end_to_end['rate_mbps']
    loss_percent = end_to_end['packet_loss_percent']

    # 生成TC命令
    tc_commands = generate_tc_commands(delay_ms, bandwidth_mbps, loss_percent)

    # 构建完整配置
    config = {
        "topology_id": topo_id,
        "topology_name": params['name'],
        "noma_config_ref": f"/home/ccc/pq-ntor-experiment/sagin-experiments/noma-topologies/configs/topology_{topo_id:02d}_*.json",
        "description": f"{params['name']} - {phys['direction']}",
        "physical_topology": {
            "links": phys['links'],
            "direction": phys['direction']
        },
        "tor_circuit_mapping": {
            "description": "3-hop Tor circuit mapped to SAGIN nodes",
            "circuit_path": ["Client", "Guard", "Middle", "Exit", "Target"],
            "roles": {
                "client": {
                    "sagin_node": phys['tor_circuit']['client'],
                    "node_type": "terminal",
                    "ip": "localhost",
                    "executable": "./client"
                },
                "guard": {
                    "sagin_node": phys['tor_circuit']['guard'],
                    "node_type": "satellite" if "SAT" in phys['tor_circuit']['guard'] else "aircraft",
                    "ip": "localhost",
                    "port": 6001,
                    "executable": "./relay",
                    "args": ["-r", "guard", "-p", "6001"]
                },
                "middle": {
                    "sagin_node": phys['tor_circuit']['middle'],
                    "node_type": "satellite",
                    "ip": "localhost",
                    "port": 6002,
                    "executable": "./relay",
                    "args": ["-r", "middle", "-p", "6002"]
                },
                "exit": {
                    "sagin_node": phys['tor_circuit']['exit'],
                    "node_type": "satellite" if "SAT" in phys['tor_circuit']['exit'] else "aircraft",
                    "ip": "localhost",
                    "port": 6003,
                    "executable": "./relay",
                    "args": ["-r", "exit", "-p", "6003"]
                },
                "directory": {
                    "sagin_node": "HUB",
                    "node_type": "server",
                    "ip": "localhost",
                    "port": 5000,
                    "executable": "./directory"
                }
            }
        },
        "network_simulation": {
            "method": "linux_tc_netem",
            "interface": "lo",
            "tc_commands": tc_commands,
            "aggregate_params": {
                "delay_ms": delay_ms,
                "bandwidth_mbps": bandwidth_mbps,
                "loss_percent": loss_percent
            }
        },
        "test_configuration": {
            "timeout_seconds": 60,
            "max_retries": 3,
            "retry_delay_seconds": 2,
            "target_url": "http://127.0.0.1:8000/test.html"
        }
    }

    return config


def main():
    """主函数：生成所有配置文件"""
    print("=" * 80)
    print("🔧 重新生成12拓扑配置文件（使用正确的网络参数）")
    print("=" * 80)
    print()

    CONFIG_DIR.mkdir(exist_ok=True, parents=True)

    configs_generated = 0

    for topo_id in range(1, 13):
        print(f"📝 生成 Topo{topo_id:02d} 配置...")

        config = generate_tor_mapping(topo_id)

        if config:
            output_file = CONFIG_DIR / f"topo{topo_id:02d}_tor_mapping.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            # 打印参数摘要
            params = config['network_simulation']['aggregate_params']
            print(f"  ✅ {config['topology_name']}")
            print(f"     方向: {config['physical_topology']['direction']}")
            print(f"     参数: delay={params['delay_ms']:.2f}ms, bw={params['bandwidth_mbps']:.2f}Mbps, loss={params['loss_percent']:.2f}%")
            print(f"     文件: {output_file}")
            print()

            configs_generated += 1
        else:
            print(f"  ❌ 配置生成失败")
            print()

    print("=" * 80)
    print(f"✅ 成功生成 {configs_generated}/12 个配置文件")
    print(f"📁 配置目录: {CONFIG_DIR}")
    print("=" * 80)
    print()
    print("下一步：运行实验")
    print(f"  cd {EXP_DIR}/scripts")
    print(f"  ./run_pq_ntor_12topologies.py --runs 10")


if __name__ == "__main__":
    main()
