#!/usr/bin/env python3
"""
自动生成12个拓扑的Tor电路映射配置文件
基于前端已定义的拓扑链路关系
"""

import json
import os
from pathlib import Path

# 配置目录
SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR.parent / "configs"
CONFIG_DIR.mkdir(exist_ok=True)

# 12种拓扑的定义（基于frontend/control-panel/index.html中的topologyLinks）
TOPOLOGIES = {
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
        },
        "network_params": {
            "delay_ms": 20,
            "bandwidth_mbps": 35,
            "loss_percent": 1.25
        }
    },

    2: {
        "name": "Z1 Up - 双路径",
        "direction": "uplink",
        "links": [
            {"source": "Ground3", "target": "Ground2", "rssi": "high"},
            {"source": "Ground2", "target": "SAT", "rssi": "low"},
            {"source": "Ground3", "target": "UAV2", "rssi": "low"},
            {"source": "UAV2", "target": "SAT", "rssi": "high"}
        ],
        "tor_circuit": {
            "client": "Ground3",
            "guard": "UAV2",  # 选择空天路径
            "middle": "SAT",
            "exit": "SAT"
        },
        "network_params": {
            "delay_ms": 25,
            "bandwidth_mbps": 40,
            "loss_percent": 0.8
        }
    },

    3: {
        "name": "Z3 Up - 双终端中继",
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
        },
        "network_params": {
            "delay_ms": 18,
            "bandwidth_mbps": 60,
            "loss_percent": 0.5
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
        },
        "network_params": {
            "delay_ms": 22,
            "bandwidth_mbps": 50,
            "loss_percent": 0.7
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
        },
        "network_params": {
            "delay_ms": 20,
            "bandwidth_mbps": 55,
            "loss_percent": 0.6
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
        },
        "network_params": {
            "delay_ms": 15,
            "bandwidth_mbps": 50,
            "loss_percent": 0.6
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
        },
        "network_params": {
            "delay_ms": 25,
            "bandwidth_mbps": 30,
            "loss_percent": 1.5
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
        },
        "network_params": {
            "delay_ms": 35,
            "bandwidth_mbps": 25,
            "loss_percent": 2.0
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
        },
        "network_params": {
            "delay_ms": 28,
            "bandwidth_mbps": 35,
            "loss_percent": 1.2
        }
    },

    10: {
        "name": "Z4 Down - 混合直连+单跳协作",
        "direction": "downlink",
        "links": [
            {"source": "SAT", "target": "UAV2", "rssi": "high"},
            {"source": "SAT", "target": "Ground2", "rssi": "low"},
            {"source": "UAV2", "target": "Ground2", "rssi": "coop"},
            {"source": "Ground2", "target": "Ground3", "rssi": "high"}
        ],
        "tor_circuit": {
            "client": "Ground3",
            "guard": "SAT",
            "middle": "SAT",
            "exit": "UAV2"
        },
        "network_params": {
            "delay_ms": 30,
            "bandwidth_mbps": 28,
            "loss_percent": 1.8
        }
    },

    11: {
        "name": "Z5 Down - 混合多跳协作",
        "direction": "downlink",
        "links": [
            {"source": "SAT", "target": "UAV2", "rssi": "high"},
            {"source": "SAT", "target": "Ground2", "rssi": "low"},
            {"source": "UAV2", "target": "Ground2", "rssi": "coop"},
            {"source": "Ground2", "target": "Ground1", "rssi": "high"},
            {"source": "Ground2", "target": "Ground3", "rssi": "low"},
            {"source": "Ground1", "target": "Ground3", "rssi": "coop"}
        ],
        "tor_circuit": {
            "client": "Ground3",
            "guard": "SAT",
            "middle": "SAT",
            "exit": "UAV2"
        },
        "network_params": {
            "delay_ms": 40,
            "bandwidth_mbps": 22,
            "loss_percent": 2.5
        }
    },

    12: {
        "name": "Z6 Down - 双中继协作下行",
        "direction": "downlink",
        "links": [
            {"source": "SAT", "target": "UAV1", "rssi": "high"},
            {"source": "SAT", "target": "Ground2", "rssi": "low"},
            {"source": "UAV1", "target": "Ground2", "rssi": "coop"},
            {"source": "UAV1", "target": "Ground1", "rssi": "high"},
            {"source": "Ground2", "target": "Ground3", "rssi": "high"}
        ],
        "tor_circuit": {
            "client": "Ground1",
            "guard": "SAT",
            "middle": "SAT",
            "exit": "UAV1"
        },
        "network_params": {
            "delay_ms": 32,
            "bandwidth_mbps": 30,
            "loss_percent": 1.6
        }
    }
}


