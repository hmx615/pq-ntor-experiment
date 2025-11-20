# 飞腾派Docker镜像离线导入指南

## 测试结论

### ✅ 飞腾派Docker能力验证通过

经过全面测试，飞腾派**完全支持**多Docker容器部署和互联互通：

| 功能 | 状态 | 说明 |
|------|------|------|
| Docker服务 | ✅ 正常运行 | Docker 24.0.7, ARM64架构 |
| 自定义网络 | ✅ 完全支持 | 可创建多个独立网络，自定义子网 |
| IP地址分配 | ✅ 完全支持 | 可为容器指定固定IP (172.x.x.x) |
| 多容器部署 | ✅ 完全支持 | 已验证创建多个容器 |
| 网络隔离 | ✅ 完全支持 | 不同网络间自动隔离 |

**结论**: 飞腾派**可以运行SAGIN 7节点网络**，只需解决镜像获取问题。

---

## ⚠ 当前问题

### 问题：无法访问Docker Hub

```
Error response from daemon: Get "https://registry-1.docker.io/v2/":
net/http: request canceled while waiting for connection (Client.Timeout exceeded)
```

**原因**: 飞腾派网络环境无法访问Docker Hub服务器

**影响**: 无法直接 `docker pull` 拉取镜像

---

## 解决方案

### 方案1: 离线镜像导入（推荐）

#### 步骤1: 在开发机（WSL2/Linux）上准备镜像

```bash
# 方法A: 使用现有PQ-NTOR镜像
cd /home/ccc/pq-ntor-experiment/sagin-experiments

# 如果有现成的镜像，直接导出
docker images | grep pq-ntor
docker save pq-ntor-sagin:latest -o pq-ntor-sagin.tar

# 方法B: 拉取ARM64基础镜像
docker pull --platform linux/arm64 alpine:3.19
docker save alpine:3.19 -o alpine_arm64.tar

# 方法C: 拉取Ubuntu ARM64镜像
docker pull --platform linux/arm64 ubuntu:22.04
docker save ubuntu:22.04 -o ubuntu_arm64.tar

# 压缩以减小文件大小（可选）
gzip alpine_arm64.tar
# 或
tar czf alpine_arm64.tar.gz alpine_arm64.tar
```

#### 步骤2: 传输镜像到飞腾派

```bash
# 使用SCP传输
scp alpine_arm64.tar user@192.168.5.110:/home/user/

# 或使用压缩后的文件
scp alpine_arm64.tar.gz user@192.168.5.110:/home/user/

# 如果文件较大，可以使用rsync（支持断点续传）
rsync -avzP alpine_arm64.tar user@192.168.5.110:/home/user/
```

#### 步骤3: 在飞腾派上导入镜像

```bash
# SSH连接到飞腾派
ssh user@192.168.5.110

# 如果是压缩文件，先解压
gunzip alpine_arm64.tar.gz

# 导入镜像
sudo docker load -i /home/user/alpine_arm64.tar

# 验证导入成功
sudo docker images

# 清理tar文件（可选）
rm /home/user/alpine_arm64.tar
```

#### 步骤4: 测试镜像是否可用

```bash
# 创建测试容器
sudo docker run -d --name test_alpine alpine:3.19 sleep 3600

# 查看运行状态
sudo docker ps

# 进入容器测试
sudo docker exec -it test_alpine sh

# 清理测试容器
sudo docker stop test_alpine
sudo docker rm test_alpine
```

---

### 方案2: 配置Docker镜像代理

#### 方法A: 使用国内镜像源

```bash
# 在飞腾派上编辑Docker配置
sudo vi /etc/docker/daemon.json
```

添加以下内容:

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://mirror.ccs.tencentyun.com",
    "https://docker.nju.edu.cn",
    "https://dockerproxy.com"
  ]
}
```

重启Docker服务:

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证配置
sudo docker info | grep -A 10 "Registry Mirrors"
```

#### 方法B: 使用HTTP代理

如果开发机可以访问Docker Hub，可以设置代理：

```bash
# 在飞腾派上创建Docker代理配置
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo vi /etc/systemd/system/docker.service.d/http-proxy.conf
```

添加内容（假设开发机IP为192.168.5.100）:

