# SAGIN环境复用指南

**用途**: 说明如何将SAGIN环境用于其他课题（如波束仿真）
**版本**: v1.0
**日期**: 2025-11-13

---

## 📋 可复用性评估

### ✅ 可直接复用的部分

| 组件 | 用途 | 复用难度 |
|------|------|---------|
| Docker网络架构 | 7节点SAGIN拓扑 | ⭐ 简单 |
| 网络延迟控制（tc） | 链路延迟仿真 | ⭐ 简单 |
| 链路启用/禁用（iptables） | 动态拓扑 | ⭐ 简单 |
| 轨道仿真器（orbit_simulator.py） | 卫星位置计算 | ⭐⭐ 中等 |
| 拓扑管理器（network_topology_manager.py） | 网络控制 | ⭐⭐ 中等 |
| SAGIN配置（sagin_topology_config.json） | 节点定义 | ⭐ 简单 |

### ⚠️ 需要替换的部分

| 组件 | 当前用途 | 替换方案 |
|------|---------|---------|
| PQ-NTOR程序 | 洋葱路由 | 替换为你的波束仿真程序 |
| Docker镜像 | PQ-NTOR环境 | 重新构建包含波束仿真软件的镜像 |
| 测试脚本 | PQ-NTOR测试 | 修改为波束仿真测试逻辑 |

---

## 🔄 复用方案设计

### 方案A: 最小修改（推荐）

**保留**:
- Docker网络基础设施
- 7节点拓扑结构
- tc/iptables网络控制
- 轨道仿真器

**替换**:
- 容器中的应用程序（PQ-NTOR → 波束仿真）
- 测试脚本逻辑
- 数据收集方式

**工作量**: 1-2天

### 方案B: 完全重构

**保留**:
- SAGIN拓扑概念
- 配置文件格式

**重写**:
- 新的Docker镜像
- 新的测试框架
- 新的分析工具

**工作量**: 3-5天

---

## 📝 波束仿真适配步骤

### 步骤1: 创建波束仿真Docker镜像

**示例Dockerfile** (`docker/Dockerfile.beam-sim`):

```dockerfile
FROM ubuntu:22.04

# 安装基础依赖
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    iproute2 iptables iputils-ping \
    net-tools tcpdump netcat curl

# 安装波束仿真相关库（示例）
RUN pip3 install numpy scipy matplotlib

# 复制你的波束仿真程序
COPY beam_simulation/ /root/beam-sim/

# 设置工作目录
WORKDIR /root/beam-sim

# 启动脚本
RUN echo '#!/bin/bash\n\
echo "SAGIN Beam Simulation Node"\n\
echo "==========================="\n\
echo "Network configuration:"\n\
ip addr show\n\
echo ""\n\
echo "Container ready. Keeping alive..."\n\
exec tail -f /dev/null\n\
' > /root/start.sh && chmod +x /root/start.sh

CMD ["/root/start.sh"]
```

**构建命令**:
```bash
docker build -t sagin-beam-sim:latest -f docker/Dockerfile.beam-sim .
```

### 步骤2: 修改拓扑配置

保持原有的7节点结构，但调整参数用于波束仿真：

```json
{
  "satellites": {
    "Sat-1": {
      "tle_line1": "...",
      "tle_line2": "...",
      "beam_parameters": {
        "frequency_ghz": 12.0,
        "beam_width_deg": 0.5,
        "transmit_power_dbm": 40.0,
        "antenna_gain_dbi": 30.0
      }
    }
  },

  "ground_stations": {
    "GS-Beijing": {
      "latitude": 39.9,
      "longitude": 116.4,
      "antenna_parameters": {
        "diameter_m": 3.0,
        "efficiency": 0.65,
        "noise_temperature_k": 50.0
      }
    }
  }
}
```

### 步骤3: 创建波束仿真测试脚本

**基本框架** (`scripts/sagin_beam_sim_test.py`):

