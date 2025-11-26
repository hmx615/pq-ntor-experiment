# WSL端口转发配置脚本
# 用途: 让外部设备(飞腾派)访问WSL内的Web服务
# 运行方式: 以管理员身份运行PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WSL端口转发配置脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取WSL IP
$wslIP = "192.168.74.81"
Write-Host "[信息] WSL IP地址: $wslIP" -ForegroundColor Green

# 获取Windows主机IP
$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {($_.IPAddress -like '192.168.*') -and ($_.InterfaceAlias -notlike '*WSL*')} | Select-Object -First 1).IPAddress
Write-Host "[信息] Windows主机IP: $windowsIP" -ForegroundColor Green
Write-Host ""

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[错误] 请以管理员身份运行此脚本！" -ForegroundColor Red
    Write-Host "右键点击PowerShell -> 以管理员身份运行" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "[✓] 管理员权限检查通过" -ForegroundColor Green
Write-Host ""

# 删除旧的端口转发规则(如果存在)
Write-Host "[步骤1] 清理旧的端口转发规则..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=9000 listenaddress=0.0.0.0 2>$null
Write-Host "[✓] 清理完成" -ForegroundColor Green
Write-Host ""

# 添加端口转发规则
Write-Host "[步骤2] 添加端口转发规则..." -ForegroundColor Yellow

# HTTP服务 (8080端口)
Write-Host "  - 转发端口 8080 (HTTP Server)..." -NoNewline
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=$wslIP
if ($?) {
    Write-Host " ✓" -ForegroundColor Green
} else {
    Write-Host " ✗" -ForegroundColor Red
}

# WebSocket服务 (9000端口)
Write-Host "  - 转发端口 9000 (WebSocket Hub)..." -NoNewline
netsh interface portproxy add v4tov4 listenport=9000 listenaddress=0.0.0.0 connectport=9000 connectaddress=$wslIP
if ($?) {
    Write-Host " ✓" -ForegroundColor Green
} else {
    Write-Host " ✗" -ForegroundColor Red
}
Write-Host ""

# 添加防火墙规则
Write-Host "[步骤3] 配置Windows防火墙..." -ForegroundColor Yellow

# 删除旧规则(如果存在)
Remove-NetFirewallRule -DisplayName "WSL HTTP Server" -ErrorAction SilentlyContinue 2>$null
Remove-NetFirewallRule -DisplayName "WSL WebSocket Hub" -ErrorAction SilentlyContinue 2>$null

# HTTP服务防火墙规则
Write-Host "  - 允许端口 8080 (HTTP)..." -NoNewline
New-NetFirewallRule -DisplayName "WSL HTTP Server" `
    -Direction Inbound `
    -LocalPort 8080 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any `
    -ErrorAction SilentlyContinue | Out-Null
if ($?) {
    Write-Host " ✓" -ForegroundColor Green
} else {
    Write-Host " ✗" -ForegroundColor Red
}

# WebSocket服务防火墙规则
Write-Host "  - 允许端口 9000 (WebSocket)..." -NoNewline
New-NetFirewallRule -DisplayName "WSL WebSocket Hub" `
    -Direction Inbound `
    -LocalPort 9000 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any `
    -ErrorAction SilentlyContinue | Out-Null
if ($?) {
    Write-Host " ✓" -ForegroundColor Green
} else {
    Write-Host " ✗" -ForegroundColor Red
}
Write-Host ""

# 显示当前配置
Write-Host "[步骤4] 验证配置..." -ForegroundColor Yellow
Write-Host ""
Write-Host "当前端口转发规则:" -ForegroundColor Cyan
netsh interface portproxy show all
Write-Host ""

# 测试端口监听
Write-Host "[步骤5] 测试服务状态..." -ForegroundColor Yellow
$httpTest = Test-NetConnection -ComputerName localhost -Port 8080 -WarningAction SilentlyContinue
$wsTest = Test-NetConnection -ComputerName localhost -Port 9000 -WarningAction SilentlyContinue

if ($httpTest.TcpTestSucceeded) {
    Write-Host "  - HTTP服务 (8080): 运行中 ✓" -ForegroundColor Green
} else {
    Write-Host "  - HTTP服务 (8080): 未运行 ✗" -ForegroundColor Red
    Write-Host "    请在WSL中启动: python3 -m http.server 8080" -ForegroundColor Yellow
}

if ($wsTest.TcpTestSucceeded) {
    Write-Host "  - WebSocket服务 (9000): 运行中 ✓" -ForegroundColor Green
} else {
    Write-Host "  - WebSocket服务 (9000): 未运行 ✗" -ForegroundColor Red
    Write-Host "    请在WSL中启动: python3 websocket_hub.py" -ForegroundColor Yellow
}
Write-Host ""

# 显示访问信息
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "飞腾派访问地址:" -ForegroundColor Cyan
Write-Host "  控制面板: http://${windowsIP}:8080/control-panel/index.html" -ForegroundColor White
Write-Host "  节点视图: http://${windowsIP}:8080/node-view/index.html?node_id=SAT" -ForegroundColor White
Write-Host ""
Write-Host "测试命令(在飞腾派上执行):" -ForegroundColor Cyan
Write-Host "  ping $windowsIP" -ForegroundColor White
Write-Host "  curl http://${windowsIP}:8080/" -ForegroundColor White
Write-Host ""

# 提示如何清理
Write-Host "如需清理配置，运行以下命令:" -ForegroundColor Yellow
Write-Host "  netsh interface portproxy reset" -ForegroundColor Gray
Write-Host "  Remove-NetFirewallRule -DisplayName 'WSL HTTP Server'" -ForegroundColor Gray
Write-Host "  Remove-NetFirewallRule -DisplayName 'WSL WebSocket Hub'" -ForegroundColor Gray
Write-Host ""

pause
