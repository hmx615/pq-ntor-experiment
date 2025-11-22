#!/usr/bin/env python3
"""
生成所有12种NOMA拓扑配置文件
"""

import json
import os

# 拓扑定义数据
TOPOLOGIES = {
    3: {
        "name": "Z2 Up (Dual UAV)",
        "direction": "uplink",
        "hops": 3,
        "cooperation": False,
        "delay_ms": 35,
        "bandwidth_mbps": 50,
        "success_rate": 90,
        "pq_overhead": 0.42
    },
    4: {
        "name": "Z3 Up (Hybrid)",
        "direction": "uplink",
        "hops": 2.5,  # 混合2-3跳
        "cooperation": False,
        "delay_ms": 25,
        "bandwidth_mbps": 50,
        "success_rate": 92,
        "pq_overhead": 0.59
    },
    5: {
        "name": "Z5 Up (Complex Cooperation)",
        "direction": "uplink",
        "hops": 3,
        "cooperation": False,
        "delay_ms": 40,
        "bandwidth_mbps": 50,
        "success_rate": 88,
        "pq_overhead": 0.37
    },
    6: {
        "name": "Z6 Up (Three Terminals)",
        "direction": "uplink",
        "hops": 3,
        "cooperation": False,
        "delay_ms": 35,
        "bandwidth_mbps": 50,
        "success_rate": 90,
        "pq_overhead": 0.42
    },
    8: {
        "name": "Z2 Down (Single UAV + Coop)",
        "direction": "downlink",
        "hops": 3,
        "cooperation": True,
        "delay_ms": 35,
        "bandwidth_mbps": 100,
        "success_rate": 85,
        "pq_overhead": 0.42
    },
    9: {
        "name": "Z3 Down (Hybrid Downlink)",
        "direction": "downlink",
        "hops": 2.5,
        "cooperation": False,
        "delay_ms": 30,
        "bandwidth_mbps": 100,
        "success_rate": 90,
        "pq_overhead": 0.49
    },
    10: {
        "name": "Z4 Down (Dual Path)",
        "direction": "downlink",
        "hops": 3,
        "cooperation": False,
        "delay_ms": 40,
        "bandwidth_mbps": 100,
        "success_rate": 85,
        "pq_overhead": 0.37
    },
    11: {
        "name": "Z5 Down (Complex + Coop)",
        "direction": "downlink",
        "hops": 3.5,
        "cooperation": True,
        "delay_ms": 50,
        "bandwidth_mbps": 100,
        "success_rate": 80,
        "pq_overhead": 0.29
    },
    12: {
        "name": "Z6 Down (Three Terminals + Coop)",
        "direction": "downlink",
        "hops": 3.5,
        "cooperation": True,
        "delay_ms": 55,
        "bandwidth_mbps": 100,
        "success_rate": 80,
        "pq_overhead": 0.27
    }
}

def generate_topology_config(topo_id, topo_data):
    """生成单个拓扑配置"""
    config = {
        "topology_id": topo_id,
        "name": topo_data["name"],
        "direction": topo_data["direction"],
        "hops": topo_data["hops"],
        "cooperation": topo_data["cooperation"],
        "description": f"NOMA Topology {topo_id}: {topo_data['name']}",

        "links": generate_links(topo_id, topo_data),

        "tor_circuit": {
            "hops_count": int(topo_data["hops"]),
            "description": f"{int(topo_data['hops'])}-hop Tor circuit"
        },

        "noma_config": {
            "enabled": True,
            "cooperation": topo_data["cooperation"],
            "sic_enabled": True
        },

        "expected_performance": {
            "total_delay_ms": topo_data["delay_ms"],
            "pq_handshake_us": 147,
            "bottleneck_bw_mbps": topo_data["bandwidth_mbps"],
            "success_rate_percent": topo_data["success_rate"],
            "pq_overhead_percent": topo_data["pq_overhead"]
        }
    }

    return config

def generate_links(topo_id, topo_data):
    """生成链路配置"""
    links = []

    direction = topo_data["direction"]
    has_coop = topo_data["cooperation"]

    if direction == "uplink":
        # 上行拓扑链路示例
        if topo_id in [3, 5, 6]:
            # 多无人机场景
            links.append({
                "type": "air_ground_high",
                "delay_ms": 5,
                "bandwidth_mbps": 100,
                "loss_percent": 0.1
            })
            links.append({
                "type": "air_ground_low",
                "delay_ms": 15,
                "bandwidth_mbps": 50,
                "loss_percent": 1.0
            })
            links.append({
                "type": "air_space",
                "delay_ms": 10,
                "bandwidth_mbps": 50,
                "loss_percent": 0.5
            })
    else:
        # 下行拓扑链路示例
        links.append({
            "type": "space_ground_downlink_high",
            "delay_ms": 10,
            "bandwidth_mbps": 100,
            "loss_percent": 0.5
        })
        links.append({
            "type": "space_ground_downlink_low",
            "delay_ms": 30,
            "bandwidth_mbps": 50,
            "loss_percent": 2.0
        })

        if has_coop:
            # 添加协作链路
            links.append({
                "type": "noma_cooperation",
                "delay_ms": 5,
                "bandwidth_mbps": 100,
                "loss_percent": 0.1,
                "is_cooperation": True
            })

    return links

def main():
    """主函数"""
    output_dir = "../configs"
    os.makedirs(output_dir, exist_ok=True)

    # 生成拓扑3-6, 8-12的配置
    for topo_id, topo_data in TOPOLOGIES.items():
        config = generate_topology_config(topo_id, topo_data)

        # 生成文件名
        name_slug = topo_data["name"].split()[0].lower().replace("-", "")
        filename = f"topology_{topo_id:02d}_{name_slug}.json"
        filepath = os.path.join(output_dir, filename)

        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✓ Created: {filename}")

    print(f"\n✅ Generated {len(TOPOLOGIES)} topology configs")
    print(f"📁 Output directory: {output_dir}")
    print(f"\nTotal topologies: 12 (3 manual + 9 generated)")

if __name__ == "__main__":
    main()
