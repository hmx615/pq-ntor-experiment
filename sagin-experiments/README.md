# SAGIN NOMA 6+1 分布式展示系统

**创建时间**: 2025-11-16
**版本**: v1.0
**状态**: ✅ 就绪

---

## 📋 系统概述

这是一个分布式SAGIN NOMA演示系统，采用**6+1架构**：
- **6个飞腾派** (Pi-1 到 Pi-6): 运行SAGIN节点，显示节点专属视角
- **1个飞腾派** (Pi-7): 运行全局控制台，显示3D总览+拓扑控制

### 核心特性
- ✅ 真实后台通信（WebSocket实时推送）
- ✅ 12种NOMA拓扑一键切换
- ✅ 6个节点专属视角 + 1个全局视角
- ✅ PQ-NTOR握手统计
- ✅ 实时流量监控
- ✅ 3D地球可视化

---

## 🏗️ 目录结构

```
distributed-demo/
├── backend/                    # 后台服务
│   ├── websocket_hub.py        # WebSocket Hub (Pi-7)
│   ├── node_agent.py           # 节点Agent (Pi-1到Pi-6)
│   └── requirements.txt        # Python依赖
│
├── frontend/                   # 前端界面
│   ├── control-panel/          # 控制台界面 (Pi-7)
│   │   └── index.html
│   ├── node-view/              # 节点视图界面 (Pi-1到Pi-6)
│   │   └── index.html
│   └── shared/                 # 共享资源
│       ├── three.min.js
│       └── globe.gl.min.js
│
├── docker/                     # Docker配置
│   ├── docker-compose-control.yml  # 控制台
│   ├── docker-compose-node.yml     # 节点
│   ├── Dockerfile.hub
│   ├── Dockerfile.agent
│   ├── nginx-control.conf
│   └── nginx-node.conf
│
├── scripts/                    # 部署脚本
│   ├── deploy_all.sh           # 一键部署到7个飞腾派
│   └── test_local.sh           # 本地测试脚本
│
├── configs/                    # 配置文件（未来扩展）
└── README.md                   # 本文件
```

---

## 🚀 快速开始

### 选项1: 本地测试（推荐先测试）

在开发机上测试整个系统：

```bash
cd distributed-demo/scripts

# 启动所有服务
./test_local.sh start

# 访问地址
# - 控制台: http://localhost:8080/control-panel/
# - 节点视图: http://localhost:8080/node-view/?node_id=SAT

# 查看日志
./test_local.sh logs

# 停止服务
./test_local.sh stop
```

### 选项2: 部署到7个飞腾派

**前提条件**:
1. 7个飞腾派已联网，IP地址如下：
   - Pi-1 (SAT): 192.168.100.11
   - Pi-2 (SR): 192.168.100.12
   - Pi-3 (S1R2): 192.168.100.13
   - Pi-4 (S1): 192.168.100.14
   - Pi-5 (S2): 192.168.100.15
   - Pi-6 (T): 192.168.100.16
   - Pi-7 (Control): 192.168.100.17

2. 所有飞腾派已安装Docker和Docker Compose
3. 已配置SSH免密登录（可选，否则需要多次输入密码）

**部署步骤**:

```bash
cd distributed-demo/scripts

# 一键部署到所有飞腾派
./deploy_all.sh

# 根据提示确认部署
# 部署完成后，访问地址会显示在终端
```

**访问地址**:
- 控制台 (Pi-7): http://192.168.100.17
- 节点视图:
  - 卫星 (Pi-1): http://192.168.100.11?node_id=SAT
  - 无人机1 (Pi-2): http://192.168.100.12?node_id=SR
  - 无人机2 (Pi-3): http://192.168.100.13?node_id=S1R2
  - 终端1 (Pi-4): http://192.168.100.14?node_id=S1
  - 终端2 (Pi-5): http://192.168.100.15?node_id=S2
  - 终端3 (Pi-6): http://192.168.100.16?node_id=T

---

## 🎮 使用说明

### 控制台操作

1. 打开控制台页面 (Pi-7的屏幕)
2. 左侧显示3D地球全局视图
3. 右侧控制面板：
   - **拓扑切换**: 点击1-12按钮切换拓扑
   - **系统监控**: 查看节点在线、链路、流量、握手统计
   - **节点状态**: 查看各节点实时状态

### 节点视图

1. 每个节点飞腾派显示自己的专属视角
2. 左侧：3D地球（突出显示当前节点）
3. 右侧：节点状态面板
   - 节点信息（角色、高度、IP）
   - 通信链路（RSSI、延迟、带宽）
   - PQ-NTOR统计
   - 流量统计

