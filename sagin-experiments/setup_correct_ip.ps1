# WSL端口转发配置 - 使用正确的有线网卡IP
# Windows主机有两个网卡:
#   - WLAN 2 (无线): 192.168.5.144 (路由器可能隔离)
#   - 以太网 (有线): 192.168.5.83 ✅ 飞腾派可访问

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WSL端口转发配置 - 使用有线网卡" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[错误] 请以管理员身份运行此脚本！" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[✓] 管理员权限确认" -ForegroundColor Green
Write-Host ""

# WSL IP
$wslIP = "192.168.74.81"

# Windows网卡IP
$ethernetIP = "192.168.5.83"   # 有线网卡 (飞腾派可访问)
$wlanIP = "192.168.5.144"       # 无线网卡 (可能被隔离)

Write-Host "[网络配置]" -ForegroundColor Yellow
Write-Host "  WSL IP: $wslIP" -ForegroundColor White
Write-Host "  Windows以太网: $ethernetIP ✓ (使用此IP)" -ForegroundColor Green
Write-Host "  Windows WLAN: $wlanIP ✗ (可能被路由器隔离)" -ForegroundColor Gray
Write-Host "  飞腾派: 192.168.5.110" -ForegroundColor White
Write-Host ""

# 清理旧的端口转发规则
Write-Host "[步骤1] 清理旧配置..." -ForegroundColor Yellow
netsh interface portproxy reset | Out-Null
Write-Host "  ✓ 已清除所有旧的端口转发规则" -ForegroundColor Green
Write-Host ""

# 添加新的端口转发规则
Write-Host "[步骤2] 配置端口转发..." -ForegroundColor Yellow

# 选项1: 绑定到所有接口 (0.0.0.0)
Write-Host "  配置方式: 监听所有网络接口" -ForegroundColor Cyan

netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=$wslIP
if ($?) {
    Write-Host "    ✓ HTTP (8080) 转发已配置" -ForegroundColor Green
} else {
    Write-Host "    ✗ HTTP (8080) 配置失败" -ForegroundColor Red
}

netsh interface portproxy add v4tov4 listenport=9000 listenaddress=0.0.0.0 connectport=9000 connectaddress=$wslIP
if ($?) {
    Write-Host "    ✓ WebSocket (9000) 转发已配置" -ForegroundColor Green
} else {
    Write-Host "    ✗ WebSocket (9000) 配置失败" -ForegroundColor Red
}
Write-Host ""

# 配置防火墙规则
Write-Host "[步骤3] 配置防火墙..." -ForegroundColor Yellow

# 清理旧规则
Remove-NetFirewallRule -DisplayName "WSL HTTP Server" -ErrorAction SilentlyContinue 2>$null
Remove-NetFirewallRule -DisplayName "WSL WebSocket Hub" -ErrorAction SilentlyContinue 2>$null
Remove-NetFirewallRule -DisplayName "Allow ICMPv4 Inbound" -ErrorAction SilentlyContinue 2>$null

# ICMP (允许Ping)
New-NetFirewallRule -DisplayName "Allow ICMPv4 Inbound" `
    -Direction Inbound `
    -Protocol ICMPv4 `
    -IcmpType 8 `
    -Action Allow `
    -Profile Any `
    -ErrorAction SilentlyContinue | Out-Null
Write-Host "  ✓ ICMP (Ping) 已允许" -ForegroundColor Green

# HTTP
New-NetFirewallRule -DisplayName "WSL HTTP Server" `
    -Direction Inbound `
    -LocalPort 8080 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any `
    -ErrorAction SilentlyContinue | Out-Null
Write-Host "  ✓ HTTP (8080) 防火墙规则已添加" -ForegroundColor Green

# WebSocket
New-NetFirewallRule -DisplayName "WSL WebSocket Hub" `
    -Direction Inbound `
    -LocalPort 9000 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any `
    -ErrorAction SilentlyContinue | Out-Null