def generate_tor_mapping_config(topo_id, topo_data):
    """为单个拓扑生成Tor映射配置"""

    circuit = topo_data["tor_circuit"]
    net_params = topo_data["network_params"]

    config = {
        "topology_id": topo_id,
        "topology_name": topo_data["name"],
        "noma_config_ref": f"/home/ccc/pq-ntor-experiment/sagin-experiments/noma-topologies/configs/topology_{topo_id:02d}_*.json",

        "description": f"{topo_data['name']} - {topo_data['direction']}",

        "physical_topology": {
            "links": topo_data["links"],
            "direction": topo_data["direction"]
        },

        "tor_circuit_mapping": {
            "description": "3-hop Tor circuit mapped to SAGIN nodes",
            "circuit_path": ["Client", "Guard", "Middle", "Exit", "Target"],

            "roles": {
                "client": {
                    "sagin_node": circuit["client"],
                    "node_type": get_node_type(circuit["client"]),
                    "ip": "localhost",
                    "executable": "./client"
                },
                "guard": {
                    "sagin_node": circuit["guard"],
                    "node_type": get_node_type(circuit["guard"]),
                    "ip": "localhost",
                    "port": 6001,
                    "executable": "./relay",
                    "args": ["-r", "guard", "-p", "6001"]
                },
                "middle": {
                    "sagin_node": circuit["middle"],
                    "node_type": get_node_type(circuit["middle"]),
                    "ip": "localhost",
                    "port": 6002,
                    "executable": "./relay",
                    "args": ["-r", "middle", "-p", "6002"]
                },
                "exit": {
                    "sagin_node": circuit["exit"],
                    "node_type": get_node_type(circuit["exit"]),
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

            "tc_commands": [
                "sudo tc qdisc del dev lo root 2>/dev/null || true",
                f"sudo tc qdisc add dev lo root netem delay {net_params['delay_ms']}ms {net_params['delay_ms']//4}ms distribution normal rate {net_params['bandwidth_mbps']}mbit loss {net_params['loss_percent']}%"
            ],

            "aggregate_params": net_params
        },

        "satellite_orbit_integration": {
            "enabled": True,
            "satellite_node": "SAT",
            "orbit_data_source": "satellite_orbit.py",
            "dynamic_parameters": {
                "position_update": "per_test_run",
                "delay_calculation": "distance_based",
                "elevation_constraint": 10.0
            }
        },

        "expected_performance": {
            "pq_handshake_us": 147,
            "circuit_build_ms": estimate_circuit_build_time(net_params),
            "total_rtt_ms": estimate_total_rtt(net_params),
            "throughput_mbps": int(net_params["bandwidth_mbps"] * 0.8),
            "success_rate_percent": estimate_success_rate(net_params)
        },

        "test_configuration": {
            "num_runs": 10,
            "timeout_seconds": 120,
            "target_url": "http://127.0.0.1:8000/",
            "metrics_to_collect": [
                "pq_handshake_time",
                "circuit_build_time",
                "http_get_time",
                "total_rtt",
                "throughput",
                "packet_loss",
                "success_flag"
            ]
        }
    }

    return config


def get_node_type(node_name):
    """获取节点类型"""
    if "SAT" in node_name:
        return "satellite"
    elif "UAV" in node_name:
        return "aircraft"
    elif "Ground" in node_name:
        return "terminal"
    else:
        return "unknown"


def estimate_circuit_build_time(net_params):
    """估算电路建立时间（基于延迟）"""
    # 假设电路建立需要3次RTT + PQ握手
    base_time = net_params["delay_ms"] * 2 * 3  # 3 RTT
    pq_overhead = 0.15  # PQ-NTOR额外15%开销
    return int(base_time * (1 + pq_overhead))


def estimate_total_rtt(net_params):
    """估算总RTT"""
    # 简单模型: 单向延迟 * 2 * 跳数
    return net_params["delay_ms"] * 2 * 3


def estimate_success_rate(net_params):
    """基于丢包率估算成功率"""
    loss = net_params["loss_percent"]
    if loss < 1.0:
        return 95
    elif loss < 2.0:
        return 90
    else:
        return 85


def main():
    print("=" * 60)
    print("  生成12个拓扑的Tor电路映射配置")
    print("=" * 60)

    for topo_id, topo_data in TOPOLOGIES.items():
        config = generate_tor_mapping_config(topo_id, topo_data)

        output_file = CONFIG_DIR / f"topo{topo_id:02d}_tor_mapping.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✅ 生成拓扑 {topo_id:02d}: {topo_data['name']}")
        print(f"   文件: {output_file}")
        print(f"   Tor电路: {config['tor_circuit_mapping']['roles']['client']['sagin_node']} "
              f"→ {config['tor_circuit_mapping']['roles']['guard']['sagin_node']} "
              f"→ {config['tor_circuit_mapping']['roles']['middle']['sagin_node']} "
              f"→ {config['tor_circuit_mapping']['roles']['exit']['sagin_node']}")
        print(f"   网络参数: Delay={config['network_simulation']['aggregate_params']['delay_ms']}ms, "
              f"BW={config['network_simulation']['aggregate_params']['bandwidth_mbps']}Mbps, "
              f"Loss={config['network_simulation']['aggregate_params']['loss_percent']}%")
        print()

    print("=" * 60)
    print(f"✅ 所有配置文件已生成到: {CONFIG_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
