# 🚀 快速开始 - 5分钟上手

## 第1步：安装依赖（30秒）

```bash
pip3 install flask flask-cors pandas
```

## 第2步：启动服务（10秒）

```bash
cd /home/ccc/pq-ntor-experiment/web-dashboard
./start.sh
```

## 第3步：打开浏览器（立即）

访问: **http://localhost:8080**

---

## ⌨️ 快捷键

- **F11** - 全屏模式
- **Ctrl+D** - 演示模式（自动模拟数据）
- **Ctrl+L** - 清空日志

---

## 🎬 演示模式

如果没有实际实验数据，启动演示模式：

```
打开浏览器后按 Ctrl+D
系统会自动切换网络配置并更新模拟数据
```

---

## 🐛 故障排查

### 端口被占用？

```bash
# 查看占用
sudo lsof -i :8080

# 清理并重启
pkill -f server.py
./start.sh
```

### API无响应？

```bash
# 测试API
curl http://localhost:8080/api/health
```

### 图表不显示？

检查浏览器控制台（F12）查看错误信息

---

## 📱 全屏Kiosk模式（用于演示）

```bash
./start.sh &
sleep 3
chromium-browser --kiosk http://localhost:8080
```

---

完整文档见: **README.md**