Write-Host "  ✓ WebSocket (9000) 防火墙规则已添加" -ForegroundColor Green
Write-Host ""

# 验证配置
Write-Host "[步骤4] 验证配置..." -ForegroundColor Yellow
Write-Host ""
Write-Host "端口转发规则:" -ForegroundColor Cyan
netsh interface portproxy show all
Write-Host ""

# 测试连接
Write-Host "[步骤5] 测试连接..." -ForegroundColor Yellow
Write-Host ""

# 测试到飞腾派
Write-Host "  测试 Windows → 飞腾派 (192.168.5.110):" -ForegroundColor Cyan
$pingPi = Test-Connection -ComputerName 192.168.5.110 -Count 2 -ErrorAction SilentlyContinue
if ($pingPi) {
    Write-Host "    ✓ Ping成功！延迟: $($pingPi[0].ResponseTime)ms" -ForegroundColor Green
} else {
    Write-Host "    ✗ Ping失败" -ForegroundColor Red
}

# 测试本地端口
Write-Host ""
Write-Host "  测试本地服务端口:" -ForegroundColor Cyan
$testHTTP = Test-NetConnection -ComputerName localhost -Port 8080 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
$testWS = Test-NetConnection -ComputerName localhost -Port 9000 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue

if ($testHTTP.TcpTestSucceeded) {
    Write-Host "    ✓ HTTP (8080) 监听中" -ForegroundColor Green
} else {
    Write-Host "    ✗ HTTP (8080) 未监听 - 请在WSL中启动服务" -ForegroundColor Yellow
}

if ($testWS.TcpTestSucceeded) {
    Write-Host "    ✓ WebSocket (9000) 监听中" -ForegroundColor Green
} else {
    Write-Host "    ✗ WebSocket (9000) 未监听 - 请在WSL中启动服务" -ForegroundColor Yellow
}
Write-Host ""

# 显示访问地址
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "飞腾派访问地址 (使用有线网卡IP):" -ForegroundColor Yellow
Write-Host ""
Write-Host "  控制面板:" -ForegroundColor Cyan
Write-Host "    http://$ethernetIP:8080/control-panel/index.html" -ForegroundColor White
Write-Host ""
Write-Host "  节点视图:" -ForegroundColor Cyan
Write-Host "    SAT:  http://$ethernetIP:8080/node-view/index.html?node_id=SAT" -ForegroundColor White
Write-Host "    SR:   http://$ethernetIP:8080/node-view/index.html?node_id=SR" -ForegroundColor White
Write-Host "    S1R2: http://$ethernetIP:8080/node-view/index.html?node_id=S1R2" -ForegroundColor White
Write-Host "    S1:   http://$ethernetIP:8080/node-view/index.html?node_id=S1" -ForegroundColor White
Write-Host "    S2:   http://$ethernetIP:8080/node-view/index.html?node_id=S2" -ForegroundColor White
Write-Host "    T:    http://$ethernetIP:8080/node-view/index.html?node_id=T" -ForegroundColor White
Write-Host ""

Write-Host "在飞腾派上测试 (SSH或直接执行):" -ForegroundColor Yellow
Write-Host "  ping $ethernetIP" -ForegroundColor Gray
Write-Host "  curl http://$ethernetIP:8080/" -ForegroundColor Gray
Write-Host ""

Write-Host "如果WSL服务未启动，在WSL中执行:" -ForegroundColor Yellow
Write-Host "  cd /home/ccc/pq-ntor-experiment/sagin-experiments/frontend" -ForegroundColor Gray
Write-Host "  python3 -m http.server 8080 --bind 0.0.0.0 &" -ForegroundColor Gray
Write-Host "  cd ../backend" -ForegroundColor Gray
Write-Host "  python3 websocket_hub.py &" -ForegroundColor Gray
Write-Host ""

pause