```python
#!/usr/bin/env python3
"""
SAGIN波束仿真测试
复用SAGIN网络基础设施，运行波束仿真实验
"""

import json
import subprocess
from pathlib import Path
from network_topology_manager import NetworkTopologyManager
from orbit_simulator import OrbitSimulator

class SAGINBeamSimTest:
    """SAGIN波束仿真测试"""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = self._load_config()

        self.network_name = 'sagin_net'
        self.image_name = 'sagin-beam-sim:latest'

        self.containers = {}

    def _load_config(self):
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def setup_network(self):
        """创建Docker网络（复用原有代码）"""
        subprocess.run([
            'docker', 'network', 'create',
            '--subnet=172.20.0.0/16',
            self.network_name
        ], check=False)

    def create_containers(self):
        """创建Docker容器（复用原有逻辑）"""
        nodes = [
            {'name': 'Sat-1', 'ip': '172.20.1.11'},
            {'name': 'Sat-2', 'ip': '172.20.1.12'},
            # ... 其他节点
        ]

        for node in nodes:
            subprocess.run([
                'docker', 'run', '-d',
                '--name', f"sagin_{node['name'].lower()}",
                '--network', self.network_name,
                '--ip', node['ip'],
                '--cap-add', 'NET_ADMIN',
                '--privileged',
                self.image_name,
                '/root/start.sh'
            ])

    def run_beam_simulation(self, scenario):
        """
        运行波束仿真实验
        这里是你的核心业务逻辑
        """
        # 1. 计算卫星位置（使用轨道仿真器）
        sat_position = self.orbit_sim.get_position('Sat-1', time)

        # 2. 计算可见性
        visibility = self.check_visibility(sat_position, gs_position)

        # 3. 如果可见，运行波束仿真
        if visibility:
            # 在容器中运行你的波束仿真程序
            result = subprocess.run([
                'docker', 'exec', 'sagin_sat-1',
                'python3', '/root/beam-sim/run_simulation.py',
                '--target', 'GS-Beijing',
                '--frequency', '12.0',
                '--power', '40.0'
            ], capture_output=True, text=True)

            # 解析结果
            return self.parse_results(result.stdout)

    def cleanup(self):
        """清理容器和网络（复用原有代码）"""
        # 删除容器
        subprocess.run(['docker', 'ps', '-a', '-q', '--filter', 'name=sagin_'],
                      capture_output=True, text=True)
        # 删除网络
        subprocess.run(['docker', 'network', 'rm', self.network_name],
                      check=False)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='SAGIN波束仿真测试')
    parser.add_argument('--config', default='configs/sagin_topology_config.json')
    parser.add_argument('--scenario', default='all')

    args = parser.parse_args()

    # 创建测试实例
    tester = SAGINBeamSimTest(args.config)

    try:
        # 设置网络
        tester.setup_network()

        # 创建容器
        tester.create_containers()

        # 运行仿真
        results = tester.run_beam_simulation(args.scenario)

        # 保存结果
        print(f"仿真完成: {results}")

    finally:
        # 清理
        tester.cleanup()

if __name__ == '__main__':
    import sys
    sys.exit(main())
```

### 步骤4: 数据收集和分析

```python
# 复用analyze_pq_comparison.py的框架
# 修改数据处理逻辑为波束仿真相关指标

def analyze_beam_results(csv_file):
    """分析波束仿真结果"""
    import pandas as pd

    df = pd.read_csv(csv_file)

    # 计算波束相关指标
    metrics = {
        'avg_signal_strength': df['signal_strength_dbm'].mean(),
        'avg_snr': df['snr_db'].mean(),
        'coverage_area': df['coverage_km2'].sum(),
        'handover_success_rate': df['handover_success'].mean() * 100
    }

    return metrics
```

---

## 🔧 关键修改点

### 1. Docker镜像

**PQ-NTOR镜像** → **波束仿真镜像**

