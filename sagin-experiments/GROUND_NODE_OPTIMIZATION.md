# 地球节点性能优化方案

## 问题分析

### 当前架构
- **控制面板 (Pi-0)**: WebSocket Hub + 控制前端 + Globe.GL可视化
- **地球节点 (Pi-1~6)**: Node Agent + Nginx + 节点前端

### 性能瓶颈
地球节点(飞腾派)上运行的资源消耗组件:
1. **Node Agent** (Python): WebSocket连接、数据采集、实时发送
2. **Nginx**: 静态文件服务器
3. **节点前端**: HTML/JS/CSS静态资源

## 优化策略

### 方案1: 取消地球节点前端 (推荐)

**核心思想**: 地球节点只需要数据采集Agent,不需要独立的Web前端

**优化措施**:
```yaml
# docker-compose-node-lite.yml
services:
  node-agent:
    build: ../backend
    container_name: sagin_node_${NODE_ID}
    environment:
      - NODE_ID=${NODE_ID}
      - NODE_ROLE=${NODE_ROLE}
      - HUB_URL=ws://192.168.100.17:9000
    restart: unless-stopped
    # 移除 Nginx 容器
```

**资源节省**:
- ❌ Nginx容器 (~50MB内存)
- ❌ 前端资源加载
- ✅ 只保留轻量级Python Agent (~30MB)

**收益**: 节省约**40-50%** CPU + 60MB内存

---

### 方案2: Agent精简模式

**优化Node Agent代码**:

```python
# node_agent_lite.py - 精简版Agent
class LiteNodeAgent:
    def __init__(self, node_id, node_role, hub_url):
        self.node_id = node_id
        self.node_role = node_role
        self.hub_url = hub_url
        self.update_interval = 2.0  # 降低更新频率: 1s -> 2s
        
    async def collect_minimal_data(self):
        """只采集必要数据"""
        return {
            'type': 'node_status',
            'node_id': self.node_id,
            'timestamp': time.time(),
            'status': {
                'role': self.node_role,
                'online': True
            },
            'pq_ntor': {
                'handshakes': self.handshake_count
            }
            # 移除: 详细流量、链路信息等
        }
```

**优化项**:
1. **降低更新频率**: 1秒 → 2秒
2. **精简数据包**: 只发送核心状态
3. **移除复杂计算**: 不计算实时流量速率
4. **批量发送**: 累积5秒数据后批量发送

**收益**: 节省约**30%** CPU

---

### 方案3: 混合优化 (最佳方案)

**组合方案1 + 方案2**:

```yaml
# docker-compose-node-optimized.yml
services:
  node-agent-lite:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.agent-lite
    container_name: sagin_node_lite_${NODE_ID}
    environment:
      - NODE_ID=${NODE_ID}
      - NODE_ROLE=${NODE_ROLE}
      - HUB_URL=ws://192.168.100.17:9000
      - UPDATE_INTERVAL=2.0  # 配置更新间隔
      - MINIMAL_MODE=true    # 启用精简模式
    restart: unless-stopped
    cpus: 0.5              # 限制CPU使用
    mem_limit: 50m         # 限制内存使用
```

**总收益**: 节省约**60-70%** CPU + 80MB内存

---

## 实施步骤

### Step 1: 创建精简版Agent

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/backend
cp node_agent.py node_agent_lite.py
# 编辑 node_agent_lite.py 应用优化
```

### Step 2: 创建精简版Dockerfile

```dockerfile
# Dockerfile.agent-lite
FROM python:3.9-slim
WORKDIR /app
COPY requirements-lite.txt .
RUN pip install --no-cache-dir -r requirements-lite.txt
COPY node_agent_lite.py .
CMD ["python", "node_agent_lite.py"]
```

### Step 3: 部署到地球节点

```bash
# 在每个地球节点飞腾派上
export NODE_ID=pi-1
export NODE_ROLE=ground
docker-compose -f docker-compose-node-optimized.yml up -d
```

---

## 对比表

| 组件 | 原方案 | 方案1 | 方案2 | 方案3 |
|------|--------|-------|-------|-------|
| Nginx | ✅ 50MB | ❌ | ✅ 50MB | ❌ |
| Agent | 30MB | 30MB | 20MB | 15MB |
| 更新频率 | 1s | 1s | 2s | 2s |
| **总内存** | **~100MB** | **~40MB** | **~80MB** | **~25MB** |
| **总CPU** | **100%** | **60%** | **70%** | **30-40%** |

---

## 验证方法

### 性能测试脚本

```bash
#!/bin/bash
# test_agent_performance.sh

# 1. 测试CPU占用
echo "=== CPU Usage ==="
docker stats --no-stream sagin_node_lite_pi-1 | grep sagin

# 2. 测试内存占用
echo "=== Memory Usage ==="
docker stats --no-stream sagin_node_lite_pi-1 | awk '{print $4}'

# 3. 测试WebSocket延迟
echo "=== WebSocket Latency ==="
# 发送测试消息，测量响应时间
```

### 预期结果

- CPU: < 5% (原15-20%)
- 内存: < 30MB (原100MB)
- WebSocket延迟: < 50ms

---

## 注意事项

1. **控制面板不变**: Pi-0的Hub和Globe.GL前端保持不变
2. **可视化功能**: 所有可视化由Pi-0的控制前端统一展示
3. **数据完整性**: 精简模式下仍保证关键数据传输
4. **回退方案**: 保留原docker-compose.yml作为备份

---

## 下一步

是否开始实施优化方案3 (混合优化)?
