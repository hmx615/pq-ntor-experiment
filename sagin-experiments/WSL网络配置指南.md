# WSL端口转发配置指南 - 飞腾派远程访问

## 问题描述

飞腾派无法访问WSL内的Web服务，因为：
- WSL2使用虚拟网络 (IP: 192.168.74.81)
- 飞腾派在物理网络 (IP: 192.168.5.83)
- 两者无法直接通信

## 解决方案

通过Windows端口转发，让飞腾派访问Windows主机IP，再转发到WSL。

---

## 配置步骤

### 步骤1: 在Windows上以管理员身份运行PowerShell

1. 按 `Win + X`
2. 选择 "Windows PowerShell (管理员)" 或 "终端 (管理员)"

### 步骤2: 运行配置脚本

```powershell
# 进入项目目录
cd C:\Users\你的用户名\路径\到\pq-ntor-experiment\sagin-experiments

# 执行脚本
.\setup_wsl_port_forward.ps1
```

**或者手动执行以下命令**:

```powershell
# 1. 添加端口转发 (HTTP服务)
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=192.168.74.81

# 2. 添加端口转发 (WebSocket服务)
netsh interface portproxy add v4tov4 listenport=9000 listenaddress=0.0.0.0 connectport=9000 connectaddress=192.168.74.81

# 3. 添加防火墙规则 (HTTP)
New-NetFirewallRule -DisplayName "WSL HTTP Server" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow

# 4. 添加防火墙规则 (WebSocket)
New-NetFirewallRule -DisplayName "WSL WebSocket Hub" -Direction Inbound -LocalPort 9000 -Protocol TCP -Action Allow

# 5. 验证配置
netsh interface portproxy show all
```

### 步骤3: 确保WSL服务正在运行

在WSL终端执行:

```bash
# 检查服务状态
lsof -i:8080 -i:9000

# 如果没有运行，启动服务
cd /home/ccc/pq-ntor-experiment/sagin-experiments

# 启动HTTP服务
cd frontend
python3 -m http.server 8080 --bind 0.0.0.0 &

# 启动WebSocket Hub
cd ../backend
python3 websocket_hub.py &

# 启动各个Node Agent (如果需要)
python3 node_agent.py --node-id SAT &
```

---

## 飞腾派访问方式

### 网络信息

- **Windows主机IP**: `192.168.5.144`
- **飞腾派IP**: `192.168.5.83`
- **WSL IP**: `192.168.74.81` (内部使用)

### 访问地址

**控制面板**:
```
http://192.168.5.144:8080/control-panel/index.html
```

**节点视图** (6个飞腾派分别访问):
```
飞腾派1 (SAT):    http://192.168.5.144:8080/node-view/index.html?node_id=SAT
飞腾派2 (SR):     http://192.168.5.144:8080/node-view/index.html?node_id=SR
飞腾派3 (S1R2):   http://192.168.5.144:8080/node-view/index.html?node_id=S1R2
飞腾派4 (S1):     http://192.168.5.144:8080/node-view/index.html?node_id=S1
飞腾派5 (S2):     http://192.168.5.144:8080/node-view/index.html?node_id=S2
飞腾派6 (T):      http://192.168.5.144:8080/node-view/index.html?node_id=T
```

---

## 测试验证

### 在飞腾派上执行测试

```bash
# 1. 测试网络连通性
ping 192.168.5.144

# 2. 测试HTTP服务
curl http://192.168.5.144:8080/

# 3. 测试完整URL
curl http://192.168.5.144:8080/node-view/index.html?node_id=SAT

# 4. 在浏览器中打开 (使用Chromium)
chromium-browser --kiosk http://192.168.5.144:8080/node-view/index.html?node_id=SAT
```

---

## 故障排查

### 问题1: 飞腾派ping不通Windows主机

**检查**:
```powershell
# Windows上检查IP
ipconfig | findstr "192.168"

# 确认Windows防火墙允许ICMP
New-NetFirewallRule -DisplayName "Allow ICMPv4" -Direction Inbound -Protocol ICMPv4 -Action Allow
```

### 问题2: curl返回"Connection refused"

**检查**:
```bash
# 在WSL中检查服务是否运行
lsof -i:8080
lsof -i:9000

# 检查服务绑定地址 (必须是 0.0.0.0)
ss -tuln | grep -E ":(8080|9000)"
```

