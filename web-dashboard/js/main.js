// ==================== 全局变量 ====================
const API_BASE = 'http://localhost:8080/api';
let performanceChart = null;
let updateInterval = null;

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('PQ-Tor SAGIN Monitor initialized');

    // 初始化时钟
    updateTime();
    setInterval(updateTime, 1000);

    // 初始化图表
    initChart();

    // 加载初始数据
    loadData();

    // 设置定时更新（每5秒）
    updateInterval = setInterval(loadData, 5000);

    // 模拟电路建立动画
    simulateCircuitBuilding();

    // 添加日志
    addLog('info', 'System initialized');
    addLog('success', 'Connected to API server');
});

// ==================== 时间更新 ====================
function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('zh-CN', { hour12: false });
    document.getElementById('currentTime').textContent = timeString;
}

// ==================== 数据加载 ====================
async function loadData() {
    try {
        // 获取系统状态
        const statusResponse = await fetch(`${API_BASE}/status`);
        if (statusResponse.ok) {
            const status = await statusResponse.json();
            updateStatus(status);
        }

        // 获取性能数据
        const performanceResponse = await fetch(`${API_BASE}/performance`);
        if (performanceResponse.ok) {
            const performance = await performanceResponse.json();
            updatePerformanceMetrics(performance);
        }

        // 获取SAGIN对比数据
        const comparisonResponse = await fetch(`${API_BASE}/sagin/comparison`);
        if (comparisonResponse.ok) {
            const comparison = await comparisonResponse.json();
            updateChart(comparison);
        }

        // 更新实时指示器
        document.getElementById('liveIndicator').classList.add('live');

    } catch (error) {
        console.error('Failed to load data:', error);
        document.getElementById('liveIndicator').classList.remove('live');
        addLog('error', `API connection error: ${error.message}`);
    }
}

// ==================== 更新系统状态 ====================
function updateStatus(status) {
    // 更新节点状态
    const nodes = status.nodes || {};

    updateNodeStatus('directoryNode', nodes.directory);
    updateNodeStatus('clientNode', nodes.client);

    // 更新电路状态
    if (status.circuit) {
        const circuit = status.circuit;
        document.getElementById('circuitProgress').style.width =
            (circuit.status === 'established' ? 100 : 50) + '%';

        if (circuit.status === 'established') {
            addLog('success', `Circuit established with ${circuit.hops} hops`);
        }
    }
}

function updateNodeStatus(elementId, nodeInfo) {
    const element = document.getElementById(elementId);
    if (!element) return;

    if (nodeInfo && nodeInfo.status === 'running') {
        element.classList.add('active');
    } else {
        element.classList.remove('active');
    }
}

// ==================== 更新性能指标 ====================
function updatePerformanceMetrics(data) {
    // 更新握手时间
    if (data.handshake) {
        const avgUs = data.handshake.avg_us;
        document.getElementById('handshakeTime').textContent = `${avgUs.toFixed(1)}μs`;
    }

    // 更新电路延迟
    if (data.circuit_construction) {
        const avgMs = data.circuit_construction.avg_ms;
        document.getElementById('circuitLatency').textContent = `${avgMs.toFixed(0)}ms`;

        const successRate = (data.circuit_construction.success_rate * 100).toFixed(0);
        document.getElementById('successRate').textContent = `${successRate}%`;
    }

    // 更新网络类型
    if (data.current_config) {
        const config = data.current_config.toUpperCase();
        document.getElementById('networkType').textContent = config;
        addLog('info', `Current network: ${config}`);
    }
}

// ==================== 图表初始化和更新 ====================
function initChart() {
    const ctx = document.getElementById('performanceChart');
    if (!ctx) return;

    performanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Baseline', 'LEO', 'MEO', 'GEO'],
            datasets: [{
                label: 'Circuit Construction Time (s)',
                data: [0.15, 0.35, 0.75, 2.10],
                backgroundColor: [
                    'rgba(39, 174, 96, 0.7)',
                    'rgba(52, 152, 219, 0.7)',
                    'rgba(243, 156, 18, 0.7)',
                    'rgba(231, 76, 60, 0.7)'
                ],
                borderColor: [
                    'rgba(39, 174, 96, 1)',
                    'rgba(52, 152, 219, 1)',
                    'rgba(243, 156, 18, 1)',
                    'rgba(231, 76, 60, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#bdc3c7'
                    },
                    title: {
                        display: true,
                        text: 'Time (seconds)',
                        color: '#bdc3c7'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#bdc3c7'
                    }
                }
            }
        }
    });
}

