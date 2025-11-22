# 6+1 SAGIN系统正确访问地址

## 系统拓扑结构

```
Pi-0 (控制面板)
   │
   ├─── Pi-1: 🛰 SAT (卫星)
   ├─── Pi-2: ✈ SR (无人机1)
   ├─── Pi-3: ✈ S1R2 (无人机2)
   ├─── Pi-4: 📱 S1 (终端1)
   ├─── Pi-5: 📱 S2 (终端2)
   └─── Pi-6: 📱 T (终端3)
```

---

## 🎛️ Pi-0 控制面板

**主控制台**:
```
http://localhost:8080/control-panel/index.html
```

**轻量版控制台**:
```
http://localhost:8080/control-panel/index-light.html
```

---

## 📺 节点视图 (Pi-1 到 Pi-6)

### Pi-1: 🛰 卫星节点
```
http://localhost:8080/node-view/index.html?node_id=SAT
```

### Pi-2: ✈ 无人机1
```
http://localhost:8080/node-view/index.html?node_id=SR
```

### Pi-3: ✈ 无人机2
```
http://localhost:8080/node-view/index.html?node_id=S1R2
```

### Pi-4: 📱 终端1
```
http://localhost:8080/node-view/index.html?node_id=S1
```

### Pi-5: 📱 终端2
```
http://localhost:8080/node-view/index.html?node_id=S2
```

### Pi-6: 📱 终端3
```
http://localhost:8080/node-view/index.html?node_id=T
```

---

## 📊 运行状态

| 服务 | 状态 | 端口 |
|------|------|------|
| WebSocket Hub | ✅ 运行中 | 9000 |
| HTTP Server | ✅ 运行中 | 8080 |
| 节点Agents (6个) | ✅ 运行中 | - |

---

## 🎯 各节点功能

### 控制面板 (Pi-0)
- Globe.GL 3D地球全景视图
- 实时监控所有6个节点
- 网络拓扑可视化
- PQ-NTOR全局统计

### 节点视图 (Pi-1~6)
**左侧**: 3D地球（从该节点视角）
- 显示所有节点位置
- 当前节点高亮显示
- 链路连线可视化

**右侧**: 状态仪表盘
- 在线状态
- 节点特征
- 通信链路详情
- PQ-NTOR握手统计
- 流量监控

---

**生成时间**: 2025-11-22
**系统**: SAGIN 1卫星+2无人机+3终端
