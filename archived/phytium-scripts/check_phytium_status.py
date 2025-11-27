#!/usr/bin/env python3
"""
飞腾派状态检查脚本
用于检查192.168.5.110上的环境和12拓扑实验准备情况
"""

import subprocess
import sys
import json
from pathlib import Path

# 配置
PHYTIUM_IP = "192.168.5.110"
PHYTIUM_USER = "user"
REMOTE_DIR = "/home/user/pq-ntor-experiment"

def run_ssh_command(command, description=""):
    """执行SSH命令"""
    ssh_cmd = f'ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no {PHYTIUM_USER}@{PHYTIUM_IP} "{command}"'

    if description:
        print(f"\n{'='*70}")
        print(f"  {description}")
        print('='*70)

    try:
        result = subprocess.run(
            ssh_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(result.stdout)
            return True, result.stdout
        else:
            print(f"❌ 错误: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print("❌ 命令超时")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False, str(e)

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          飞腾派状态检查 - 12拓扑实验准备                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\n目标设备: {PHYTIUM_IP}")
    print(f"用户名: {PHYTIUM_USER}")
    print(f"项目路径: {REMOTE_DIR}")

    checks = []

    # 1. 基本连接测试
    success, _ = run_ssh_command(
        "echo 'SSH连接成功' && uname -a",
        "1️⃣ 基本连接和系统信息"
    )
    checks.append(("SSH连接", success))

    if not success:
        print("\n❌ 无法连接到飞腾派，请检查:")
        print("  1. 飞腾派是否开机")
        print("  2. IP地址是否正确 (192.168.5.110)")
        print("  3. SSH密钥是否已配置")
        print("\n💡 配置SSH密钥:")
        print(f"  ssh-copy-id {PHYTIUM_USER}@{PHYTIUM_IP}")
        sys.exit(1)

    # 2. 检查liboqs安装
    success, output = run_ssh_command(
        "ls -lh ~/oqs/lib/liboqs.so* 2>/dev/null || ls -lh ~/_oqs/lib/liboqs.so* 2>/dev/null || echo '未找到liboqs'",
        "2️⃣ liboqs安装检查"
    )
    liboqs_found = "liboqs.so" in output
    checks.append(("liboqs安装", liboqs_found))

    # 3. 检查项目目录
    success, output = run_ssh_command(
        f"ls -ld {REMOTE_DIR} 2>/dev/null || echo '项目目录不存在'",
        "3️⃣ 项目目录检查"
    )
    project_exists = "pq-ntor-experiment" in output
    checks.append(("项目目录", project_exists))

    # 4. 检查C代码是否已编译
    success, output = run_ssh_command(
        f"cd {REMOTE_DIR}/c && ls -lh directory relay client 2>/dev/null || echo '程序未编译'",
        "4️⃣ C程序编译状态"
    )
    compiled = "directory" in output and "relay" in output
    checks.append(("C程序编译", compiled))

    # 5. 检查测试程序
    success, output = run_ssh_command(
        f"cd {REMOTE_DIR}/c && ls test_* benchmark_* 2>/dev/null | head -10",
        "5️⃣ 测试和Benchmark程序"
    )
    tests_exist = "test_" in output or "benchmark_" in output
    checks.append(("测试程序", tests_exist))

    # 6. 检查12拓扑脚本
    success, output = run_ssh_command(
        f"ls {REMOTE_DIR}/sagin-experiments/pq-ntor-12topo-experiment/scripts/*.py 2>/dev/null || echo '脚本未找到'",
        "6️⃣ 12拓扑测试脚本"
    )
    script_exists = ".py" in output
    checks.append(("12拓扑脚本", script_exists))

    # 7. 检查拓扑配置文件
    success, output = run_ssh_command(
        f"ls {REMOTE_DIR}/sagin-experiments/noma-topologies/configs/topology_*.json 2>/dev/null | wc -l",
        "7️⃣ NOMA拓扑配置文件"
    )
    try:
        config_count = int(output.strip())
        checks.append(("拓扑配置", config_count >= 12))
        print(f"✅ 找到 {config_count} 个拓扑配置文件")
    except:
        checks.append(("拓扑配置", False))

    # 8. 检查Python环境
    success, output = run_ssh_command(
        "python3 --version && which python3",
        "8️⃣ Python环境"
    )
    checks.append(("Python3", success))

    # 9. 检查系统权限（sudo）
    success, output = run_ssh_command(
        "sudo -n tc qdisc show 2>/dev/null && echo '有sudo权限' || echo '需要sudo密码'",
        "9️⃣ sudo权限检查（网络模拟需要）"
    )
    has_sudo = "有sudo权限" in output or "qdisc" in output
    checks.append(("sudo权限", has_sudo))

    # 10. 磁盘空间检查
    success, output = run_ssh_command(
        "df -h ~",
        "🔟 磁盘空间"
    )

    # 总结
    print("\n" + "="*70)
    print("  📊 检查结果汇总")
    print("="*70)

    passed = 0
    total = len(checks)

    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"  {status} {check_name}")
        if check_result:
            passed += 1

    print("\n" + "="*70)
    print(f"  通过: {passed}/{total}")
    print("="*70)

    # 建议下一步
    print("\n" + "="*70)
    print("  🚀 下一步建议")
    print("="*70)

    if passed == total:
        print("\n✅ 环境已就绪！可以开始12拓扑实验")
        print("\n运行实验:")
        print(f"  ssh {PHYTIUM_USER}@{PHYTIUM_IP}")
        print(f"  cd {REMOTE_DIR}/sagin-experiments/pq-ntor-12topo-experiment/scripts")
        print(f"  python3 run_pq_ntor_12topologies.py --mode pq --runs 10")
    elif not liboqs_found:
        print("\n❌ 需要先安装liboqs")
        print(f"  ssh {PHYTIUM_USER}@{PHYTIUM_IP}")
        print(f"  cd {REMOTE_DIR}")
        print(f"  ./setup_phytium.sh")
    elif not project_exists or not compiled:
        print("\n❌ 需要部署和编译项目")
        print("  在本地运行:")
        print(f"  cd {Path.cwd()}/sagin-experiments/pq-ntor-12topo-experiment/scripts")
        print(f"  ./deploy_to_phytium.sh")
    else:
        print("\n⚠️ 部分检查未通过，请根据上述结果修复问题")

    print("\n")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
