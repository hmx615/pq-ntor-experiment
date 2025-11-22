# 飞腾派远程访问配置 - 瘦客户端模式

## 🎯 架构说明

采用**瘦客户端**架构：
- **服务器**（WSL本机）：运行所有后台服务和前端资源
- **飞腾派 1-6**：仅运行浏览器访问服务器，显示页面

**优势**：
- ✅ 飞腾派零后台负担，不需要运行任何Python服务
- ✅ 所有计算在服务器完成
- ✅ 飞腾派只需要网络+浏览器

---

## 📡 服务器信息

### 当前服务器IP
```
192.168.74.81
```

**说明**：这是WSL的IP地址。如果重启WSL或网络变化，IP可能改变。

### 服务状态
```bash
# 检查服务是否运行
lsof -i:9000 -i:8080

# 应该看到：
# python3   WebSocket Hub  *:9000 (LISTEN)
# python3   HTTP Server    *:8080 (LISTEN)
```

---

## 🌐 访问地址（6+1架构）

### 控制面板（Pi-0 / 第7个屏幕）
```
http://192.168.74.81:8080/control-panel/index.html
```

### 节点视图（Pi-1 到 Pi-6）

| 飞腾派 | 节点ID | 角色 | 访问地址 |
|-------|--------|------|----------|
| **Pi-1** | SAT | 卫星 | http://192.168.74.81:8080/node-view/index.html?node_id=SAT |
| **Pi-2** | SR | 无人机1 | http://192.168.74.81:8080/node-view/index.html?node_id=SR |
| **Pi-3** | S1R2 | 无人机2 | http://192.168.74.81:8080/node-view/index.html?node_id=S1R2 |
| **Pi-4** | S1 | 终端1 | http://192.168.74.81:8080/node-view/index.html?node_id=S1 |
| **Pi-5** | S2 | 终端2 | http://192.168.74.81:8080/node-view/index.html?node_id=S2 |
| **Pi-6** | T | 终端3 | http://192.168.74.81:8080/node-view/index.html?node_id=T |

---

## 🚀 飞腾派配置步骤

### 前提条件
1. 飞腾派与服务器在同一局域网
2. 飞腾派能ping通服务器IP：`192.168.74.81`
3. 飞腾派安装了浏览器（Chromium/Firefox）

### 测试连接
在飞腾派上执行：
```bash
# 测试网络连通性
ping 192.168.74.81

# 测试HTTP服务
curl http://192.168.74.81:8080/

# 测试WebSocket（可选）
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  http://192.168.74.81:9000/
```

### 打开浏览器
```bash
# 方法1：在飞腾派终端执行（自动打开浏览器）
chromium-browser --kiosk http://192.168.74.81:8080/node-view/index.html?node_id=SAT

# 方法2：手动打开浏览器，输入URL
# 在地址栏输入对应的访问地址
```

### 全屏显示（推荐）
```bash
# 使用kiosk模式全屏显示，无工具栏
chromium-browser --kiosk --noerrdialogs --disable-infobars \
  http://192.168.74.81:8080/node-view/index.html?node_id=SAT
```

---

## 🔧 故障排查

### 问题1：无法访问页面

**检查步骤：**
```bash
# 1. 检查飞腾派能否ping通服务器
ping 192.168.74.81

# 2. 检查服务器防火墙（Windows）
# 在Windows PowerShell执行：
New-NetFirewallRule -DisplayName "WSL HTTP" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "WSL WebSocket" -Direction Inbound -LocalPort 9000 -Protocol TCP -Action Allow

# 3. 检查WSL服务是否运行
# 在WSL执行：
lsof -i:9000 -i:8080
```

### 问题2：页面显示"WebSocket: 连接中..."

**原因**：WebSocket端口9000被防火墙阻止

**解决**：
```bash
# Windows PowerShell（管理员）
New-NetFirewallRule -DisplayName "WSL WebSocket" -Direction Inbound -LocalPort 9000 -Protocol TCP -Action Allow
```

### 问题3：WSL IP改变了

**查找新IP**：
```bash
# 在WSL执行
hostname -I

# 更新所有飞腾派的访问地址中的IP
```

### 问题4：3D地球仍然卡顿

**原因**：WebGL渲染仍在飞腾派GPU上

**解决方案**：
1. 降级为2D平面视图（需要修改代码）
2. 或使用VNC方案（服务器渲染，飞腾派只显示画面）

---

## 📊 性能对比

### 原方案（每个飞腾派独立运行）
```
飞腾派1-6：
  - WebSocket Hub: ❌ 不运行
  - Node Agent: ✅ 运行（Python进程）
  - HTTP Server: ✅ 运行
  - 浏览器: ✅ 渲染3D地球
  - CPU: 40-60%
  - 内存: 200-300MB
```

### 新方案（瘦客户端）
```
服务器（WSL）：
  - WebSocket Hub: ✅ 运行
  - 6个 Node Agent: ✅ 运行
  - HTTP Server: ✅ 运行

飞腾派1-6：
  - 后台服务: ❌ 不运行
  - 浏览器: ✅ 仅渲染页面
  - CPU: 20-30%（仅浏览器+WebGL）
  - 内存: 100-150MB
```

**性能提升**：
- 飞腾派CPU降低: 40-60% → 20-30%
- 飞腾派内存降低: 200-300MB → 100-150MB
- 无需在飞腾派上安装Python/依赖

---

## 🎨 浏览器推荐设置

### Chromium（推荐）
```bash
chromium-browser --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-restore-session-state \
  --no-first-run \
  http://192.168.74.81:8080/node-view/index.html?node_id=SAT
```

### Firefox
```bash
firefox --kiosk \
  http://192.168.74.81:8080/node-view/index.html?node_id=SAT
```

---

## 📝 快速启动脚本（可选）

为每个飞腾派创建启动脚本：

### Pi-1 (SAT)
```bash
#!/bin/bash
# /home/pi/start_sagin_display.sh

SERVER_IP="192.168.74.81"
NODE_ID="SAT"

chromium-browser --kiosk --noerrdialogs --disable-infobars \
  "http://${SERVER_IP}:8080/node-view/index.html?node_id=${NODE_ID}"
```

### 使用方法
```bash
# 添加执行权限
chmod +x /home/pi/start_sagin_display.sh

# 运行
./start_sagin_display.sh
```

---

## 🔄 自动启动（可选）

### 开机自动启动浏览器
编辑 `/etc/xdg/lxsession/LXDE-pi/autostart`：
```bash
@chromium-browser --kiosk --noerrdialogs --disable-infobars \
  http://192.168.74.81:8080/node-view/index.html?node_id=SAT
```

---

**创建日期**: 2025-11-22
**服务器**: WSL (192.168.74.81)
**模式**: 瘦客户端（Thin Client）
**适用**: 飞腾派 1-6 显示节点
