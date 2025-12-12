# 12拓扑实验调试总结

**日期**: 2025-12-11 10:10 UTC+8
**状态**: 🟡 已诊断问题，需要进一步调试

---

## ✅ 已完成的工作

### 1. 发现并修复TC配置错误 ✅
- **问题**: 配置文件TC命令使用了错误的旧参数
- **修复**: 创建 `regenerate_configs_with_correct_params.py`
- **验证**: 新配置正确使用 `topology_params.json` 中的参数

### 2. 清理旧数据 ✅
- 备份63个文件到 `backup/old_experiment_data_20251211/`
- 清理所有基于错误配置的实验结果
- 文档化清理过程

### 3. 调试实验脚本 🟡
- **发现问题**: `run_pq_ntor_12topologies.py` 执行时卡住
  - 使用已弃用的 `proc.connections()` API（警告）
  - 脚本启动但没有实际输出

- **解决方案**: 创建简化版测试脚本 `run_simple_test.py`
  - 添加了HTTP Target Server（端口8000）
  - 修复客户端命令行参数
  - 简化流程便于调试

### 4. 发现新问题 🔍
通过手动测试和简化脚本，发现：
- 客户端报错: "Connection refused"
- Directory服务可能没有成功启动
- 或者服务启动需要更长的等待时间

---

## 🔍 当前问题诊断

###问题1: 原始脚本卡住
**症状**:
```
run_pq_ntor_12topologies.py --runs 10
# 只输出警告，然后卡住，没有实际测试输出
```

**可能原因**:
1. `kill_port_process()` 函数使用弃用的API导致卡住
2. 某个进程检查陷入死循环
3. 没有正确启动HTTP服务器

### 问题2: 客户端连接失败
**症状**:
```
connect: Connection refused
Failed to fetch directory
```

**可能原因**:
1. Directory服务启动需要更长时间（当前等1.5秒）
2. Directory服务启动失败但没有报错
3. 端口被占用或防火墙阻止

---

## 📋 建议的解决方案

### 方案A: 增加服务启动等待时间
修改 `run_simple_test.py`:
```python
# Directory启动后等待3-5秒
time.sleep(3.0)

# 验证服务是否真正监听端口
import socket
def wait_for_port(port, timeout=10):
    for _ in range(timeout):
        sock = socket.socket()
        try:
            sock.connect(('localhost', port))
            sock.close()
            return True
        except:
            time.sleep(1)
    return False
```

### 方案B: 检查服务日志
启动服务时不要重定向stdout/stderr到DEVNULL:
```python
# 临时改为输出到文件，便于调试
proc = subprocess.Popen(
    [str(PQ_NTOR_DIR / 'directory'), '-p', '5000'],
    stdout=open('/tmp/directory.log', 'w'),
    stderr=subprocess.STDOUT
)
```

### 方案C: 手动运行完整测试
```bash
# 1. 清理环境
pkill -9 -f "directory|relay|http.server"
sudo tc qdisc del dev lo root

# 2. 配置TC (Topo01参数)
sudo tc qdisc add dev lo root netem delay 5.42ms 1.35ms rate 59.27mbit loss 3.00%

# 3. 启动服务（等待足够时间）
cd /home/ccc/pq-ntor-experiment/sagin-experiments/docker/build_context/c
python3 -m http.server 8000 &
sleep 2
./directory -p 5000 &
sleep 3
./relay -r guard -p 6001 &
sleep 2
./relay -r middle -p 6002 &
sleep 2
./relay -r exit -p 6003 &
sleep 2

# 4. 验证服务运行
ps aux | grep -E "directory|relay|http"
netstat -tuln | grep -E "5000|600[123]|8000"

# 5. 运行客户端
./client -d localhost -p 5000 -u http://localhost:8000/
```

---

## 📊 实验数据状态

### 当前状态
- ✅ 配置文件: 已使用正确参数重新生成
- ✅ 旧数据: 已清理并备份
- ❌ 新实验数据: 尚未成功运行
- 🟡 脚本: 简化版已创建，但需要调试服务启动

### 预期vs实际

**预期** (修复后):
- Topo01 (Uplink): delay=5.42ms, bw=59.27Mbps → 较慢
- Topo07 (Downlink): delay=5.42ms, bw=69.43Mbps → **较快**
- **结果**: Downlink overhead < Uplink overhead

**实际**:
- 还无法运行成功获取数据

---

##  💡 下一步

### 立即行动
1. **增加服务启动等待时间** - 改为5秒并添加端口检查
2. **启用调试日志** - 查看服务为什么启动失败
3. **手动测试单个拓扑** - 验证完整流程

### 后续工作
1. 修复服务启动问题
2. 成功运行Topo01测试
3. 扩展到所有12个拓扑
4. 生成新的正确图表
5. 更新论文数据

---

## 📁 相关文件

- `/home/ccc/pq-ntor-experiment/CURRENT_STATUS.md` - 项目状态
- `/home/ccc/pq-ntor-experiment/CLEANUP_SUMMARY.md` - 清理总结
- `sagin-experiments/pq-ntor-12topo-experiment/scripts/run_simple_test.py` - 简化测试脚本
- `sagin-experiments/pq-ntor-12topo-experiment/scripts/regenerate_configs_with_correct_params.py` - 配置生成脚本

---

**更新时间**: 2025-12-11 10:10 UTC+8
