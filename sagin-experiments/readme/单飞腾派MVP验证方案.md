# 单飞腾派MVP验证方案

## 核心思路

在**一个飞腾派**上运行所有7个节点（使用Docker容器），验证：
1. ✅ PQ-NTOR多节点通信能力
2. ✅ 动态网络拓扑控制
3. ✅ 卫星轨道可视化UI
4. ✅ 完整系统架构可行性

验证成功后，将整个环境**镜像克隆**到其他6个飞腾派，每个飞腾派只运行1个容器（物理分布式部署）。

---

## 1. 单飞腾派架构（MVP版本）

### 1.1 Docker容器方案

```
飞腾派 (192.168.5.110)
├── Docker容器1: Sat-1      (172.20.1.11)  - Guard节点
├── Docker容器2: Sat-2      (172.20.1.12)  - ISL中继
├── Docker容器3: Aircraft-1 (172.20.2.21)  - Middle节点
├── Docker容器4: Aircraft-2 (172.20.2.22)  - 备用中继
├── Docker容器5: GS-Beijing (172.20.3.31)  - Client客户端
├── Docker容器6: GS-London  (172.20.3.32)  - Exit节点
├── Docker容器7: GS-NewYork (172.20.3.33)  - Directory服务
└── 显示器UI: 卫星轨道可视化 (主机直接运行)
```

**优势**：
- ✅ 在1个设备上完整验证整个系统
- ✅ Docker网络完全隔离，模拟真实分布式环境
- ✅ 可以使用简化版网络控制（iptables，已验证可用）
- ✅ 开发调试方便，所有日志在一处
- ✅ 验证成功后，直接镜像系统到其他飞腾派

### 1.2 与最终7飞腾派方案的对应关系

| MVP阶段 | 最终部署 |
|---------|---------|
| 1个飞腾派 + 7个Docker容器 | 7个飞腾派，每个1个容器 |
| iptables控制容器间链路 | iptables控制物理设备间链路 |
| UI显示在1个屏幕 | 每个飞腾派1个屏幕显示本节点 |
| 手动启动容器 | systemd自动启动 |

---

## 2. 卫星轨道可视化UI设计

### 2.1 显示效果示意

```
┌─────────────────────────────────────────────────────────────┐
│           SAGIN PQ-NTOR 网络拓扑实时演示                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│        北极                                                 │
│         ▲                                                   │
│         │                                                   │
│         │         ●Sat-2 (ISL)                              │
│         │       ╱  ╲                                        │
│    ●────●───●Sat-1   ●Aircraft-2                           │
│   🌍地球  │    ╲   ╱                                        │
│         │     ●Aircraft-1                                   │
│         │      │                                            │
│         │   ●──┴──●                                         │
│         │  GS-Bei GS-Lon                                    │
│        南极  ●GS-NY                                         │
│                                                             │
│  链路状态:                                                  │
│  ━━━ 活跃链路 (绿色)    ╌╌╌ 不可见链路 (灰色)              │
│                                                             │
│  实时统计:                                                  │
│  ├ PQ-NTOR握手: 23次   平均延迟: 49μs                      │
│  ├ 活跃电路: 2条       总流量: 1.2MB                        │
│  └ 网络延迟: Sat→GS 5.2ms  ISL 10.1ms                      │
│                                                             │
│  [UTC时间: 2025-11-14 03:25:10]  按Q退出                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术实现方案

#### 方案A: Python + Pygame（推荐用于演示）

```python
import pygame
import math
from datetime import datetime

