# 版本说明

## 当前正式版本

**目录**: `/home/ccc/pq-ntor-experiment/sagin-experiments/frontend/`

**启动脚本**: `start_correct_version.sh`

### 功能特性

**控制面板 (control-panel/)**
- ✅ 左上角实时时间显示
- ✅ 左下角链路图例（绿色/橙色/紫色）
- ✅ 12个拓扑完整支持，Topo 7-12 显示紫色协作NOMA链路
- ✅ 3D地球视图
- ✅ 节点状态实时显示

**节点视图 (node-view/)**
- ✅ 左上角实时时间显示
- ✅ 左下角链路图例（放大版）
- ✅ 3D地球视图，节点高亮显示
- ✅ 链路实时显示（绿色/橙色/紫色）
- ✅ 节点信息面板
- ✅ PQ-NTOR 统计
- ✅ 流量统计
- ✅ 通信链路列表
- ✅ 底部节点标识 Badge（简洁显示，无重复）
- ✅ 已移除特性面板（界面简洁）

### 节点配置

```javascript
SAT (卫星):     550 km
UAV1 (无人机1): 150 m
UAV2 (无人机2): 200 m
Ground1 (终端1): 5 m
Ground2 (终端2): 3 m
Ground3 (终端3): 8 m
```

### 访问地址（飞腾派）

```
控制面板: http://192.168.5.83:8080/control-panel/
节点视图: http://192.168.5.83:8080/node-view/index.html?node_id=SAT
节点视图: http://192.168.5.83:8080/node-view/index.html?node_id=UAV1
节点视图: http://192.168.5.83:8080/node-view/index.html?node_id=UAV2
节点视图: http://192.168.5.83:8080/node-view/index.html?node_id=Ground1
节点视图: http://192.168.5.83:8080/node-view/index.html?node_id=Ground2
节点视图: http://192.168.5.83:8080/node-view/index.html?node_id=Ground3
```

### 启动命令

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments
./start_correct_version.sh
```

### 停止命令

```bash
pkill -f websocket_hub.py
pkill -f node_agent.py
pkill -f http.server
```

## 备份版本

**备份文件**: `all-backup-versions-20251127.tar.gz`
- 包含所有历史版本的备份
- 包括 distributed-demo 的多个版本
- 仅用于紧急恢复，不应使用

## 重要说明

⚠️ **只使用 `frontend/` 目录，不要使用其他版本！**

⚠️ **`distributed-demo/` 目录已删除，已备份到 tar.gz 文件中**

⚠️ **启动时务必使用 `start_correct_version.sh` 脚本**

## 修改历史

- 2025-11-27: 设置 frontend/ 为正式版本
- 2025-11-27: 修复字体显示问题
- 2025-11-27: 修复 WebSocket IP 自动检测
- 2025-11-27: 修复节点 ID 映射 (UAV1, UAV2, Ground1-3)
- 2025-11-27: 修复节点高度显示
- 2025-11-27: 移除特性面板，界面简洁化
- 2025-11-27: 放大链路图例
- 2025-11-27: 修复底部 Badge 重复显示
- 2025-11-27: 备份并删除 distributed-demo 版本
