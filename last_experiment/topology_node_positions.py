#!/usr/bin/env python3
"""
12拓扑的3D节点坐标定义（地面终端聚集，UAV上方1km）

修正说明：
- UAV高度: 1000m
- 所有地面终端聚集在一起，彼此距离300-500m
- UAV在地面终端上方1km处（水平距离~1km）
- UAV-Ground斜距: √(1000² + 300~500²) ≈ 1044~1118m

节点命名规则：
- S1, S2: Single-hop用户（1跳直连卫星）
- T1, T2: Two-hop用户（2跳，需中继）
- R, R1, R2: Relay中继节点

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

# 地面终端中心位置（UAV下方）
GROUND_CENTER = np.array([1000.0, 0.0, GROUND_HEIGHT])

# 地面终端间距范围
D2D_MIN = 300.0  # 300m
D2D_MAX = 500.0  # 500m

# ========== 地面终端位置定义 ==========
# 所有地面终端在中心周围300-500m范围内

# 为确保可复现，使用固定偏移值
GROUND_OFFSETS = {
    's2_ground': np.array([-195.1, 278.8, 0.0]),      # 342m from center
    's2_r1_ground': np.array([285.3, -192.7, 0.0]),   # 346m from center
    's2_r2_ground': np.array([-425.3, -67.4, 0.0]),   # 430m from center
    's2_r_ground': np.array([158.7, 374.6, 0.0]),     # 407m from center
    't_ground': np.array([305.8, 149.3, 0.0]),        # 340m from center
    't1_ground': np.array([-273.9, -258.4, 0.0]),     # 376m from center
    't2_ground': np.array([419.7, 88.6, 0.0]),        # 429m from center
}

def get_ground_pos(name):
    """获取地面节点位置"""
    if name in GROUND_OFFSETS:
        return GROUND_CENTER + GROUND_OFFSETS[name]
    else:
        # 未预定义的节点，放在中心
        return GROUND_CENTER.copy()

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
            "s2_ground": get_ground_pos('s2_ground'),                 # 地面终端
            "s1_uav": np.array([0.0, 0.0, UAV_HEIGHT]),               # UAV上方
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
            "s2_r1_ground": get_ground_pos('s2_r1_ground'),           # 地面中继
            "s1_r2_uav": np.array([0.0, 0.0, UAV_HEIGHT]),            # UAV中继
            "t_ground": get_ground_pos('t_ground'),                   # T用户
        },
        "links": [
            ("s2_r1_ground", "sat", "天基上行-低RSSI"),
            ("s1_r2_uav", "sat", "天基上行-高RSSI"),
            ("t_ground", "s2_r1_ground", "D2D-近距离"),
            ("t_ground", "s1_r2_uav", "空/地上行-1km"),
        ]
    },

    "topo03": {
        "name": "Z3 Up - T用户协作NOMA",
        "description": "两个地面T用户通过UAV中继上行",
        "nodes": {
            "sat": SAT_POS,
            "s_r_uav": np.array([0.0, 0.0, UAV_HEIGHT]),              # UAV中继
            "t2_ground": get_ground_pos('t2_ground'),                 # T2
            "t1_ground": get_ground_pos('t1_ground'),                 # T1
        },
        "links": [
            ("s_r_uav", "sat", "卫星链路"),
            ("t2_ground", "s_r_uav", "空/地上行-1km"),
            ("t1_ground", "s_r_uav", "空/地上行-1km"),
        ]
    },

    "topo04": {
        "name": "Z4 Up - 混合直连+协作",
        "description": "S2(地面)直连，T通过S1/R(UAV)上行",
        "nodes": {
            "sat": SAT_POS,
            "s2_ground": get_ground_pos('s2_ground'),                 # S2直连
            "s1_r_uav": np.array([0.0, 0.0, UAV_HEIGHT]),             # S1/R UAV
            "t_ground": get_ground_pos('t_ground'),                   # T用户
        },
        "links": [
            ("s2_ground", "sat", "天基上行-低RSSI"),
            ("s1_r_uav", "sat", "天基上行-高RSSI"),
            ("t_ground", "s1_r_uav", "空/地上行-1km"),
        ]
    },

    "topo05": {
        "name": "Z5 Up - 多层树形结构",
        "description": "S2(地面)直连，T1/T2通过S1/R(UAV)上行",
        "nodes": {
            "sat": SAT_POS,
            "s2_ground": get_ground_pos('s2_ground'),                 # S2直连
            "s1_r_uav": np.array([0.0, 0.0, UAV_HEIGHT]),             # S1/R UAV
            "t1_ground": get_ground_pos('t1_ground'),                 # T1
            "t2_ground": get_ground_pos('t2_ground'),                 # T2
        },
        "links": [
            ("s2_ground", "sat", "天基上行-低RSSI"),
            ("s1_r_uav", "sat", "天基上行-高RSSI"),
            ("t1_ground", "s1_r_uav", "空/地上行-1km"),
            ("t2_ground", "s1_r_uav", "空/地上行-1km"),
        ]
    },

    "topo06": {
        "name": "Z6 Up - 双UAV中继+T用户",
        "description": "两个UAV分别中继一个地面T用户",
        "nodes": {
            "sat": SAT_POS,
            "s1_r1_uav": np.array([0.0, 0.0, UAV_HEIGHT]),            # S1/R1 UAV
            "s2_r2_uav": np.array([0.0, 800.0, UAV_HEIGHT]),          # S2/R2 UAV，相距800m
            "t1_ground": get_ground_pos('t1_ground'),                 # T1
            "t2_ground": get_ground_pos('t2_ground'),                 # T2
        },
        "links": [
            ("s1_r1_uav", "sat", "天基上行-高RSSI"),
            ("s2_r2_uav", "sat", "天基上行-低RSSI"),
            ("t1_ground", "s1_r1_uav", "空/地上行-1km"),
            ("t2_ground", "s2_r2_uav", "空/地上行-1km"),
        ]
    },

    # =======================================
    # 下行拓扑 (7-12): 有协作链路
    # =======================================

    "topo07": {
        "name": "Z1 Down - 直连NOMA+协作",
        "description": "SAT → S1(UAV,高RSSI) + S2(地面,低RSSI), S1→S2协作",
        "nodes": {
            "sat": SAT_POS,
            "s2_ground": get_ground_pos('s2_ground'),                 # S2地面终端（对应topo01）
            "s1_uav": np.array([0.0, 0.0, UAV_HEIGHT]),               # S1 UAV（对应topo01）
        },
        "links": [
            ("sat", "s1_uav", "天基下行-高RSSI"),                      # 对称：topo01的s1_uav→sat
            ("sat", "s2_ground", "天基下行-低RSSI"),                   # 对称：topo01的s2_ground→sat
            ("s1_uav", "s2_ground", "空/地下行-1km"),                  # 额外协作链路
        ]
    },

    "topo08": {
        "name": "Z2 Down - T协作接入+协作",
        "description": "SAT → S1/R2(UAV) + S2/R1(地面) → T(地面), S1→S2协作",
        "nodes": {
            "sat": SAT_POS,
            "s2_r1_ground": get_ground_pos('s2_r1_ground'),           # 地面中继（对应topo02）
            "s1_r2_uav": np.array([0.0, 0.0, UAV_HEIGHT]),            # UAV中继（对应topo02）
            "t_ground": get_ground_pos('t_ground'),                   # T用户（对应topo02）
        },
        "links": [
            ("sat", "s2_r1_ground", "天基下行-低RSSI"),                # 对称：topo02的s2_r1_ground→sat
            ("sat", "s1_r2_uav", "天基下行-高RSSI"),                   # 对称：topo02的s1_r2_uav→sat
            ("s1_r2_uav", "s2_r1_ground", "协作链路-1km"),             # 额外协作链路
            ("s2_r1_ground", "t_ground", "D2D-近距离"),                # 对称：topo02的t_ground→s2_r1_ground
            ("s1_r2_uav", "t_ground", "空/地下行-1km"),                # 对称：topo02的t_ground→s1_r2_uav
        ]
    },

    "topo09": {
        "name": "Z3 Down - T用户协作下行",
        "description": "SAT → S/R(UAV) → T1(地面) + T2(地面), T1→T2协作",
        "nodes": {
            "sat": SAT_POS,
            "s_r_uav": np.array([0.0, 0.0, UAV_HEIGHT]),              # S/R UAV中继
            "t1_ground": get_ground_pos('t1_ground'),                 # T1
            "t2_ground": get_ground_pos('t2_ground'),                 # T2
        },
        "links": [
            ("sat", "s_r_uav", "卫星链路"),
            ("s_r_uav", "t1_ground", "空/地下行-1km"),
            ("s_r_uav", "t2_ground", "空/地下行-1km"),
            ("t1_ground", "t2_ground", "D2D协作-近距离"),
        ]
    },

    "topo10": {
        "name": "Z4 Down - 混合直连+协作",
        "description": "SAT → S2(地面)直连 + SAT → S1/R(UAV) → T(地面), S1→S2协作",
        "nodes": {
            "sat": SAT_POS,
            "s2_ground": get_ground_pos('s2_ground'),                 # S2直连（对应topo04）
            "s1_r_uav": np.array([0.0, 0.0, UAV_HEIGHT]),             # S1/R UAV（对应topo04）
            "t_ground": get_ground_pos('t_ground'),                   # T用户（对应topo04）
        },
        "links": [
            ("sat", "s2_ground", "天基下行-低RSSI"),                   # 对称：topo04的s2_ground→sat
            ("sat", "s1_r_uav", "天基下行-高RSSI"),                    # 对称：topo04的s1_r_uav→sat
            ("s1_r_uav", "s2_ground", "协作链路-1km"),                 # 额外协作链路
            ("s1_r_uav", "t_ground", "空/地下行-1km"),                 # 对称：topo04的t_ground→s1_r_uav
        ]
    },

    "topo11": {
        "name": "Z5 Down - NOMA接收+转发+T协作",
        "description": "SAT → S1(UAV) + S2/R(地面) [NOMA], S1→S2/R协作, S2/R→T1/T2, T1↔T2协作",
        "nodes": {
            "sat": SAT_POS,
            "s1_uav": np.array([0.0, 0.0, UAV_HEIGHT]),               # S1 UAV (高RSSI)
            "s2_r_ground": get_ground_pos('s2_r_ground'),             # S2/R地面 (低RSSI + 转发)
            "t1_ground": get_ground_pos('t1_ground'),                 # T1
            "t2_ground": get_ground_pos('t2_ground'),                 # T2
        },
        "links": [
            ("sat", "s1_uav", "天基下行-高RSSI"),                      # NOMA组内
            ("sat", "s2_r_ground", "天基下行-低RSSI"),                 # NOMA组内
            ("s1_uav", "s2_r_ground", "协作链路-1km"),                 # UAV协作到地面
            ("s2_r_ground", "t1_ground", "D2D-近距离"),                # S2/R转发给T1
            ("s2_r_ground", "t2_ground", "D2D-近距离"),                # S2/R转发给T2
            ("t1_ground", "t2_ground", "D2D协作-近距离"),              # T用户间协作
        ]
    },

    "topo12": {
        "name": "Z6 Down - 双中继NOMA接收+协作+转发",
        "description": "SAT → S1/R1(UAV) + S2/R2(地面) [NOMA], S1/R1→S2/R2协作, S1/R1→T1, S2/R2→T2",
        "nodes": {
            "sat": SAT_POS,
            "s1_r1_uav": np.array([0.0, 0.0, UAV_HEIGHT]),            # S1/R1 UAV (高RSSI)
            "s2_r2_ground": get_ground_pos('s2_r2_ground'),           # S2/R2地面 (低RSSI，按截图)
            "t1_ground": get_ground_pos('t1_ground'),                 # T1
            "t2_ground": get_ground_pos('t2_ground'),                 # T2
        },
        "links": [
            ("sat", "s1_r1_uav", "天基下行-高RSSI"),                   # NOMA组内
            ("sat", "s2_r2_ground", "天基下行-低RSSI"),                # NOMA组内
            ("s1_r1_uav", "s2_r2_ground", "协作链路-1km"),             # UAV协作到地面
            ("s1_r1_uav", "t1_ground", "空/地下行-1km"),               # S1/R1转发给T1
            ("s2_r2_ground", "t2_ground", "D2D-近距离"),               # S2/R2转发给T2
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
    print("12拓扑节点定义总览（地面终端聚集，UAV上方1km）")
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

        # 验证地面终端间距
        print("\n" + "=" * 80)
        print("地面终端间距验证")
        print("=" * 80)

        ground_positions = list(GROUND_OFFSETS.values())
        max_dist = 0
        min_dist = float('inf')

        for i, pos1 in enumerate(ground_positions):
            for j, pos2 in enumerate(ground_positions[i+1:], i+1):
                dist = np.linalg.norm(pos1 - pos2)
                max_dist = max(max_dist, dist)
                min_dist = min(min_dist, dist)

        print(f"地面终端间最小距离: {min_dist:.1f}m")
        print(f"地面终端间最大距离: {max_dist:.1f}m")

        if min_dist >= 150 and max_dist <= 800:
            print("✅ 地面终端间距合理 (150-800m范围)")
        else:
            print("⚠️ 地面终端间距可能需要调整")
    else:
        print("⚠️  发现问题，请检查")
