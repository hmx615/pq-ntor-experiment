# PowerShell脚本 - 在Windows 11中运行
# 下载Globe.GL和Three.js库

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SAGIN NOMA 3D可视化 - 资源下载脚本" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 设置下载目录（当前目录）
$downloadDir = Get-Location

Write-Host "[1/2] 下载Three.js..." -ForegroundColor Yellow
$threeUrl = "https://cdn.jsdelivr.net/npm/three@0.154.0/build/three.min.js"
$threePath = Join-Path $downloadDir "three.min.js"

try {
    Invoke-WebRequest -Uri $threeUrl -OutFile $threePath
    $threeSize = (Get-Item $threePath).Length
    Write-Host "  ✓ Three.js 下载成功 ($threeSize bytes)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Three.js 下载失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "[2/2] 下载Globe.GL..." -ForegroundColor Yellow
$globeUrl = "https://cdn.jsdelivr.net/npm/globe.gl@2.31.0/dist/globe.gl.min.js"
$globePath = Join-Path $downloadDir "globe.gl.min.js"

try {
    Invoke-WebRequest -Uri $globeUrl -OutFile $globePath
    $globeSize = (Get-Item $globePath).Length
    Write-Host "  ✓ Globe.GL 下载成功 ($globeSize bytes)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Globe.GL 下载失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  下载完成！" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "文件已保存到: $downloadDir" -ForegroundColor White
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 检查当前目录是否有这两个文件：" -ForegroundColor White
Write-Host "   - three.min.js" -ForegroundColor Cyan
Write-Host "   - globe.gl.min.js" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. 这些文件已经在WSL可访问的位置，可以直接使用！" -ForegroundColor Green
Write-Host ""

# 列出文件
Write-Host "当前目录文件列表：" -ForegroundColor Yellow
Get-ChildItem -Filter "*.js" | Format-Table Name, Length, LastWriteTime
