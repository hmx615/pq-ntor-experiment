# Windows防火墙快速修复脚本 - 允许飞腾派访问
# 必须以管理员身份运行

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Windows防火墙快速修复" -ForegroundColor Cyan
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

# 1. 允许ICMP (Ping)
Write-Host "[步骤1] 允许ICMP回显请求 (Ping)..." -ForegroundColor Yellow

# 删除旧规则
Remove-NetFirewallRule -DisplayName "Allow ICMPv4 Inbound" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "Allow ICMPv4 Outbound" -ErrorAction SilentlyContinue

# 添加新规则
try {
    New-NetFirewallRule -DisplayName "Allow ICMPv4 Inbound" `
        -Direction Inbound `
        -Protocol ICMPv4 `
        -IcmpType 8 `
        -Action Allow `
        -Profile Any `
        -ErrorAction Stop | Out-Null
    Write-Host "  ✓ ICMP入站规则已添加" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 添加ICMP规则失败: $_" -ForegroundColor Red
}

try {
    New-NetFirewallRule -DisplayName "Allow ICMPv4 Outbound" `
        -Direction Outbound `
        -Protocol ICMPv4 `
        -Action Allow `
        -Profile Any `
        -ErrorAction Stop | Out-Null
    Write-Host "  ✓ ICMP出站规则已添加" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 添加ICMP规则失败: $_" -ForegroundColor Red
}
Write-Host ""

# 2. 确保WSL端口转发规则存在
Write-Host "[步骤2] 确认端口转发规则..." -ForegroundColor Yellow

# 获取WSL IP
$wslIP = "192.168.74.81"
Write-Host "  WSL IP: $wslIP" -ForegroundColor Gray

# 删除旧规则
netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=9000 listenaddress=0.0.0.0 2>$null

# 添加新规则
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=$wslIP
netsh interface portproxy add v4tov4 listenport=9000 listenaddress=0.0.0.0 connectport=9000 connectaddress=$wslIP

Write-Host "  ✓ 端口转发规则已更新" -ForegroundColor Green
Write-Host ""

# 3. 确保防火墙规则存在
Write-Host "[步骤3] 确认防火墙端口规则..." -ForegroundColor Yellow

# 删除旧规则
Remove-NetFirewallRule -DisplayName "WSL HTTP Server" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "WSL WebSocket Hub" -ErrorAction SilentlyContinue

# HTTP (8080)
try {
    New-NetFirewallRule -DisplayName "WSL HTTP Server" `
        -Direction Inbound `
        -LocalPort 8080 `
        -Protocol TCP `
        -Action Allow `
        -Profile Any `
        -ErrorAction Stop | Out-Null
    Write-Host "  ✓ HTTP端口(8080)规则已添加" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 添加HTTP规则失败: $_" -ForegroundColor Red
}

# WebSocket (9000)
try {
    New-NetFirewallRule -DisplayName "WSL WebSocket Hub" `
        -Direction Inbound `
        -LocalPort 9000 `
        -Protocol TCP `
        -Action Allow `
        -Profile Any `
        -ErrorAction Stop | Out-Null
    Write-Host "  ✓ WebSocket端口(9000)规则已添加" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 添加WebSocket规则失败: $_" -ForegroundColor Red
}
Write-Host ""

# 4. 显示网络配置
Write-Host "[步骤4] 当前网络配置:" -ForegroundColor Yellow
Write-Host ""

# Windows IP地址
$windowsIPs = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like '192.168.*'}
Write-Host "  Windows IP地址:" -ForegroundColor Cyan
foreach ($ip in $windowsIPs) {
    Write-Host "    - $($ip.IPAddress) ($($ip.InterfaceAlias))" -ForegroundColor White
}
Write-Host ""

# 端口转发配置
Write-Host "  端口转发规则:" -ForegroundColor Cyan
netsh interface portproxy show all
Write-Host ""

# 5. 测试连接
Write-Host "[步骤5] 测试网络连通性..." -ForegroundColor Yellow
Write-Host ""

# 测试到飞腾派
Write-Host "  测试到飞腾派 (192.168.5.110):" -ForegroundColor Cyan
$pingTest = Test-Connection -ComputerName 192.168.5.110 -Count 2 -ErrorAction SilentlyContinue
if ($pingTest) {
    Write-Host "    ✓ Ping成功！延迟: $($pingTest[0].ResponseTime)ms" -ForegroundColor Green
} else {
    Write-Host "    ✗ Ping失败！" -ForegroundColor Red
    Write-Host "    可能原因: 网络隔离、路由器配置、飞腾派防火墙" -ForegroundColor Yellow
}
Write-Host ""

# 测试本地端口
Write-Host "  测试本地服务端口:" -ForegroundColor Cyan
$ports = @(8080, 9000)
foreach ($port in $ports) {
    $portTest = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($portTest.TcpTestSucceeded) {
        Write-Host "    ✓ 端口 $port : 监听中" -ForegroundColor Green
    } else {
        Write-Host "    ✗ 端口 $port : 未监听" -ForegroundColor Red
        Write-Host "      请在WSL中启动服务" -ForegroundColor Yellow
    }
}
Write-Host ""

# 6. 总结和建议
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  在飞腾派上测试Ping:" -ForegroundColor White
Write-Host "   ping 192.168.5.144" -ForegroundColor Gray
Write-Host ""
Write-Host "2️⃣  如果Ping仍然失败:" -ForegroundColor White
Write-Host "   方案A: 暂时完全关闭Windows防火墙测试" -ForegroundColor Gray
Write-Host "   Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False" -ForegroundColor Gray
Write-Host ""
Write-Host "   方案B: 检查路由器是否启用了AP隔离" -ForegroundColor Gray
Write-Host "   (路由器管理界面 -> 无线设置 -> AP隔离 -> 关闭)" -ForegroundColor Gray
Write-Host ""
Write-Host "3️⃣  如果Ping成功，在飞腾派浏览器访问:" -ForegroundColor White
Write-Host "   http://192.168.5.144:8080/node-view/index.html?node_id=SAT" -ForegroundColor Gray
Write-Host ""

Write-Host "飞腾派URL列表:" -ForegroundColor Cyan
Write-Host "  SAT:  http://192.168.5.144:8080/node-view/index.html?node_id=SAT" -ForegroundColor White
Write-Host "  SR:   http://192.168.5.144:8080/node-view/index.html?node_id=SR" -ForegroundColor White
Write-Host "  S1R2: http://192.168.5.144:8080/node-view/index.html?node_id=S1R2" -ForegroundColor White
Write-Host "  S1:   http://192.168.5.144:8080/node-view/index.html?node_id=S1" -ForegroundColor White
Write-Host "  S2:   http://192.168.5.144:8080/node-view/index.html?node_id=S2" -ForegroundColor White
Write-Host "  T:    http://192.168.5.144:8080/node-view/index.html?node_id=T" -ForegroundColor White
Write-Host ""

pause
