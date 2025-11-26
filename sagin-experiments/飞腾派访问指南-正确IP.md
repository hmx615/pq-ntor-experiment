# 飞腾派访问指南 - 使用正确的Windows IP

## 🎯 问题解决

### 发现的问题

Windows主机有**两个网络接口**：
- ❌ **WLAN 2 (无线)**: `192.168.5.144` - 飞腾派无法访问（可能被路由器AP隔离）
- ✅ **以太网 (有线)**: `192.168.5.83` - 飞腾派**可以访问**

### 解决方案

**使用有线网卡IP**: `192.168.5.83`

---

## 🚀 快速配置步骤

### 步骤1: 在Windows上配置端口转发

**在Windows PowerShell (管理员模式) 执行**:

```powershell
# 快速配置命令
netsh interface portproxy reset
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=192.168.74.81
netsh interface portproxy add v4tov4 listenport=9000 listenaddress=0.0.0.0 connectport=9000 connectaddress=192.168.74.81

# 添加防火墙规则
New-NetFirewallRule -DisplayName "WSL HTTP Server" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow -Profile Any
New-NetFirewallRule -DisplayName "WSL WebSocket Hub" -Direction Inbound -LocalPort 9000 -Protocol TCP -Action Allow -Profile Any

# 验证
netsh interface portproxy show all
```

**或者运行自动化脚本**:
```powershell
cd C:\...\pq-ntor-experiment\sagin-experiments
.\setup_correct_ip.ps1
```

---

### 步骤2: 在飞腾派测试连接

```bash
# 1. 测试ping (应该成功)
ping -c 3 192.168.5.83

# 预期输出:
# 64 字节，来自 192.168.5.83: icmp_seq=1 ttl=128 时间=1.84 毫秒

# 2. 测试HTTP服务
curl http://192.168.5.83:8080/

# 预期输出: HTML目录列表或文件内容

# 3. 测试完整URL
curl http://192.168.5.83:8080/node-view/index.html?node_id=SAT

# 预期输出: 包含 "SAGIN" 的HTML内容
```

---

### 步骤3: 在飞腾派浏览器访问

#### 各节点访问URL

| 飞腾派 | 节点ID | 浏览器访问URL |
|-------|--------|--------------|
| Pi-1 | SAT (卫星) | `http://192.168.5.83:8080/node-view/index.html?node_id=SAT` |
| Pi-2 | SR (无人机1) | `http://192.168.5.83:8080/node-view/index.html?node_id=SR` |
| Pi-3 | S1R2 (无人机2) | `http://192.168.5.83:8080/node-view/index.html?node_id=S1R2` |
| Pi-4 | S1 (终端1) | `http://192.168.5.83:8080/node-view/index.html?node_id=S1` |
| Pi-5 | S2 (终端2) | `http://192.168.5.83:8080/node-view/index.html?node_id=S2` |
| Pi-6 | T (终端3) | `http://192.168.5.83:8080/node-view/index.html?node_id=T` |

#### 控制面板 (可选)

```
http://192.168.5.83:8080/control-panel/index.html
```

#### 全屏模式启动

```bash
# Chromium (推荐)
chromium-browser --kiosk --noerrdialogs --disable-infobars \
  http://192.168.5.83:8080/node-view/index.html?node_id=SAT

# Firefox
firefox --kiosk http://192.168.5.83:8080/node-view/index.html?node_id=SAT
```

---

## 🔧 故障排查

### 问题1: 飞腾派仍然无法ping通192.168.5.83

**可能原因**:
- Windows防火墙阻止ICMP

**解决方案**:
```powershell
# 在Windows PowerShell (管理员) 执行
New-NetFirewallRule -DisplayName "Allow ICMPv4 Inbound" `
    -Direction Inbound `
    -Protocol ICMPv4 `
    -IcmpType 8 `
    -Action Allow `
    -Profile Any
```

---

### 问题2: ping成功但curl失败

**症状**:
```bash
ping 192.168.5.83  # ✓ 成功
curl http://192.168.5.83:8080/  # ✗ Connection refused
```

**检查WSL服务是否运行**:

```bash
# 在WSL中执行
lsof -i:8080 -i:9000

# 如果没有输出，启动服务:
cd /home/ccc/pq-ntor-experiment/sagin-experiments/frontend
python3 -m http.server 8080 --bind 0.0.0.0 &

cd ../backend
python3 websocket_hub.py &
```

**检查端口转发**:
```powershell
# Windows PowerShell
netsh interface portproxy show all