| 内容 | PQ-NTOR | 波束仿真 |
|------|---------|---------|
| 基础镜像 | ubuntu:22.04 | ubuntu:22.04 |
| 主要依赖 | liboqs, OpenSSL | numpy, scipy, matplotlib |
| 程序 | relay, client, directory | beam_sim, antenna_model |
| 数据 | 握手时间 | 信号强度、SNR、覆盖范围 |

### 2. 测试逻辑

**PQ-NTOR测试** → **波束仿真测试**

| 内容 | PQ-NTOR | 波束仿真 |
|------|---------|---------|
| 测试目标 | 电路建立时间 | 波束覆盖、链路质量 |
| 输入参数 | 跳数、路径 | 频率、功率、天线参数 |
| 输出指标 | 延迟、成功率 | 信号强度、SNR、误码率 |
| 测试场景 | 4个路径场景 | 多个波束指向场景 |

### 3. 分析工具

**对比分析** → **性能评估**

```python
# PQ-NTOR: 对比两种协议
analyze_pq_comparison(pq_results, traditional_results)

# 波束仿真: 评估不同配置
analyze_beam_performance(
    frequencies=[10.0, 12.0, 14.0],
    powers=[30, 35, 40],
    scenarios=['urban', 'suburban', 'rural']
)
```

---

## 📦 可直接复用的模块

### 模块1: network_topology_manager.py ✅

**功能**: 管理Docker网络拓扑
**复用方式**: 直接使用，无需修改

```python
from network_topology_manager import NetworkTopologyManager

# 创建管理器
manager = NetworkTopologyManager(config_file, dry_run=False)

# 应用网络延迟（tc）
manager.apply_link_delay('Sat-1', '172.20.3.31', delay_ms=10.0)

# 禁用链路（iptables）
manager.disable_link('Sat-1', '172.20.1.12')

# 启用链路
manager.enable_link('Sat-1', '172.20.1.12')
```

### 模块2: orbit_simulator.py ✅

**功能**: 计算卫星位置和可见性
**复用方式**: 直接使用，可能需要添加新方法

```python
from orbit_simulator import OrbitSimulator

# 创建仿真器
sim = OrbitSimulator(config_file)

# 获取卫星位置
position = sim.get_satellite_position('Sat-1', timestamp)
# 返回: (lat, lon, alt)

# 计算可见性
visible = sim.is_visible('Sat-1', 'GS-Beijing', timestamp)

# 计算距离
distance_km = sim.calculate_distance('Sat-1', 'GS-Beijing', timestamp)
```

### 模块3: 配置文件格式 ✅

**复用方式**: 保持JSON结构，添加你的参数

```json
{
  "satellites": {
    "Sat-1": {
      // 保留轨道参数
      "tle_line1": "...",
      "tle_line2": "...",

      // 添加波束参数
      "beam_config": {
        "type": "phased_array",
        "elements": 256,
        "steering_range_deg": 60
      }
    }
  }
}
```

---

## 🚀 快速开始（波束仿真）

### 1. 准备波束仿真程序

```bash
# 创建目录
mkdir -p /home/ccc/beam-simulation-sagin/

# 放置你的波束仿真代码
cp -r your_beam_sim_code/* /home/ccc/beam-simulation-sagin/
```

### 2. 创建Dockerfile

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker
cp Dockerfile.pq-ntor Dockerfile.beam-sim

# 编辑Dockerfile.beam-sim
# 1. 删除liboqs相关内容
# 2. 添加你的依赖（numpy, scipy等）
# 3. 复制波束仿真代码
```

### 3. 构建镜像

```bash
docker build -t sagin-beam-sim:latest -f Dockerfile.beam-sim .
```

### 4. 修改测试脚本

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/scripts
cp sagin_pq_ntor_test.py sagin_beam_sim_test.py

# 修改sagin_beam_sim_test.py
# 1. 更新镜像名称: pq-ntor-sagin → sagin-beam-sim
# 2. 修改测试逻辑: 电路测试 → 波束仿真
# 3. 更新数据收集: 延迟指标 → 信号指标
```

