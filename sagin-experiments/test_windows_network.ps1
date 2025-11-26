# Windows网络诊断脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Windows网络诊断 - 飞腾派连接测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 显示本机IP地址
Write-Host "[1] 本机IP地址:" -ForegroundColor Yellow
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like '192.168.*'} | Select-Object IPAddress, InterfaceAlias, PrefixLength | Format-Table
Write-Host ""

# 2. 测试到飞腾派的连接
Write-Host "[2] 测试到飞腾派的连接 (192.168.5.110):" -ForegroundColor Yellow
$pingResult = Test-Connection -ComputerName 192.168.5.110 -Count 3 -ErrorAction SilentlyContinue
if ($pingResult) {
    Write-Host "  ✓ Ping成功！" -ForegroundColor Green
    $pingResult | Select-Object Address, ResponseTime | Format-Table
} else {
    Write-Host "  ✗ Ping失败！" -ForegroundColor Red
}
Write-Host ""

# 3. 检查防火墙状态
Write-Host "[3] 检查Windows防火墙状态:" -ForegroundColor Yellow
$firewallProfiles = Get-NetFirewallProfile
foreach ($profile in $firewallProfiles) {
    Write-Host "  $($profile.Name): $($profile.Enabled)" -ForegroundColor $(if ($profile.Enabled) { "Yellow" } else { "Green" })
}
Write-Host ""

# 4. 检查ICMP规则
Write-Host "[4] 检查ICMP防火墙规则:" -ForegroundColor Yellow
$icmpRules = Get-NetFirewallRule | Where-Object {$_.DisplayName -like '*ICMP*' -or $_.DisplayName -like '*Echo*'} | Select-Object DisplayName, Enabled, Direction, Action -First 5
if ($icmpRules) {
    $icmpRules | Format-Table
} else {
    Write-Host "  ! 未找到ICMP规则" -ForegroundColor Yellow
}
Write-Host ""

# 5. 检查WSL相关规则
Write-Host "[5] 检查WSL防火墙规则:" -ForegroundColor Yellow
$wslRules = Get-NetFirewallRule | Where-Object {$_.DisplayName -like '*WSL*'} | Select-Object DisplayName, Enabled, Direction, Action
if ($wslRules) {
    $wslRules | Format-Table
} else {
    Write-Host "  ! 未找到WSL相关规则" -ForegroundColor Yellow
}
Write-Host ""

# 6. 测试端口
Write-Host "[6] 测试本机端口监听状态:" -ForegroundColor Yellow
$ports = @(8080, 9000)
foreach ($port in $ports) {
    $result = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
    if ($result.TcpTestSucceeded) {
        Write-Host "  ✓ 端口 $port : 监听中" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 端口 $port : 未监听" -ForegroundColor Red
    }
}
Write-Host ""

# 7. 路由表
Write-Host "[7] 路由表 (192.168网段):" -ForegroundColor Yellow
Get-NetRoute -AddressFamily IPv4 | Where-Object {$_.DestinationPrefix -like '192.168.*'} | Select-Object DestinationPrefix, NextHop, InterfaceAlias | Format-Table
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "诊断建议:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 生成建议
Write-Host ""
Write-Host "如果Ping失败，请执行以下操作:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  允许ICMP回显请求 (Ping):" -ForegroundColor White
Write-Host '   New-NetFirewallRule -DisplayName "Allow ICMPv4 In" -Direction Inbound -Protocol ICMPv4 -IcmpType 8 -Action Allow' -ForegroundColor Gray
Write-Host ""
Write-Host "2️⃣  暂时关闭防火墙测试 (不推荐用于生产):" -ForegroundColor White
Write-Host '   Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False' -ForegroundColor Gray
Write-Host ""
Write-Host "3️⃣  检查网络是否在同一个局域网:" -ForegroundColor White
Write-Host "   - Windows IP: 192.168.5.144" -ForegroundColor Gray
Write-Host "   - 飞腾派 IP: 192.168.5.110" -ForegroundColor Gray
Write-Host "   - 子网掩码应相同 (通常是 255.255.255.0)" -ForegroundColor Gray
Write-Host ""

pause