class SAGINVisualizer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("SAGIN PQ-NTOR 网络拓扑")

        # 地球参数
        self.earth_radius = 150
        self.earth_pos = (640, 360)

        # 卫星轨道参数（LEO：550km高度）
        self.orbit_radius = self.earth_radius + 50

    def draw_earth(self):
        """绘制地球"""
        pygame.draw.circle(
            self.screen,
            (0, 100, 200),  # 蓝色
            self.earth_pos,
            self.earth_radius
        )

        # 绘制大陆轮廓（简化）
        pygame.draw.circle(
            self.screen,
            (34, 139, 34),  # 绿色
            (self.earth_pos[0] + 50, self.earth_pos[1]),
            30
        )

    def calculate_satellite_position(self, angle, orbit_radius):
        """计算卫星位置（极地轨道）"""
        x = self.earth_pos[0] + orbit_radius * math.cos(angle)
        y = self.earth_pos[1] + orbit_radius * math.sin(angle)
        return (int(x), int(y))

    def draw_satellite(self, pos, name, is_active):
        """绘制卫星节点"""
        color = (0, 255, 0) if is_active else (128, 128, 128)
        pygame.draw.circle(self.screen, color, pos, 8)

        # 标签
        font = pygame.font.Font(None, 20)
        text = font.render(name, True, (255, 255, 255))
        self.screen.blit(text, (pos[0] + 10, pos[1] - 10))

    def draw_link(self, pos1, pos2, is_active, link_type):
        """绘制链路"""
        if is_active:
            color = (0, 255, 0)   # 绿色：活跃
            width = 2
        else:
            color = (64, 64, 64)  # 灰色：不可见
            width = 1

        pygame.draw.line(self.screen, color, pos1, pos2, width)

        # 显示链路类型标签
        if is_active:
            mid_x = (pos1[0] + pos2[0]) // 2
            mid_y = (pos1[1] + pos2[1]) // 2
            font = pygame.font.Font(None, 16)
            text = font.render(link_type, True, (255, 200, 0))
            self.screen.blit(text, (mid_x, mid_y))

    def update(self, orbit_sim, network_mgr):
        """主循环更新"""
        clock = pygame.time.Clock()
        angle_sat1 = 0
        angle_sat2 = math.pi  # 反向轨道

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False

            # 清屏
            self.screen.fill((0, 0, 0))

            # 绘制地球
            self.draw_earth()

            # 计算卫星位置（模拟轨道运动）
            angle_sat1 += 0.01  # 每帧移动角度
            angle_sat2 += 0.01

            sat1_pos = self.calculate_satellite_position(
                angle_sat1, self.orbit_radius
            )
            sat2_pos = self.calculate_satellite_position(
                angle_sat2, self.orbit_radius
            )

            # 固定地面站位置
            gs_beijing_pos = (
                self.earth_pos[0] + self.earth_radius * math.cos(0.8),
                self.earth_pos[1] + self.earth_radius * math.sin(0.8)
            )
            gs_london_pos = (
                self.earth_pos[0] + self.earth_radius * math.cos(2.5),
                self.earth_pos[1] + self.earth_radius * math.sin(2.5)
            )

            # 判断链路可见性（简化：根据角度）
            # 实际应使用 orbit_sim.is_link_available()
            sat1_beijing_visible = self._check_visibility(
                sat1_pos, gs_beijing_pos
            )

            # 绘制链路
            self.draw_link(
                sat1_pos, sat2_pos,
                True,  # ISL总是可见
                "ISL 10ms"
            )
            self.draw_link(
                sat1_pos, gs_beijing_pos,
                sat1_beijing_visible,
                "SG 5ms"
            )

            # 绘制节点
            self.draw_satellite(sat1_pos, "Sat-1", True)
            self.draw_satellite(sat2_pos, "Sat-2", True)
            self.draw_satellite(gs_beijing_pos, "GS-Bei", True)
            self.draw_satellite(gs_london_pos, "GS-Lon", True)

            # 显示统计信息
            self._draw_stats()

            pygame.display.flip()
            clock.tick(30)  # 30 FPS

        pygame.quit()

    def _check_visibility(self, sat_pos, gs_pos):
        """简化的可见性检查"""
        # 实际应使用仰角计算
        distance = math.sqrt(
            (sat_pos[0] - gs_pos[0])**2 +
            (sat_pos[1] - gs_pos[1])**2
        )
        return distance < 250  # 简化判断

    def _draw_stats(self):
        """绘制统计面板"""
        font = pygame.font.Font(None, 24)

        stats = [
            "PQ-NTOR握手: 23次  平均延迟: 49μs",
            "活跃电路: 2条  总流量: 1.2MB",
            f"UTC时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        ]

        y = 10
        for stat in stats:
            text = font.render(stat, True, (255, 255, 255))
            self.screen.blit(text, (10, y))
            y += 30
```

#### 方案B: Web界面 + Three.js 3D（更炫酷）

```html
<!DOCTYPE html>
<html>
<head>
    <title>SAGIN 3D可视化</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="canvas"></div>
    <script>
        // 创建3D场景
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer();

        // 地球（使用纹理）
        const earthGeometry = new THREE.SphereGeometry(5, 32, 32);
        const earthMaterial = new THREE.MeshBasicMaterial({
            map: new THREE.TextureLoader().load('earth_texture.jpg')
        });
        const earth = new THREE.Mesh(earthGeometry, earthMaterial);
        scene.add(earth);

        // 卫星（小球体）
        function createSatellite(name, color, position) {
            const geometry = new THREE.SphereGeometry(0.3, 16, 16);
            const material = new THREE.MeshBasicMaterial({ color: color });
            const satellite = new THREE.Mesh(geometry, material);
            satellite.position.set(...position);
            satellite.userData.name = name;
            scene.add(satellite);
            return satellite;
        }

        // 链路（线条）
        function createLink(pos1, pos2, isActive) {
            const material = new THREE.LineBasicMaterial({
                color: isActive ? 0x00ff00 : 0x404040
            });
            const geometry = new THREE.BufferGeometry().setFromPoints([pos1, pos2]);
            const line = new THREE.Line(geometry, material);
            scene.add(line);
            return line;
        }

        // 动画循环
        function animate() {
            requestAnimationFrame(animate);

            // 旋转地球
            earth.rotation.y += 0.001;

            // 更新卫星轨道位置
            updateSatellitePositions();

            renderer.render(scene, camera);
        }

        animate();
    </script>
</body>
</html>
```

#### 方案C: 终端UI + ASCII艺术（极客风格）

```python
import curses
import math
import time

class TerminalSAGINUI:
    def __init__(self):
        self.earth_char = "🌍"
        self.satellite_char = "●"
        self.link_active = "━"
        self.link_inactive = "╌"

    def draw(self, stdscr):
        curses.curs_set(0)  # 隐藏光标

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            # 标题
            title = "SAGIN PQ-NTOR 网络拓扑"
            stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

            # 地球中心
            earth_y, earth_x = height // 2, width // 2
            stdscr.addstr(earth_y, earth_x, "●", curses.color_pair(1))
            stdscr.addstr(earth_y, earth_x + 2, "Earth")

            # 卫星位置（简化）
            sat1_y, sat1_x = earth_y - 5, earth_x - 10
            sat2_y, sat2_x = earth_y - 5, earth_x + 10

            stdscr.addstr(sat1_y, sat1_x, "◉ Sat-1", curses.color_pair(2))
            stdscr.addstr(sat2_y, sat2_x, "◉ Sat-2", curses.color_pair(2))

            # 地面站
            gs_y, gs_x = earth_y + 5, earth_x
            stdscr.addstr(gs_y, gs_x - 10, "▲ GS-Beijing", curses.color_pair(3))
            stdscr.addstr(gs_y, gs_x + 5, "▲ GS-London", curses.color_pair(3))

            # 链路（使用ASCII线条）
            # Sat-1 到 Sat-2 (ISL)
            for i in range(sat1_x + 6, sat2_x):
                stdscr.addstr(sat1_y, i, "─", curses.color_pair(4))

            # 统计信息
            stats_y = height - 5
            stdscr.addstr(stats_y, 2, "PQ-NTOR握手: 23次", curses.A_BOLD)
            stdscr.addstr(stats_y + 1, 2, "平均延迟: 49μs")
            stdscr.addstr(stats_y + 2, 2, "活跃链路: 5条")

            # 按Q退出提示
            stdscr.addstr(height - 1, 2, "按 Q 退出", curses.A_DIM)

            stdscr.refresh()

            # 检查键盘输入
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                break

            time.sleep(0.1)

if __name__ == '__main__':
    curses.wrapper(TerminalSAGINUI().draw)
```

---

## 3. 单飞腾派MVP实施步骤

### 步骤1: 准备Docker镜像（离线导入）

由于飞腾派无法访问Docker Hub，我们需要：

```bash
# 在WSL2上（有网络的机器）
cd /home/ccc/pq-ntor-experiment

# 方法1: 拉取Alpine ARM64基础镜像
docker pull --platform linux/arm64 alpine:3.19

# 方法2: 或者构建PQ-NTOR专用镜像
docker buildx build --platform linux/arm64 \
    -t pq-ntor-sagin:arm64 \
    -f sagin-experiments/Dockerfile.pq-ntor .

# 导出镜像
docker save alpine:3.19 | gzip > /tmp/alpine_arm64.tar.gz

# 传输到飞腾派
scp /tmp/alpine_arm64.tar.gz user@192.168.5.110:/home/user/

# 在飞腾派上导入
ssh user@192.168.5.110
gunzip alpine_arm64.tar.gz
sudo docker load -i alpine_arm64.tar
```

### 步骤2: 在飞腾派上创建SAGIN网络

```bash
# SSH到飞腾派
ssh user@192.168.5.110

# 创建Docker网络
sudo docker network create --subnet=172.20.0.0/16 sagin_net

# 创建7个容器
sudo docker run -d --name sagin_sat-1 \
    --network sagin_net --ip 172.20.1.11 \
    --cap-add NET_ADMIN --privileged \
    alpine:3.19 sleep infinity

sudo docker run -d --name sagin_sat-2 \
    --network sagin_net --ip 172.20.1.12 \
    --cap-add NET_ADMIN --privileged \
    alpine:3.19 sleep infinity

# ... 创建其余5个容器（Aircraft-1/2, GS-Beijing/London/NewYork）

# 验证容器运行
sudo docker ps
```

### 步骤3: 在容器内安装PQ-NTOR程序

```bash
# 编译PQ-NTOR（在飞腾派主机上）
cd /home/user/pq-ntor-experiment/c
make clean && make

# 复制到容器
for container in sagin_sat-1 sagin_sat-2 sagin_aircraft-1 \
                 sagin_gs-beijing sagin_gs-london sagin_gs-newyork; do
    sudo docker cp relay $container:/usr/local/bin/
    sudo docker cp client $container:/usr/local/bin/
    sudo docker cp directory_server $container:/usr/local/bin/
done

# 启动Directory服务（在GS-NewYork容器内）
sudo docker exec -d sagin_gs-newyork directory_server -p 5000

# 启动Relay节点（在各卫星/飞行器容器内）
sudo docker exec -d sagin_sat-1 relay -p 9001 -i Sat-1
sudo docker exec -d sagin_sat-2 relay -p 9002 -i Sat-2
sudo docker exec -d sagin_aircraft-1 relay -p 9003 -i Aircraft-1
```

### 步骤4: 测试PQ-NTOR握手

```bash
# 在GS-Beijing容器内发起连接
sudo docker exec -it sagin_gs-beijing client \
    -d 172.20.3.33 -p 5000

# 查看日志
sudo docker logs sagin_sat-1
```

### 步骤5: 部署可视化UI（主机运行）

```bash
# 安装Python依赖
pip3 install --user pygame

# 运行可视化程序
cd /home/user/sagin-experiments/ui
python3 sagin_visualizer.py
```

---

## 4. 镜像克隆部署方案（未来7飞腾派）

### 4.1 飞腾派系统镜像制作

```bash
# 步骤1: 在当前验证成功的飞腾派上，清理临时文件
sudo apt clean
sudo rm -rf /tmp/*
sudo docker system prune -a

# 步骤2: 创建系统镜像
# 方法A: 使用SD卡克隆工具（推荐）
# 关闭飞腾派，取出SD卡
# 在PC上使用 Win32DiskImager 或 dd 命令制作镜像

# 方法B: 使用rsync备份（在线克隆）
rsync -aAXv --exclude={"/dev/*","/proc/*","/sys/*","/tmp/*"} \
    / /mnt/backup/

# 步骤3: 将镜像写入其他6个SD卡
# 使用 Win32DiskImager 或 dd 命令
```

### 4.2 每个飞腾派的个性化配置

```bash
# 每个飞腾派启动后，执行配置脚本
# /home/user/configure_node.sh

#!/bin/bash
# 根据飞腾派编号配置节点角色

case "$HOSTNAME" in
    "phytium-pi-1")
        NODE_NAME="Sat-1"
        NODE_IP="192.168.100.11"
        CONTAINER_NAME="sagin_sat-1"
        ;;
    "phytium-pi-2")
        NODE_NAME="Sat-2"
        NODE_IP="192.168.100.12"
        CONTAINER_NAME="sagin_sat-2"
        ;;
    # ... 其他5个节点
esac

# 配置静态IP
cat > /etc/netplan/01-netcfg.yaml <<EOF
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - $NODE_IP/24
      gateway4: 192.168.100.1
      nameservers:
        addresses: [8.8.8.8]
EOF

sudo netplan apply

# 只启动本节点对应的容器
sudo docker start $CONTAINER_NAME

# 停止其他6个容器
sudo docker stop $(sudo docker ps -a --format "{{.Names}}" | grep -v $CONTAINER_NAME)

echo "节点 $NODE_NAME 配置完成"
```

### 4.3 每个飞腾派的UI显示

```python
# /home/user/sagin-experiments/ui/single_node_display.py
import os

# 读取节点配置
NODE_NAME = os.environ.get('NODE_NAME', 'Unknown')

class SingleNodeDisplay:
    def __init__(self, node_name):
        self.node_name = node_name

    def show_satellite_view(self):
        """卫星节点显示：轨道视图"""
        if 'Sat' in self.node_name:
            # 显示地球+本卫星轨道
            self.draw_earth_and_orbit()
            self.draw_satellite_position(self.node_name)
            self.draw_visible_links()

    def show_ground_station_view(self):
        """地面站显示：网络拓扑"""
        if 'GS' in self.node_name:
            # 显示网络拓扑图
            self.draw_network_topology()
            self.draw_statistics()

# 启动显示
display = SingleNodeDisplay(NODE_NAME)
if 'Sat' in NODE_NAME:
    display.show_satellite_view()
else:
    display.show_ground_station_view()
```

---

## 5. 开发时间线（单飞腾派MVP）

| 阶段 | 任务 | 预计时间 | 交付物 |
|------|------|---------|--------|
| **Week 1** | 镜像准备和Docker部署 | 2-3天 | 7个容器运行 |
| **Week 1** | PQ-NTOR程序编译和测试 | 2-3天 | 基础握手成功 |
| **Week 2** | 网络拓扑控制集成 | 3-4天 | 动态链路控制 |
| **Week 2** | 可视化UI开发（Pygame版） | 3-4天 | 卫星轨道动画 |
| **Week 3** | 动态拓扑集成和调试 | 5-7天 | 完整演示系统 |

**总计**: 2-3周（单人开发）

---

## 6. 可视化UI三种方案对比

| 方案 | 技术栈 | 开发难度 | 视觉效果 | 适合场景 |
|------|--------|---------|---------|---------|
| **Pygame** | Python + Pygame | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ 良好 | 快速开发，适合原型 |
| **Three.js** | Web + Three.js | ⭐⭐⭐⭐ 较难 | ⭐⭐⭐⭐⭐ 3D炫酷 | 正式展示，远程访问 |
| **curses** | Python + curses | ⭐⭐ 简单 | ⭐⭐ 终端风格 | 极客风格，轻量级 |

**推荐**: 先用**Pygame**快速验证，后期有需要再升级到**Three.js 3D**

---

## 7. 立即可执行的第一步

### 今天就可以开始（在当前飞腾派上）：

```bash
# 1. 测试Docker基本功能（已验证可用）
sudo docker network create --subnet=172.20.0.0/16 sagin_net

# 2. 创建测试容器（使用hello-world镜像）
sudo docker create --name test_sat1 \
    --network sagin_net --ip 172.20.1.11 \
    hello-world

sudo docker create --name test_sat2 \
    --network sagin_net --ip 172.20.1.12 \
    hello-world

# 3. 验证网络配置
sudo docker inspect test_sat1 | grep IPAddress

# 4. 清理测试
sudo docker rm test_sat1 test_sat2
sudo docker network rm sagin_net
```

### 明天可以做：

```bash
# 1. 准备Alpine镜像（我帮您从WSL2导出并传输）
# 2. 在飞腾派上安装Pygame
pip3 install --user pygame

# 3. 创建第一个可视化demo
# 我会为您编写一个简单的卫星轨道动画示例
```

---

## 8. 需要我现在帮您做什么？

请选择：

**A. 立即执行代码** - 我开始在飞腾派上创建Docker容器和测试网络

**B. 先写UI Demo** - 我先为您编写一个卫星轨道可视化的示例程序（Pygame）

**C. 准备镜像** - 我在WSL2上准备Alpine ARM64镜像并传输到飞腾派

**D. 全部执行** - 按照上述步骤依次进行（预计30分钟）

---

## 9. MVP成功标准

验证成功的标志：

- [ ] 7个Docker容器成功运行在1个飞腾派上
- [ ] 容器间网络互通（ping测试）
- [ ] PQ-NTOR程序可在容器内运行
- [ ] 简化版网络控制器可动态启用/禁用链路
- [ ] 可视化UI显示卫星轨道动画
- [ ] UI实时显示链路状态（活跃/不可见）
- [ ] 整个系统可稳定运行30分钟以上

达成后，即可镜像到其他6个飞腾派！

---

**总结**: 这个方案的核心优势是：
1. ✅ **风险低** - 在1个设备上完整验证
2. ✅ **成本低** - 不需要等待其他6个飞腾派
3. ✅ **可扩展** - 验证成功后，镜像即可部署
4. ✅ **开发快** - 集中调试，无需处理分布式问题

您觉得这个方案如何？我们从哪里开始？