### 5. 运行测试

```bash
python3 sagin_beam_sim_test.py --config configs/sagin_topology_config.json
```

---

## 📊 复用性评分

| 组件 | 复用难度 | 修改工作量 | 推荐做法 |
|------|---------|-----------|---------|
| Docker网络 | ⭐ 简单 | 0 小时 | 直接复用 |
| tc/iptables控制 | ⭐ 简单 | 0 小时 | 直接复用 |
| network_topology_manager.py | ⭐ 简单 | 0 小时 | 直接复用 |
| orbit_simulator.py | ⭐⭐ 中等 | 1-2 小时 | 可能需要添加方法 |
| sagin_topology_config.json | ⭐⭐ 中等 | 1-2 小时 | 添加业务参数 |
| Docker镜像 | ⭐⭐⭐ 复杂 | 2-4 小时 | 需要重新构建 |
| 测试脚本 | ⭐⭐⭐ 复杂 | 4-8 小时 | 需要重写业务逻辑 |
| 分析工具 | ⭐⭐⭐ 复杂 | 2-4 小时 | 需要适配新指标 |

**总工作量估算**: 10-20 小时

---

## ✅ 检查清单

在将SAGIN环境用于波束仿真前，请确认：

**基础设施**:
- [ ] Docker已安装并运行
- [ ] Python 3.8+已安装
- [ ] 必要的Python库已安装（numpy, scipy, matplotlib）

**波束仿真程序**:
- [ ] 波束仿真代码已准备
- [ ] 可以在容器环境中运行
- [ ] 输入/输出接口已定义

**配置文件**:
- [ ] 了解SAGIN配置文件格式
- [ ] 准备好波束相关参数
- [ ] 定义好测试场景

**测试脚本**:
- [ ] 理解原有测试脚本逻辑
- [ ] 确定需要修改的部分
- [ ] 准备数据收集方案

---

## 💡 最佳实践建议

### 1. 逐步迁移

**第一阶段**: 验证基础设施
- 使用原有PQ-NTOR镜像验证网络工作正常
- 确认tc和iptables控制有效

**第二阶段**: 替换应用程序
- 构建包含波束仿真的Docker镜像
- 在单个容器中测试波束仿真程序

**第三阶段**: 集成测试
- 在7节点SAGIN网络中运行波束仿真
- 收集数据并验证结果

### 2. 保持兼容性

- 不要修改核心基础设施代码
- 通过配置文件传递业务参数
- 使用独立的测试脚本

### 3. 文档化修改

- 记录所有修改点
- 保留原始代码备份
- 编写新的使用文档

---

## 🔗 相关资源

### 原有文档
1. `SAGIN代码结构说明-技术版.md` - 理解现有架构
2. `Phase2测试完成总结.md` - 了解测试流程
3. `configs/sagin_topology_config.json` - 配置文件示例

### 新建文档（建议）
1. `beam_simulation_integration.md` - 波束仿真集成指南
2. `beam_analysis_tools.md` - 数据分析工具说明
3. `beam_test_scenarios.md` - 测试场景定义

---

## 📞 支持

**如需帮助，请参考**:
1. 原有SAGIN文档（技术版）
2. Docker官方文档（网络部分）
3. 波束仿真相关论文

**常见问题**:
- Q: 能否同时运行PQ-NTOR和波束仿真？
- A: 可以，使用不同的Docker网络和容器名称

- Q: 轨道仿真器的精度如何？
- A: 使用Skyfield库，精度约±1km（足够大多数研究）

- Q: 能否增加更多节点？
- A: 可以，修改配置文件和IP分配规则

---

**文档版本**: v1.0
**最后更新**: 2025-11-13
**适用于**: 将SAGIN环境用于其他网络仿真课题
**建议阅读**: 配合`SAGIN代码结构说明-技术版.md`使用