### 拓扑切换演示

1. 在控制台点击"拓扑3"
2. 所有7个屏幕会同步切换到拓扑3
3. 各节点视图自动更新链路信息
4. 3D地球上的连接线实时变化

---

## 🔧 故障排查

### 问题1: WebSocket连接失败

**现象**: 前端显示"WebSocket: 连接中..."

**解决**:
```bash
# 检查Hub是否运行
ssh pi@192.168.100.17 "docker ps | grep websocket_hub"

# 查看Hub日志
ssh pi@192.168.100.17 "docker logs sagin_websocket_hub"

# 重启Hub
ssh pi@192.168.100.17 "cd /home/pi/sagin-demo/docker && docker-compose restart"
```

### 问题2: 节点数据不更新

**现象**: 控制台看不到节点数据

**解决**:
```bash
# 检查节点Agent是否运行
ssh pi@192.168.100.11 "docker ps | grep node_agent"

# 查看Agent日志
ssh pi@192.168.100.11 "docker logs sagin_node_SAT"

# 重启节点Agent
ssh pi@192.168.100.11 "cd /home/pi/sagin-demo/docker && docker-compose restart"
```

### 问题3: 拓扑切换无效

**现象**: 点击拓扑按钮，没有反应

**解决**:
1. 检查浏览器控制台是否有错误
2. 确认WebSocket连接正常
3. 查看Hub日志，确认收到拓扑切换命令

### 问题4: 3D地球不显示

**现象**: 页面空白或地球无法渲染

**解决**:
1. 检查网络连接（需要加载外部资源）
2. 查看浏览器控制台错误
3. 确认three.min.js和globe.gl.min.js已加载

---

## 📊 系统架构

### 通信流程

```
节点Agent (Pi-1到Pi-6)
    ↓ 发送状态数据
WebSocket Hub (Pi-7:9000)
    ↓ 广播到所有前端
前端页面（控制台 + 6个节点视图）
    ↓ 实时更新UI
```

### 拓扑切换流程

```
用户在控制台点击"拓扑X"
    ↓
控制台发送 {"type": "change_topology", "topology_id": X}
    ↓
WebSocket Hub接收并广播到所有节点Agent
    ↓
各节点Agent执行拓扑切换（停止/启动Docker容器）
    ↓
节点Agent发送新状态数据
    ↓
所有前端同步更新显示
```

---

## 🛠️ 开发指南

### 添加新功能

1. **修改后台服务**:
   - 编辑 `backend/websocket_hub.py` 或 `backend/node_agent.py`
   - 重新构建Docker镜像

2. **修改前端界面**:
   - 编辑 `frontend/control-panel/index.html` 或 `frontend/node-view/index.html`
   - 刷新浏览器即可看到效果

3. **修改Docker配置**:
   - 编辑 `docker/docker-compose-*.yml`
   - 重新部署

### 本地开发流程

```bash
# 1. 修改代码
vim backend/websocket_hub.py

# 2. 本地测试
cd scripts
./test_local.sh restart

# 3. 访问测试
# 浏览器打开 http://localhost:8080/control-panel/

# 4. 满意后部署到飞腾派
./deploy_all.sh
```

---

## 📝 TODO

- [ ] 集成真实Docker容器监控（替换模拟数据）
- [ ] 实现真实的PQ-NTOR握手统计
- [ ] 添加网络流量真实测量
- [ ] 实现拓扑切换时的真实Docker容器操作
- [ ] 添加数据持久化（保存历史数据）
- [ ] 优化3D地球性能（减少重绘）
- [ ] 添加链路动画效果（数据流动可视化）
- [ ] 支持自定义拓扑配置
- [ ] 添加告警功能（节点离线、链路中断）

---

## 📚 参考文档

- [6+1优化方案.md](../readme/6+1优化方案.md) - 系统设计详细说明
- [12种NOMA网络拓扑定义.md](../readme/12种NOMA网络拓扑定义.md) - 拓扑定义
- [RSSI网络参数映射方案.md](../readme/RSSI网络参数映射方案.md) - 参数映射

---

## 🤝 贡献

如果您有改进建议：
1. 修改代码
2. 测试功能
3. 提交更改

---

## 📄 许可证

内部项目，仅供SAGIN NOMA演示使用

---

**创建者**: Claude AI Assistant
**最后更新**: 2025-11-16
**版本**: v1.0
