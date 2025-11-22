# 6+1 SAGIN 演示系统访问地址

## 系统架构

```
Pi-0 (控制面板) ──┬─── WebSocket Hub (端口9000)
                 │
                 ├─── Pi-1 (北京)
                 ├─── Pi-2 (上海)
                 ├─── Pi-3 (深圳)
                 ├─── Pi-4 (成都)
                 ├─── Pi-5 (西安)
                 └─── Pi-6 (哈尔滨)
```

---

## 🎛️ 控制面板 (Pi-0)

**主控制台 - Globe.GL全局视图**:
```
http://localhost:8080/control-panel/index.html
```

**轻量版控制台**:
```
http://localhost:8080/control-panel/index-light.html
```

**功能**:
- 🌍 3D地球可视化 (Globe.GL)
- 📡 6个地球节点实时监控
- 🛰️ 卫星轨道显示
- 📊 全局PQ-NTOR统计
- 🔗 网络拓扑可视化

---

## 📺 节点视图 (Pi-1 到 Pi-6)

每个飞腾派显示器展示自己的节点状态和本地视角。

### Pi-1 - 北京节点
```
http://localhost:8080/node-view/index.html?node_id=pi-1&node_name=北京地面站
```

**显示内容**:
- 左侧: 3D地球 (从北京视角)
- 右侧: 本节点状态仪表盘
  - PQ-NTOR握手次数
  - 卫星链路延迟
  - 网络流量统计
  - 在线状态

---

### Pi-2 - 上海节点
```
http://localhost:8080/node-view/index.html?node_id=pi-2&node_name=上海地面站
```

---

### Pi-3 - 深圳节点
```
http://localhost:8080/node-view/index.html?node_id=pi-3&node_name=深圳地面站
```

---

### Pi-4 - 成都节点
```
http://localhost:8080/node-view/index.html?node_id=pi-4&node_name=成都地面站
```

---

### Pi-5 - 西安节点
```
http://localhost:8080/node-view/index.html?node_id=pi-5&node_name=西安地面站
```

---

### Pi-6 - 哈尔滨节点
```
http://localhost:8080/node-view/index.html?node_id=pi-6&node_name=哈尔滨地面站
```

---

## 🔍 测试页面

**简单测试页面**:
```
http://localhost:8080/test-simple.html
```

---

## 📊 实时数据流

所有节点通过WebSocket连接到Hub:
```
ws://localhost:9000
```

**数据格式**:
```json
{
  "type": "node_status",
  "node_id": "pi-1",
  "timestamp": 1732279968,
  "status": {
    "role": "ground",
    "online": true,
    "latitude": 39.9,
    "longitude": 116.4,
    "city": "北京"
  },
  "pq_ntor": {
    "handshakes": 123,
    "avg_time_us": 147
  },
  "links": [
    {
      "target": "satellite-1",
      "delay_ms": 8.5,
      "bandwidth_mbps": 85
    }
  ]
}
```

---

## 🚀 快速启动

所有服务已启动并运行中：

| 服务 | 状态 | 端口 |
|------|------|------|
| WebSocket Hub | ✅ 运行中 | 9000 |
| HTTP Server | ✅ 运行中 | 8080 |
| Pi-1 Agent (北京) | ✅ 运行中 | - |
| Pi-2 Agent (上海) | ✅ 运行中 | - |
| Pi-3 Agent (深圳) | ✅ 运行中 | - |
| Pi-4 Agent (成都) | ✅ 运行中 | - |
| Pi-5 Agent (西安) | ✅ 运行中 | - |
| Pi-6 Agent (哈尔滨) | ✅ 运行中 | - |

---

## 💡 演示说明

### 控制面板 (Pi-0)
- 展示整个SAGIN网络的全局视图
- 可以看到所有6个地球节点在地球上的位置
- 实时更新所有节点的PQ-NTOR握手统计

### 节点视图 (Pi-1~6)
- 每个节点显示自己的本地状态
- 左侧3D地球从该节点所在城市的视角旋转
- 右侧仪表盘显示该节点独立的监控数据
- 数据每2秒更新一次

---

## 🎨 主题配色

- **地球节点**: 蓝绿渐变主题
- **卫星节点**: 紫色渐变主题
- **飞机节点**: 天蓝渐变主题

---

**生成时间**: 2025-11-22 13:49
**版本**: 演示版 v1.0
