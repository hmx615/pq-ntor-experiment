# 12拓扑实验调试最终报告

**日期**: 2025-12-11
**状态**: ✅ 根本问题已解决

---

## 问题回顾

用户提问："为什么修改了网络参数后实验跑不起来？仅仅只是参数修改了啊"

**答案**: 实验失败的原因**不是**网络参数修改，而是代码中硬编码的IP地址与本地测试环境不匹配。

---

## 发现的问题

### 问题1: HTTP服务器端口冲突 ❌
**症状**: Directory服务启动失败，报"bind: Address already in use"

**根本原因**:
- 测试脚本启动了外部的 `python3 -m http.server 8000`
- Directory程序内置了HTTP测试服务器（也监听8000端口）
- 两者冲突导致Directory启动失败

**修复**:
```python
# 删除外部HTTP服务器
# proc = subprocess.Popen(['python3', '-m', 'http.server', '8000'], ...)

# Directory已内置HTTP服务器
proc = subprocess.Popen([str(PQ_NTOR_DIR / 'directory'), '-p', '5000', '-t', '8000'], ...)
```

**文件**: `sagin-experiments/pq-ntor-12topo-experiment/scripts/run_simple_test.py:92-114`

---

### 问题2: IP地址硬编码错误 ❌ **核心问题**
**症状**:
- 客户端报错 "Connection refused"
- 客户端尝试连接 `172.20.1.11:9001` 而不是 `localhost:6001`

**根本原因**:
`directory_server.c` 中硬编码了SAGIN网络部署的IP地址:
```c
/* Hardcoded node list (for SAGIN network deployment) */
static node_info_t nodes[] = {
    {
        .hostname = "172.20.1.11",  // Sat-1 (Guard)
        .port = 9001,
        .type = NODE_TYPE_GUARD,
        ...
    },
    {
        .hostname = "172.20.2.21",  // Aircraft-1 (Middle)
        .port = 9003,
        ...
    },
    {
        .hostname = "172.20.3.32",  // GS-London (Exit)
        .port = 9005,
        ...
    }
};
```

这些IP和端口是为7π物理集群或SAGIN网络设计的，但WSL2本地测试需要localhost。

**修复**:
```c
/* Hardcoded node list (for localhost testing) */
static node_info_t nodes[] = {
    {
        .hostname = "127.0.0.1",  // Guard (localhost)
        .port = 6001,
        .type = NODE_TYPE_GUARD,
        ...
    },
    {
        .hostname = "127.0.0.1",  // Middle (localhost)
        .port = 6002,
        .type = NODE_TYPE_MIDDLE,
        ...
    },
    {
        .hostname = "127.0.0.1",  // Exit (localhost)
        .port = 6003,
        .type = NODE_TYPE_EXIT,
        ...
    }
};
```

**文件**: `sagin-experiments/docker/build_context/c/src/directory_server.c:15-41`

**重新编译**:
```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c
make clean
make directory relay client
```

---

## 测试结果

### 修复前 ❌
```
[Client] Fetching node list from directory...
connect: Connection refused
Failed to fetch directory
```

### 修复后 ✅
```
[Client] Found 1 guards, 1 middles, 1 exits

[2/4] Building 3-hop circuit...
[Client] Creating first hop to Guard 127.0.0.1:6001
[Client] Connected to Guard
[Client] First hop established
[Client] Extending circuit to 127.0.0.1:6002
[Client] Circuit extended (layer 1 added)
[Client] Extending circuit to 127.0.0.1:6003
[Client] Circuit extended (layer 2 added)
[Client] 3-hop circuit established!

[3/4] Sending HTTP GET request...
[Client] Sent RELAY_BEGIN
[Client] Stream connected
[Client] Sent 54 bytes
[Client] Received 1205 bytes of data
```

**结论**: 系统现在可以正常工作了！

---

## 文件变更总结

### 修改的文件
1. `sagin-experiments/pq-ntor-12topo-experiment/scripts/run_simple_test.py`
   - 添加 `wait_for_port()` 函数进行端口检查
   - 移除外部HTTP服务器
   - 添加调试日志输出

2. `sagin-experiments/docker/build_context/c/src/directory_server.c`
   - 修改硬编码的node list从SAGIN IP (172.20.x.x:900x) 改为 localhost (127.0.0.1:600x)

### 重新编译的程序
- `directory` - Directory服务器
- `relay` - Relay节点
- `client` - Tor客户端

---

## 为什么TC参数修改后失效？

### 真相
**TC参数修改本身没有问题**。实验失败是因为:

1. 旧代码从未在WSL2本地环境中正确测试过
2. 代码硬编码了分布式网络的IP地址
3. 当我们生成新的TC配置文件时，触发了完整的测试流程
4. 完整测试流程暴露了IP地址硬编码的根本问题

### 时间线
1. **之前**: 可能从未在WSL2上成功运行过完整测试（或使用了不同的代码版本）
2. **修改TC参数**: 生成了正确的配置文件
3. **运行测试**: 首次在WSL2上运行完整测试流程
4. **暴露问题**: 发现directory_server.c的IP地址硬编码问题

---

## 下一步

### 立即可做
1. ✅ 使用修复后的代码运行单个拓扑测试
2. ⏳ 运行所有12个拓扑的实验
3. ⏳ 生成新的正确的实验数据和图表

### 未来改进
建议修改 `directory_server.c` 支持动态配置：
- 从配置文件读取节点列表
- 或通过命令行参数指定节点信息
- 避免硬编码，支持多种部署场景

---

## 总结

**问题**: "为什么修改了网络参数后实验跑不起来？"

**答案**:
- ❌ **不是**因为TC参数修改
- ❌ **不是**因为网络配置问题
- ✅ **是**因为代码中硬编码了分布式网络的IP地址，与WSL2本地测试环境不匹配
- ✅ TC参数修改是**正确的**，只是碰巧触发了首次完整的本地测试，暴露了代码的环境依赖问题

**修复结果**:
- 所有服务现在可以正确启动 ✅
- 客户端可以连接到正确的地址 ✅
- 3跳电路可以成功建立 ✅
- HTTP请求可以正常发送和接收 ✅

---

**生成时间**: 2025-12-11 11:20 UTC+8