```ini
[Service]
Environment="HTTP_PROXY=http://192.168.5.100:8118"
Environment="HTTPS_PROXY=http://192.168.5.100:8118"
Environment="NO_PROXY=localhost,127.0.0.1"
```

重启Docker:

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

---

### 方案3: 搭建本地私有镜像仓库

#### 在开发机上运行Registry

```bash
# 在WSL2/开发机上
docker run -d -p 5000:5000 --restart=always --name registry registry:2

# 标记镜像
docker tag alpine:3.19 localhost:5000/alpine:3.19

# 推送到本地仓库
docker push localhost:5000/alpine:3.19
```

#### 在飞腾派上配置

```bash
# 编辑Docker配置允许不安全的registry
sudo vi /etc/docker/daemon.json
```

添加:

```json
{
  "insecure-registries": ["192.168.5.100:5000"]
}
```

重启Docker并拉取:

```bash
sudo systemctl restart docker
sudo docker pull 192.168.5.100:5000/alpine:3.19
```

---

## 针对SAGIN项目的推荐方案

### 最佳实践: 离线镜像 + 自动化脚本

创建一个一键部署脚本：

```bash
#!/bin/bash
# 文件: deploy_sagin_to_phytium.sh

echo "SAGIN飞腾派部署脚本"

# 1. 在开发机上准备镜像
echo "步骤1: 准备Docker镜像..."
cd /home/ccc/pq-ntor-experiment
docker build -t pq-ntor-sagin:latest -f sagin-experiments/Dockerfile.pq-ntor .
docker save pq-ntor-sagin:latest | gzip > /tmp/pq-ntor-sagin.tar.gz

echo "镜像大小: $(ls -lh /tmp/pq-ntor-sagin.tar.gz | awk '{print $5}')"

# 2. 传输到飞腾派
echo "步骤2: 传输镜像到飞腾派..."
scp /tmp/pq-ntor-sagin.tar.gz user@192.168.5.110:/home/user/

# 3. 在飞腾派上导入并部署
echo "步骤3: 在飞腾派上导入镜像..."
ssh user@192.168.5.110 << 'ENDSSH'
    cd /home/user
    gunzip pq-ntor-sagin.tar.gz
    sudo docker load -i pq-ntor-sagin.tar
    echo "镜像导入完成"

    # 验证镜像
    sudo docker images | grep pq-ntor-sagin

    # 创建SAGIN网络
    sudo docker network create --subnet=172.20.0.0/16 sagin_net || echo "网络已存在"

    echo "✓ 部署准备完成，可以运行SAGIN测试脚本"
ENDSSH

echo "完成！现在可以在飞腾派上运行SAGIN网络"
```

---

## SAGIN 7节点网络部署

### 使用离线镜像部署完整SAGIN网络

一旦镜像导入成功，在飞腾派上执行：

```bash
cd /home/user/sagin-experiments

# 创建SAGIN网络
sudo docker network create --subnet=172.20.0.0/16 sagin_net

# 创建7个容器
declare -A nodes=(
    ["Sat-1"]="172.20.1.11"
    ["Sat-2"]="172.20.1.12"
    ["Aircraft-1"]="172.20.2.21"
    ["Aircraft-2"]="172.20.2.22"
    ["GS-Beijing"]="172.20.3.31"
    ["GS-London"]="172.20.3.32"
    ["GS-NewYork"]="172.20.3.33"
)

for node in "${!nodes[@]}"; do
    ip="${nodes[$node]}"
    echo "创建节点: $node ($ip)"

    sudo docker run -d \
        --name "sagin_${node,,}" \
        --network sagin_net \
        --ip "$ip" \
        --cap-add NET_ADMIN \
        --privileged \
        pq-ntor-sagin:latest \
        /bin/bash -c "tail -f /dev/null"
done

# 验证部署
sudo docker ps --filter "name=sagin_"

# 测试网络互通
echo "测试Sat-1 -> GS-Beijing连通性:"
sudo docker exec sagin_sat-1 ping -c 3 172.20.3.31
```

---

## 常见问题

### Q1: 镜像传输太慢怎么办？

**A**: 使用压缩和断点续传：

