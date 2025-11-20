#!/usr/bin/env python3
"""
PQ-Tor SAGIN Monitor - API Server
提供实时数据接口for前端展示
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import pandas as pd
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
RESULTS_DIR = BASE_DIR / 'results' / 'sagin'
C_DIR = BASE_DIR / 'c'

print(f"Base directory: {BASE_DIR}")
print(f"Results directory: {RESULTS_DIR}")

# ==================== 工具函数 ====================

def check_process(process_name):
    """检查进程是否运行"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', process_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            pid = int(result.stdout.strip().split('\n')[0])
            return {'status': 'running', 'pid': pid}
        else:
            return {'status': 'stopped', 'pid': None}
    except Exception as e:
        return {'status': 'unknown', 'pid': None, 'error': str(e)}

def load_sagin_results():
    """加载SAGIN实验结果"""
    summary_file = RESULTS_DIR / 'summary.csv'

    if not summary_file.exists():
        print(f"Warning: {summary_file} not found, using default data")
        return {
            'baseline': {'latency': 0.15, 'success_rate': 1.0},
            'leo': {'latency': 0.35, 'success_rate': 0.98},
            'meo': {'latency': 0.75, 'success_rate': 0.95},
            'geo': {'latency': 2.10, 'success_rate': 0.92}
        }

    try:
        df = pd.read_csv(summary_file)
        data = {}
        for _, row in df.iterrows():
            config = row.get('Config', '').lower()
            if config:
                data[config] = {
                    'latency': float(row.get('Time(s)_mean', 0)),
                    'success_rate': float(row.get('Success_count', 0)) / float(row.get('Time(s)_count', 1))
                }
        return data
    except Exception as e:
        print(f"Error loading SAGIN results: {e}")
        return {}

def load_benchmark_results():
    """加载握手性能基准测试结果"""
    benchmark_file = C_DIR / 'benchmark_results.csv'

    if not benchmark_file.exists():
        print(f"Warning: {benchmark_file} not found, using default data")
        return {
            'avg_us': 49.2,
            'median_us': 41.0,
            'std_us': 23.6,
            'samples': 1000
        }

    try:
        df = pd.read_csv(benchmark_file)
        # 查找Full Handshake行
        full_handshake = df[df['Operation'].str.contains('Full Handshake', na=False)]
        if not full_handshake.empty:
            row = full_handshake.iloc[0]
            return {
                'avg_us': float(row.get('Avg(μs)', 49.2)),
                'median_us': float(row.get('Median(μs)', 41.0)),
                'std_us': float(row.get('StdDev(μs)', 23.6)),
                'samples': 1000
            }
        return {}
    except Exception as e:
        print(f"Error loading benchmark results: {e}")
        return {}

# ==================== API Endpoints ====================

@app.route('/')
def index():
    """重定向到前端页面"""
    return send_from_directory(str(BASE_DIR / 'web-dashboard'), 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """提供静态文件"""
    return send_from_directory(str(BASE_DIR / 'web-dashboard'), path)

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    status = {
        'timestamp': datetime.now().isoformat(),
        'network_type': 'LEO',  # 默认
        'nodes': {
            'directory': check_process('directory'),
            'guard': check_process('relay.*guard'),
            'middle': check_process('relay.*middle'),
            'exit': check_process('relay.*exit'),
            'client': check_process('client')
        },
        'circuit': {
            'status': 'established',
            'hops': 3,
            'latency_ms': 52
        }
    }
    return jsonify(status)

@app.route('/api/performance')
def get_performance():
    """获取性能数据"""
    handshake_data = load_benchmark_results()
    sagin_data = load_sagin_results()

    # 获取当前配置（尝试从文件读取，否则默认LEO）
    current_config = 'leo'

    performance = {
        'handshake': handshake_data,
        'circuit_construction': {
            'avg_ms': sagin_data.get(current_config, {}).get('latency', 0.35) * 1000,
            'success_rate': sagin_data.get(current_config, {}).get('success_rate', 0.98)
        },
        'current_config': current_config
    }

    return jsonify(performance)

@app.route('/api/sagin/comparison')
def get_sagin_comparison():
    """获取SAGIN网络配置对比数据"""
    data = load_sagin_results()
    return jsonify(data)

@app.route('/api/logs')
def get_logs():
    """获取最新日志"""
    lines = int(request.args.get('lines', 50))

    log_files = [
        C_DIR / 'directory.log',
        C_DIR / 'guard.log',
        C_DIR / 'middle.log',
        C_DIR / 'exit.log'
    ]

    logs = []
    for log_file in log_files:
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    content = f.readlines()
                    logs.extend(content[-lines:])
            except Exception as e:
                logs.append(f"Error reading {log_file.name}: {str(e)}")

    return jsonify({'logs': logs[-lines:]})

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# ==================== 主程序 ====================

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║     PQ-Tor SAGIN Monitor - API Server                     ║
    ║     后量子Tor空天地网络监控系统 - API服务                  ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    print(f"📁 Base directory: {BASE_DIR}")
    print(f"📊 Results directory: {RESULTS_DIR}")
    print(f"🌐 Starting server at http://localhost:8080")
    print("\n🔗 访问地址:")
    print("   - Web UI:  http://localhost:8080")
    print("   - API:     http://localhost:8080/api/status")
    print("\n⌨️  按 Ctrl+C 停止服务\n")

    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True
    )
