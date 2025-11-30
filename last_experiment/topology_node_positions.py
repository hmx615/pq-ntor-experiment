#!/usr/bin/env python3
"""
12拓扑的3D节点坐标定义（基于官方拓扑定义）

节点命名规则：
- S1, S2: Single-hop用户（1跳直连卫星）
- T1, T2: Two-hop用户（2跳，需中继）
- R, R1, R2: Relay中继节点
- S1/R: 同时担任S和R角色
- S2/R: 同时担任S和R角色

RSSI与距离关系：
- 高RSSI: 近距离（地面500m-1km，空中2-3km）
- 低RSSI: 远距离（地面5-10km，空中5-8km）

参考高度：
- 卫星: 813,000m
- UAV: 1,000m
- 地面: 0m
"""

import numpy as np

# ========== 固定参考点 ==========

# 卫星位置（固定）
SAT_POS = np.array([0.0, 0.0, 813000.0])  # 813km高度

# UAV标准高度
UAV_HEIGHT = 1000.0  # 1km

# 地面高度
GROUND_HEIGHT = 0.0

# ========== 12拓扑节点定义 ==========

TOPOLOGY_NODES = {

    # =======================================
    # 上行拓扑 (1-6): 无协作链路
    # =======================================

    "topo01": {
        "name": "Z1 Up - 直连NOMA",
        "description": "SAT ← S2(地面,低RSSI) + S1(UAV,高RSSI)",
        "nodes": {
            "sat": SAT_POS,
            "s2_ground": np.array([8000.0, 0.0, GROUND_HEIGHT]),      # 地面远端，8km
            "s1_uav": np.array([2000.0, 0.0, UAV_HEIGHT]),            # UAV近端，2km
        },
        "links": [
            ("s2_ground", "sat", "天基上行-低RSSI"),
            ("s1_uav", "sat", "天基上行-高RSSI"),
        ]
    },

    "topo02": {
        "name": "Z1 Up - T协作接入(混合双路径)",
        "description": "T通过S2/R1(地面)或S1/R2(UAV)双路径上行",
        "nodes": {
            "sat": SAT_POS,
            "s2_r1_ground": np.array([8000.0, 0.0, GROUND_HEIGHT]),   # 地面中继，远端
            "s1_r2_uav": np.array([2000.0, 0.0, UAV_HEIGHT]),         # UAV中继，近端
            "t_ground": np.array([7500.0, 0.0, GROUND_HEIGHT]),       # T用户，地面 [优化: 1000m→500m D2D距离]
        },
        "links": [
            ("s2_r1_ground", "sat", "天基上行-低RSSI"),
            ("s1_r2_uav", "sat", "天基上行-高RSSI"),
            ("t_ground", "s2_r1_ground", "空/地-高RSSI(近距离)"),
            ("t_ground", "s1_r2_uav", "空/地-低RSSI(远距离)"),
        ]
    },

    "topo03": {
        "name": "Z3 Up - T用户协作NOMA",
        "description": "两个地面T用户通过UAV中继上行",
        "nodes": {
            "sat": SAT_POS,
            "s_r_uav": np.array([5000.0, 0.0, UAV_HEIGHT]),           # UAV中继
            "t2_ground": np.array([9000.0, 0.0, GROUND_HEIGHT]),      # T2远端
            "t1_ground": np.array([3500.0, 0.0, GROUND_HEIGHT]),      # T1近端
        },
        "links": [
            ("s_r_uav", "sat", "卫星链路(无标注)"),
            ("t2_ground", "s_r_uav", "空/地上行-低RSSI"),
            ("t1_ground", "s_r_uav", "空/地上行-高RSSI"),
        ]
    },

    "topo04": {
        "name": "Z4 Up - 混合直连+协作",
        "description": "S2(地面)直连，T通过S1/R(UAV)上行",
        "nodes": {
            "sat": SAT_POS,
            "s2_ground": np.array([8000.0, 0.0, GROUND_HEIGHT]),      # S2直连，远端
            "s1_r_uav": np.array([2000.0, 0.0, UAV_HEIGHT]),          # S1/R UAV，近端
            "t_ground": np.array([1500.0, 0.0, GROUND_HEIGHT]),       # T用户
        },
        "links": [
            ("s2_ground", "sat", "天基上行-低RSSI"),
            ("s1_r_uav", "sat", "天基上行-高RSSI"),
            ("t_ground", "s1_r_uav", "空/地链路"),
        ]
    },

    "topo05": {
        "name": "Z5 Up - 多层树形结构",
        "description": "S2(地面)直连，T1/T2通过S1/R(UAV)上行",
        "nodes": {
            "sat": SAT_POS,
            "s2_ground": np.array([8000.0, 0.0, GROUND_HEIGHT]),      # S2直连，远端
            "s1_r_uav": np.array([2000.0, 0.0, UAV_HEIGHT]),          # S1/R UAV，近端
            "t1_ground": np.array([1500.0, 0.0, GROUND_HEIGHT]),      # T1近端
            "t2_ground": np.array([5000.0, 0.0, GROUND_HEIGHT]),      # T2远端
        },
        "links": [
            ("s2_ground", "sat", "天基上行-低RSSI"),
            ("s1_r_uav", "sat", "天基上行-高RSSI"),
            ("t1_ground", "s1_r_uav", "空/地-高RSSI"),
            ("t2_ground", "s1_r_uav", "空/地-低RSSI"),
        ]
    },

    "topo06": {
        "name": "Z6 Up - 双UAV中继+T用户",
        "description": "两个UAV分别中继一个地面T用户",
        "nodes": {
            "sat": SAT_POS,
            "s1_r1_uav": np.array([2000.0, 0.0, UAV_HEIGHT]),         # S1/R1 UAV近端
            "s2_r2_uav": np.array([7000.0, 0.0, UAV_HEIGHT]),         # S2/R2 UAV远端
            "t1_ground": np.array([1500.0, 0.0, GROUND_HEIGHT]),      # T1近端
            "t2_ground": np.array([7500.0, 0.0, GROUND_HEIGHT]),      # T2远端
        },
        "links": [
            ("s1_r1_uav", "sat", "天基上行-高RSSI"),
            ("s2_r2_uav", "sat", "天基上行-低RSSI"),
            ("t1_ground", "s1_r1_uav", "空/地-高RSSI"),
            ("t2_ground", "s2_r2_uav", "空/地-低RSSI"),
        ]
    },

    # =======================================
    # 下行拓扑 (7-12): 有协作链路
    # =======================================

    "topo07": {
        "name": "Z1 Down - 直连NOMA+协作",
        "description": "SAT → S1/R(UAV) + S2(地面), S1→S2协作",
        "nodes": {
            "sat": SAT_POS,
            "s1_r_uav": np.array([2000.0, 0.0, UAV_HEIGHT]),          # S1/R UAV近端
            "s2_ground": np.array([8000.0, 0.0, GROUND_HEIGHT]),      # S2地面远端
        },
        "links": [
            ("sat", "s1_r_uav", "天基下行-高RSSI"),
            ("sat", "s2_ground", "天基下行-低RSSI"),
            ("s1_r_uav", "s2_ground", "空/地协作(单向)"),
        ]
    },

    "topo08": {
        "name": "Z2 Down - 多跳协作下行",
        "description": "SAT → S1/R1(UAV) + S2/R2(地面) → T(地面)",
        "nodes": {
            "sat": SAT_POS,
            "s1_r1_uav": np.array([2000.0, 0.0, UAV_HEIGHT]),         # S1/R1 UAV近端
            "s2_r2_ground": np.array([8000.0, 0.0, GROUND_HEIGHT]),   # S2/R2 地面远端
            "t_ground": np.array([7500.0, 0.0, GROUND_HEIGHT]),       # T用户（靠近S2/R2）
        },
        "links": [
            ("sat", "s1_r1_uav", "天基下行-高RSSI"),
            ("sat", "s2_r2_ground", "天基下行-低RSSI"),
            ("s1_r1_uav", "s2_r2_ground", "协作链路"),
            ("s1_r1_uav", "t_ground", "空/地-低RSSI(远距离)"),
            ("s2_r2_ground", "t_ground", "空/地-高RSSI(近距离)"),
        ]
    },

    "topo09": {
        "name": "Z3 Down - T用户协作下行",
        "description": "SAT → S/R(UAV) → T1(地面) + T2(地面), T1→T2协作",
        "nodes": {
            "sat": SAT_POS,
            "s_r_uav": np.array([5000.0, 0.0, UAV_HEIGHT]),           # S/R UAV中继
            "t1_ground": np.array([3500.0, 0.0, GROUND_HEIGHT]),      # T1近端
            "t2_ground": np.array([4000.0, 0.0, GROUND_HEIGHT]),      # T2远端 [优化: 1000m→500m D2D距离]
        },
        "links": [
            ("sat", "s_r_uav", "卫星链路(无标注)"),
            ("s_r_uav", "t1_ground", "空/地-高RSSI"),
            ("s_r_uav", "t2_ground", "空/地-低RSSI"),
            ("t1_ground", "t2_ground", "协作链路(D2D)"),  # 距离仅1km，避免0.3Mbps问题
        ]
    },

    "topo10": {
        "name": "Z4 Down - 混合直连+单跳协作",
        "description": "SAT → S1(UAV) + S2/R(地面) → T(地面)",
        "nodes": {
            "sat": SAT_POS,
            "s1_uav": np.array([2000.0, 0.0, UAV_HEIGHT]),            # S1 UAV近端
            "s2_r_ground": np.array([8000.0, 0.0, GROUND_HEIGHT]),    # S2/R地面远端
            "t_ground": np.array([7500.0, 0.0, GROUND_HEIGHT]),       # T用户（靠近S2/R）
        },
        "links": [
            ("sat", "s1_uav", "天基下行-高RSSI"),
            ("sat", "s2_r_ground", "天基下行-低RSSI"),
            ("s1_uav", "s2_r_ground", "协作链路"),
            ("s2_r_ground", "t_ground", "空/地链路"),
        ]
    },

    "topo11": {
        "name": "Z5 Down - 混合直连+多跳协作",
        "description": "SAT → S1(UAV) + S2/R(地面) → T1/T2(地面)",
        "nodes": {
            "sat": SAT_POS,
            "s1_uav": np.array([2000.0, 0.0, UAV_HEIGHT]),            # S1 UAV近端
            "s2_r_ground": np.array([8000.0, 0.0, GROUND_HEIGHT]),    # S2/R地面远端
            "t1_ground": np.array([7500.0, 0.0, GROUND_HEIGHT]),      # T1近端（靠近S2/R, 距S2/R 500m）
            "t2_ground": np.array([8500.0, 0.0, GROUND_HEIGHT]),      # T2远端（距S2/R 500m, 距T1 1000m）[优化: 避免与S2/R重叠]
        },
        "links": [
            ("sat", "s1_uav", "天基下行-高RSSI"),
            ("sat", "s2_r_ground", "天基下行-低RSSI"),
            ("s1_uav", "s2_r_ground", "协作链路"),
            ("s2_r_ground", "t1_ground", "空/地-高RSSI"),
            ("s2_r_ground", "t2_ground", "空/地-低RSSI"),
            ("t1_ground", "t2_ground", "协作链路(D2D)"),
        ]
    },

    "topo12": {
        "name": "Z6 Down - 双中继协作下行",
        "description": "SAT → S1/R1(UAV) + S2/R2(地面) → T1/T2(地面)",
        "nodes": {
            "sat": SAT_POS,
            "s1_r1_uav": np.array([2000.0, 0.0, UAV_HEIGHT]),         # S1/R1 UAV近端
            "s2_r2_ground": np.array([8000.0, 0.0, GROUND_HEIGHT]),   # S2/R2地面远端
            "t1_ground": np.array([1500.0, 0.0, GROUND_HEIGHT]),      # T1近端（靠近S1/R1）
            "t2_ground": np.array([7500.0, 0.0, GROUND_HEIGHT]),      # T2远端（靠近S2/R2）
        },
        "links": [
            ("sat", "s1_r1_uav", "天基下行-高RSSI"),
            ("sat", "s2_r2_ground", "天基下行-低RSSI"),
            ("s1_r1_uav", "s2_r2_ground", "协作链路"),
            ("s1_r1_uav", "t1_ground", "空/地链路"),
            ("s2_r2_ground", "t2_ground", "空/地链路"),
        ]
    },
}