**预期输出**:
```
tcp   LISTEN 0      5      0.0.0.0:8080    0.0.0.0:*
tcp   LISTEN 0    100      0.0.0.0:9000    0.0.0.0:*
```

### 问题3: WebSocket连接失败

**检查浏览器控制台** (F12):
- 查看是否有WebSocket连接错误
- 确认连接地址是 `ws://192.168.5.144:9000`

**解决方案**:
前端会自动使用页面host连接WebSocket，无需修改代码。

### 问题4: Windows IP改变

**症状**: 之前能访问，重启后不能了

**原因**: Windows可能获取新的DHCP IP

**解决方案**:
```powershell
# 1. 重新获取Windows IP
ipconfig | findstr "192.168"

# 2. 更新飞腾派访问地址
# 将新IP替换 192.168.5.144
```

**永久方案**: 在路由器上为Windows设置静态IP

---

## 清理配置

如需移除端口转发和防火墙规则:

```powershell
# 管理员PowerShell

# 删除端口转发
netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0
netsh interface portproxy delete v4tov4 listenport=9000 listenaddress=0.0.0.0

# 或者重置所有端口转发
netsh interface portproxy reset

# 删除防火墙规则
Remove-NetFirewallRule -DisplayName "WSL HTTP Server"
Remove-NetFirewallRule -DisplayName "WSL WebSocket Hub"
```

---

## 性能优化建议

由于使用了瘦客户端模式，飞腾派性能消耗：
- CPU: 10-20% (仅浏览器渲染)
- 内存: 50-100MB
- GPU: 25-35% (已优化的3D地球)

如果仍然卡顿，可以：
1. 使用优化版节点视图 (index.html 已是优化版)
2. 降低浏览器分辨率
3. 增加WebSocket更新间隔

---

## 架构图

```
┌─────────────────────────────────────────────────────┐
│                   Windows主机                        │
│                 IP: 192.168.5.144                   │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │              WSL2 虚拟机                      │  │
│  │           IP: 192.168.74.81                  │  │
│  │                                               │  │
│  │  ┌─────────────────────────────────────┐    │  │
│  │  │  WebSocket Hub (9000)               │    │  │
│  │  │  HTTP Server (8080)                 │    │  │
│  │  │  6个 Node Agents                     │    │  │
│  │  └─────────────────────────────────────┘    │  │
│  │                    ↑                         │  │
│  └────────────────────┼─────────────────────────┘  │
│                       │ 端口转发                     │
│         ┌─────────────┼─────────────────┐          │
│         │  8080 → 192.168.74.81:8080   │          │
│         │  9000 → 192.168.74.81:9000   │          │
│         └──────────────────────────────┘          │
│                       ↓                            │
│            对外端口: 8080, 9000                     │
└───────────────────────┼────────────────────────────┘
                        │
                        │ 局域网
                        ↓
            ┌───────────────────────┐
            │   飞腾派 Pi-1~6        │
            │   IP: 192.168.5.83    │
            │   仅运行浏览器          │
            └───────────────────────┘
```

---

## 附录: 自动化脚本

### 飞腾派启动脚本

在每个飞腾派创建 `/home/user/start_display.sh`:

```bash
#!/bin/bash
# 飞腾派自动启动脚本

# 配置
SERVER_IP="192.168.5.144"  # Windows主机IP
NODE_ID="SAT"              # 节点ID (每个飞腾派不同)

# 等待网络就绪
sleep 5

# 测试连通性
if ! ping -c 1 $SERVER_IP > /dev/null 2>&1; then
    zenity --error --text="无法连接到服务器 $SERVER_IP"
    exit 1
fi

# 启动浏览器
chromium-browser --kiosk --noerrdialogs --disable-infobars \
    "http://${SERVER_IP}:8080/node-view/index.html?node_id=${NODE_ID}"
```

赋予执行权限:
```bash
chmod +x /home/user/start_display.sh
```

添加到自动启动:
```bash
echo "@/home/user/start_display.sh" >> ~/.config/lxsession/LXDE-pi/autostart
```

---

**创建时间**: 2025-11-23
**适用环境**: WSL2 + 飞腾派
**状态**: ✅ 已测试可用