# 应该看到:
# 0.0.0.0  8080  192.168.74.81  8080
# 0.0.0.0  9000  192.168.74.81  9000
```

---

### 问题3: 浏览器打开但页面空白或加载失败

**检查浏览器控制台** (按F12):

1. 查看Network标签，确认资源加载情况
2. 查看Console标签，查看JavaScript错误
3. 检查WebSocket连接状态

**常见错误和解决方案**:

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `WebSocket connection failed` | 9000端口不通 | 检查端口转发和防火墙 |
| `404 Not Found` | 路径错误 | 确认URL正确 |
| `ERR_CONNECTION_REFUSED` | 服务未运行 | 启动WSL服务 |

---

## 📊 网络架构图

```
┌─────────────────────────────────────────────────────────┐
│                  Windows主机                             │
│                                                          │
│  ┌────────────────┐         ┌────────────────┐         │
│  │ 无线网卡 (WLAN)│         │ 有线网卡 (以太网)│        │
│  │ 192.168.5.144 │         │ 192.168.5.83   │ ✅      │
│  │ ✗ 被路由器隔离  │         │ 飞腾派可访问     │        │
│  └────────────────┘         └────────┬───────┘         │
│                                      │                  │
│  ┌──────────────────────────────────┼─────────────┐   │
│  │             WSL2虚拟机             │              │   │
│  │          IP: 192.168.74.81        │              │   │
│  │                                   ↓              │   │
│  │  端口转发: 8080 → 192.168.74.81:8080           │   │
│  │           9000 → 192.168.74.81:9000           │   │
│  │                                                │   │
│  │  服务:                                          │   │
│  │    - HTTP Server (8080)                       │   │
│  │    - WebSocket Hub (9000)                     │   │
│  │    - Node Agents                              │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────┘
                          │ 以太网
                          │ 192.168.5.0/24
                          ↓
              ┌───────────────────────┐
              │   飞腾派 Pi-1          │
              │   IP: 192.168.5.110   │
              │                       │
              │   访问:                │
              │   192.168.5.83:8080  │
              └───────────────────────┘
```

---

## ✅ 验证清单

配置完成后，请验证以下项目：

- [ ] Windows PowerShell端口转发已配置
- [ ] Windows防火墙规则已添加
- [ ] WSL HTTP服务正在运行 (8080端口)
- [ ] WSL WebSocket服务正在运行 (9000端口)
- [ ] 飞腾派可以ping通 192.168.5.83
- [ ] 飞腾派curl可以访问 http://192.168.5.83:8080/
- [ ] 飞腾派浏览器可以打开节点视图页面
- [ ] WebSocket连接成功（页面右上角显示"已连接"）

---

## 📝 自动化脚本

### 飞腾派启动脚本

创建 `/home/user/start_sagin_display.sh`:

```bash
#!/bin/bash
# 飞腾派SAGIN节点视图启动脚本

# 配置
SERVER_IP="192.168.5.83"  # Windows有线网卡IP
NODE_ID="SAT"             # 节点ID (每个飞腾派不同)

# 等待网络
sleep 3

# 测试连接
if ! ping -c 1 $SERVER_IP > /dev/null 2>&1; then
    echo "错误: 无法连接到服务器 $SERVER_IP"
    exit 1
fi

# 启动浏览器
chromium-browser --kiosk --noerrdialogs --disable-infobars \
    "http://${SERVER_IP}:8080/node-view/index.html?node_id=${NODE_ID}"
```

赋予权限:
```bash
chmod +x /home/user/start_sagin_display.sh
```

---

## 🎯 总结

**关键要点**:
1. ✅ **使用Windows有线网卡IP**: `192.168.5.83`
2. ✅ **不要使用无线网卡IP**: `192.168.5.144` (被路由器隔离)
3. ✅ **确保WSL服务绑定到 0.0.0.0** (接受外部连接)
4. ✅ **配置Windows端口转发和防火墙**

**网络拓扑**:
- Windows有线网卡: `192.168.5.83`
- 飞腾派: `192.168.5.110`
- WSL虚拟机: `192.168.74.81` (通过端口转发访问)

**访问地址**:
```
http://192.168.5.83:8080/node-view/index.html?node_id=<节点ID>
```

---

**创建时间**: 2025-11-23
**适用环境**: WSL2 + Windows双网卡 + 飞腾派
**状态**: ✅ 已确认可行