function updateChart(comparison) {
    if (!performanceChart || !comparison) return;

    const data = [
        comparison.baseline?.latency || 0.15,
        comparison.leo?.latency || 0.35,
        comparison.meo?.latency || 0.75,
        comparison.geo?.latency || 2.10
    ];

    performanceChart.data.datasets[0].data = data;
    performanceChart.update();

    addLog('info', 'Performance data updated');
}

// ==================== 电路建立动画 ====================
function simulateCircuitBuilding() {
    const hops = ['client', 'guard', 'middle', 'exit'];
    let currentHop = 0;

    const interval = setInterval(() => {
        if (currentHop < hops.length) {
            const hopElement = document.querySelector(`[data-hop="${hops[currentHop]}"]`);
            if (hopElement) {
                // 移除之前的状态
                if (currentHop > 0) {
                    const prevHop = document.querySelector(`[data-hop="${hops[currentHop-1]}"]`);
                    if (prevHop) {
                        prevHop.classList.remove('building');
                        prevHop.classList.add('active');
                    }
                }

                // 当前hop设为building
                hopElement.classList.remove('pending');
                hopElement.classList.add('building');

                // 更新进度条
                const progress = ((currentHop + 1) / hops.length) * 100;
                document.getElementById('circuitProgress').style.width = progress + '%';

                addLog('info', `Building circuit: ${hops[currentHop]} hop`);
            }

            currentHop++;
        } else {
            // 完成
            const lastHop = document.querySelector(`[data-hop="${hops[hops.length-1]}"]`);
            if (lastHop) {
                lastHop.classList.remove('building');
                lastHop.classList.add('active');
            }
            addLog('success', 'Circuit established successfully!');
            clearInterval(interval);
        }
    }, 1500);
}

// ==================== 日志管理 ====================
function addLog(type, message) {
    const logsContent = document.getElementById('logsContent');
    if (!logsContent) return;

    const now = new Date();
    const timeString = now.toLocaleTimeString('zh-CN', { hour12: false });

    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `
        <span class="log-time">[${timeString}]</span>
        <span class="log-message">${message}</span>
    `;

    logsContent.appendChild(logEntry);

    // 限制日志条数（最多50条）
    while (logsContent.children.length > 50) {
        logsContent.removeChild(logsContent.firstChild);
    }

    // 滚动到底部
    logsContent.scrollTop = logsContent.scrollHeight;
}

function clearLogs() {
    const logsContent = document.getElementById('logsContent');
    if (logsContent) {
        logsContent.innerHTML = '';
        addLog('info', 'Logs cleared');
    }
}

// ==================== 全屏切换 ====================
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            addLog('error', `Fullscreen error: ${err.message}`);
        });
    } else {
        document.exitFullscreen();
    }
}

// ==================== 模拟数据（用于演示） ====================
function startDemoMode() {
    addLog('info', 'Demo mode started');

    // 模拟节点状态变化
    setInterval(() => {
        const configs = ['baseline', 'leo', 'meo', 'geo'];
        const randomConfig = configs[Math.floor(Math.random() * configs.length)];
        document.getElementById('networkType').textContent = randomConfig.toUpperCase();

        // 随机更新指标
        const handshake = (40 + Math.random() * 20).toFixed(1);
        document.getElementById('handshakeTime').textContent = `${handshake}μs`;

        const latency = (200 + Math.random() * 300).toFixed(0);
        document.getElementById('circuitLatency').textContent = `${latency}ms`;

        const success = (90 + Math.random() * 10).toFixed(0);
        document.getElementById('successRate').textContent = `${success}%`;

        addLog('info', `Network switched to ${randomConfig.toUpperCase()}`);
    }, 8000);
}

// ==================== 键盘快捷键 ====================
document.addEventListener('keydown', (e) => {
    if (e.key === 'F11') {
        e.preventDefault();
        toggleFullscreen();
    } else if (e.key === 'd' && e.ctrlKey) {
        e.preventDefault();
        startDemoMode();
    } else if (e.key === 'l' && e.ctrlKey) {
        e.preventDefault();
        clearLogs();
    }
});

// ==================== 工具函数 ====================
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatDuration(ms) {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}min`;
}

// ==================== 导出函数供HTML调用 ====================
window.toggleFullscreen = toggleFullscreen;
window.clearLogs = clearLogs;
window.startDemoMode = startDemoMode;

console.log('✓ PQ-Tor SAGIN Monitor loaded successfully');
console.log('Keyboard shortcuts:');
console.log('  F11       - Toggle fullscreen');
console.log('  Ctrl+D    - Start demo mode');
console.log('  Ctrl+L    - Clear logs');
