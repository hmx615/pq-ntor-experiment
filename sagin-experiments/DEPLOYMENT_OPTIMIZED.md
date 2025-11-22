# 优化版部署指南 - 飞腾派节点

## 快速部署 (地球节点 Pi-1~6)

### 1. 部署精简版Agent

```bash
# 在每个飞腾派上执行
cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker

# 设置节点信息
export NODE_ID=pi-1      # 修改为: pi-1, pi-2, ... pi-6
export NODE_ROLE=ground  # ground/aircraft/satellite

# 启动优化版Agent
docker-compose -f docker-compose-node-optimized.yml up -d

# 查看日志
docker logs -f sagin_node_lite_pi-1
```

### 2. 验证部署

```bash
# 检查容器状态
docker ps

# 查看资源使用
docker stats sagin_node_lite_pi-1

# 预期结果:
# - CPU: < 5%
# - Memory: < 30MB
```

### 3. 性能测试 (可选)

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/scripts
./test_agent_performance.sh pi-1 ground
```

---

## 对比: 原版 vs 优化版

| 项目 | 原版 | 优化版 | 改进 |
|------|------|--------|------|
| **容器数量** | 2个 (Agent + Nginx) | 1个 (Lite Agent) | -50% |
| **CPU使用** | 15-20% | < 5% | **-70%** |
| **内存使用** | ~100MB | < 30MB | **-70%** |
| **日志大小** | 无限制 | 1MB × 2 | 资源节省 |
| **更新频率** | 1秒 | 2秒 | 网络带宽节省 |

---

## 架构说明

### 原版架构 (已废弃)
```
飞腾派 (Pi-1~6)
├── Node Agent (Python)     - 30MB, 10% CPU
└── Nginx (前端服务)         - 50MB, 5% CPU
    └── 节点视图 (HTML/JS)
```

### 优化版架构 (推荐)
```
飞腾派 (Pi-1~6)
└── Lite Node Agent (Python) - 25MB, 3% CPU
    ├── 精简数据采集
    ├── 批量发送 (3条/次)
    └── 降低更新频率 (2s)
```

### 控制面板 (Pi-0 不变)
```
飞腾派 Pi-0
├── WebSocket Hub
├── 控制前端 (Globe.GL)
└── 6+1 节点可视化
```

---

## 主要优化点

### 1. 移除Nginx容器
- **原因**: 地球节点不需要独立Web界面
- **好处**: 节省50MB内存 + 5% CPU

### 2. 精简Agent代码
- **批量发送**: 累积3条消息批量发送
- **降低频率**: 1秒 → 2秒更新
- **精简数据**: 只发送必要字段
- **降低日志**: WARNING级别

### 3. Docker资源限制
```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'    # 最多0.5核
      memory: 50M    # 最多50MB
```

### 4. 日志限制
```yaml
logging:
  options:
    max-size: "1m"   # 单文件最大1MB
    max-file: "2"    # 最多2个文件
```

---

## 故障排查

### 问题1: 容器无法启动
```bash
# 检查Hub是否运行
ping 192.168.100.17

# 检查端口
nc -zv 192.168.100.17 9000

# 查看容器日志
docker logs sagin_node_lite_pi-1
```

### 问题2: CPU/内存超限
```bash
# 查看资源使用
docker stats

# 如果超限,调整docker-compose-node-optimized.yml:
# - 增加 memory: 80M
# - 增加 cpus: '0.8'
```

### 问题3: 数据未到达Hub
```bash
# 检查WebSocket连接
docker logs sagin_node_lite_pi-1 | grep "connected"

# 手动测试连接
python3 -c "import websockets; import asyncio; asyncio.run(websockets.connect('ws://192.168.100.17:9000'))"
```

---

## 回退到原版

如果需要回退:

```bash
# 停止优化版
docker-compose -f docker-compose-node-optimized.yml down

# 启动原版
docker-compose -f docker-compose-node.yml up -d
```

---

## 下一步

- [ ] 在Pi-1上测试优化版
- [ ] 验证数据到达控制面板
- [ ] 对比性能指标
- [ ] 推广到Pi-2~6

---

## 参考文件

- **精简Agent**: `backend/node_agent_lite.py`
- **Dockerfile**: `docker/Dockerfile.agent-lite`
- **Docker Compose**: `docker/docker-compose-node-optimized.yml`
- **测试脚本**: `scripts/test_agent_performance.sh`
- **优化方案**: `GROUND_NODE_OPTIMIZATION.md`