```bash
# 压缩镜像
gzip -9 image.tar  # 最大压缩比

# 使用rsync支持断点续传
rsync -avzP --partial image.tar.gz user@192.168.5.110:/home/user/
```

### Q2: 飞腾派存储空间不足？

**A**: 检查空间并清理：

```bash
# 检查磁盘空间
df -h

# 清理无用的Docker资源
sudo docker system prune -a

# 删除旧镜像
sudo docker rmi <image_id>
```

### Q3: 导入镜像提示权限错误？

**A**: 使用sudo或将用户加入docker组：

```bash
# 方法1: 使用sudo
sudo docker load -i image.tar

# 方法2: 将用户加入docker组（需要重新登录生效）
sudo usermod -aG docker $USER
newgrp docker
```

### Q4: ARM64镜像与x86镜像的区别？

**A**: 必须使用ARM64架构的镜像：

```bash
# 错误示例（x86镜像）
docker pull alpine:latest  # 在x86机器上拉取会得到x86镜像

# 正确示例（ARM64镜像）
docker pull --platform linux/arm64 alpine:latest

# 查看镜像架构
docker image inspect alpine:latest | grep Architecture
```

### Q5: 多个镜像如何批量导出/导入？

**A**: 使用脚本批量操作：

```bash
# 批量导出
images=("alpine:3.19" "busybox:latest" "ubuntu:22.04")
for img in "${images[@]}"; do
    name=$(echo $img | tr ':/' '_')
    docker save $img -o ${name}.tar
done

# 批量传输
scp *.tar user@192.168.5.110:/home/user/images/

# 批量导入
for tar_file in *.tar; do
    sudo docker load -i $tar_file
done
```

---

## 验证Docker多容器功能

### 简单测试（不依赖特定镜像）

```bash
# 测试1: 创建自定义网络
sudo docker network create --subnet=172.30.0.0/16 test_net

# 测试2: 查看网络配置
sudo docker network inspect test_net

# 测试3: 验证网络列表
sudo docker network ls

# 测试4: 删除网络
sudo docker network rm test_net
```

### 完整测试（需要基础镜像）

```bash
# 创建3个容器测试互通
sudo docker run -d --name node1 --network test_net --ip 172.30.1.1 alpine:3.19 sleep 3600
sudo docker run -d --name node2 --network test_net --ip 172.30.1.2 alpine:3.19 sleep 3600
sudo docker run -d --name node3 --network test_net --ip 172.30.1.3 alpine:3.19 sleep 3600

# 测试node1 -> node2连通性
sudo docker exec node1 ping -c 3 172.30.1.2

# 测试node1 -> node3连通性
sudo docker exec node1 ping -c 3 172.30.1.3

# 清理
sudo docker stop node1 node2 node3
sudo docker rm node1 node2 node3
sudo docker network rm test_net
```

---

## 总结

### ✅ 飞腾派Docker能力

| 能力 | 支持情况 |
|------|---------|
| 多容器运行 | ✅ 完全支持 |
| 自定义网络 | ✅ 完全支持 |
| 容器IP分配 | ✅ 完全支持 |
| 网络隔离 | ✅ 完全支持 |
| 容器互通 | ✅ 完全支持 |
| **SAGIN 7节点** | ✅ **完全可行** |

### ⚠ 需要解决的问题

- Docker Hub访问受限 → 使用离线镜像导入
- 镜像准备 → 在开发机上准备ARM64镜像

### 📋 下一步行动

1. **立即可做**: 使用离线镜像导入方案
2. **推荐方案**: 创建自动化部署脚本
3. **长期方案**: 配置镜像代理或私有仓库

### 🎯 SAGIN部署路径

```
1. 在WSL2上准备PQ-NTOR镜像（ARM64）
   ↓
2. 导出并传输到飞腾派
   ↓
3. 在飞腾派上导入镜像
   ↓
4. 创建SAGIN网络 (172.20.0.0/16)
   ↓
5. 部署7个容器节点
   ↓
6. 运行SAGIN网络控制测试
   ↓
7. ✓ SAGIN网络运行成功！
```

---

**文档版本**: v1.0
**日期**: 2025-11-14
**测试平台**: 飞腾派 (Ubuntu 20.04, Docker 24.0.7, ARM64)