def get_topology_nodes(topo_id):
    """获取指定拓扑的节点坐标"""
    if topo_id not in TOPOLOGY_NODES:
        raise ValueError(f"Unknown topology: {topo_id}")
    return TOPOLOGY_NODES[topo_id]


def list_all_topologies():
    """列出所有拓扑"""
    print("=" * 80)
    print("12拓扑节点定义总览")
    print("=" * 80)

    for topo_id in sorted(TOPOLOGY_NODES.keys()):
        topo = TOPOLOGY_NODES[topo_id]
        print(f"\n{topo_id}: {topo['name']}")
        print(f"  描述: {topo['description']}")
        print(f"  节点数: {len(topo['nodes'])}")
        print(f"  链路数: {len(topo['links'])}")


if __name__ == "__main__":
    list_all_topologies()

    # 验证所有拓扑定义完整
    print("\n" + "=" * 80)
    print("验证结果")
    print("=" * 80)

    all_ok = True
    for topo_id in TOPOLOGY_NODES:
        topo = TOPOLOGY_NODES[topo_id]

        # 检查必需字段
        if 'nodes' not in topo or 'links' not in topo:
            print(f"❌ {topo_id}: 缺少nodes或links定义")
            all_ok = False
            continue

        # 检查链路引用的节点是否存在
        for link in topo['links']:
            node1, node2, link_type = link
            if node1 not in topo['nodes'] and node1 != 'sat':
                print(f"❌ {topo_id}: 链路引用了不存在的节点 {node1}")
                all_ok = False
            if node2 not in topo['nodes'] and node2 != 'sat':
                print(f"❌ {topo_id}: 链路引用了不存在的节点 {node2}")
                all_ok = False

    if all_ok:
        print("✅ 所有12拓扑定义完整，链路引用正确")
    else:
        print("⚠️  发现问题，请检查")
