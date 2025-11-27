#!/usr/bin/env python3
"""
飞腾派SSH连接脚本 - 使用paramiko
用于自动连接192.168.5.110并检查12拓扑实验环境
"""

import paramiko
import sys
import time

# 配置
HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"
PORT = 22

def execute_command(ssh, command, description=""):
    """执行SSH命令并返回结果"""
    if description:
        print(f"\n{'='*70}")
        print(f"  {description}")
        print('='*70)

    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')

        if output:
            print(output)
        if error and exit_code != 0:
            print(f"❌ 错误: {error}")

        return exit_code == 0, output, error
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False, "", str(e)

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          飞腾派连接 - 12拓扑实验环境检查                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\n🔌 连接信息:")
    print(f"   主机: {HOST}")
    print(f"   用户: {USER}")
    print(f"   端口: {PORT}")

    # 创建SSH客户端
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 连接
        print(f"\n🔄 正在连接到 {HOST}...")
        ssh.connect(
            hostname=HOST,
            port=PORT,
            username=USER,
            password=PASSWORD,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        print("✅ SSH连接成功！\n")

        # 检查项目列表
        checks = []

        # 1. 系统信息
        success, output, _ = execute_command(
            ssh,
            "uname -a && echo && cat /etc/os-release | grep PRETTY_NAME",
            "1️⃣ 系统信息"
        )
        checks.append(("系统连接", success))

        # 2. 架构确认
        success, output, _ = execute_command(
            ssh,
            "uname -m && echo && lscpu | grep 'Architecture\\|Model name' | head -2",
            "2️⃣ CPU架构"
        )
        is_arm = "aarch64" in output or "arm64" in output
        checks.append(("ARM64架构", is_arm))

        # 3. liboqs检查
        success, output, _ = execute_command(
            ssh,
            "ls -lh ~/oqs/lib/liboqs.so* 2>/dev/null || ls -lh ~/_oqs/lib/liboqs.so* 2>/dev/null || echo '❌ liboqs未找到'",
            "3️⃣ liboqs库检查"
        )
        liboqs_found = "liboqs.so" in output
        checks.append(("liboqs安装", liboqs_found))

        if liboqs_found:
            # 检查liboqs版本
            execute_command(
                ssh,
                "cat ~/oqs/include/oqs/oqsconfig.h 2>/dev/null | grep OQS_VERSION_TEXT || cat ~/_oqs/include/oqs/oqsconfig.h 2>/dev/null | grep OQS_VERSION_TEXT || echo '版本未知'",
                "   liboqs版本信息"
            )

        # 4. GCC和编译工具
        success, output, _ = execute_command(
            ssh,
            "gcc --version | head -1 && make --version | head -1",
            "4️⃣ 编译工具"
        )
        checks.append(("GCC/Make", success))

        # 5. 项目目录检查
        success, output, _ = execute_command(
            ssh,
            "ls -ld ~/pq-ntor-experiment 2>/dev/null && echo '✅ 项目目录存在' || echo '❌ 项目目录不存在'",
            "5️⃣ 项目目录"
        )
        project_exists = "pq-ntor-experiment" in output and "✅" in output
        checks.append(("项目目录", project_exists))

        # 6. C代码编译状态
        if project_exists:
            success, output, _ = execute_command(
                ssh,
                "cd ~/pq-ntor-experiment/c && ls -lh directory relay client 2>/dev/null || echo '❌ 程序未编译'",
                "6️⃣ C程序编译状态"
            )
            compiled = "directory" in output and "relay" in output and "client" in output
            checks.append(("C程序编译", compiled))
        else:
            checks.append(("C程序编译", False))
            compiled = False

        # 7. 测试程序
        if project_exists and compiled:
            success, output, _ = execute_command(
                ssh,
                "cd ~/pq-ntor-experiment/c && ls -1 test_* benchmark_* 2>/dev/null | head -10",
                "7️⃣ 测试和Benchmark程序"
            )
            tests_exist = "test_" in output
            checks.append(("测试程序", tests_exist))
        else:
            checks.append(("测试程序", False))

        # 8. 12拓扑脚本
        success, output, _ = execute_command(
            ssh,
            "find ~/pq-ntor-experiment/sagin-experiments -name '*12topo*.py' -o -name 'run_pq_ntor*.py' 2>/dev/null | head -5",
            "8️⃣ 12拓扑测试脚本"
        )
        script_exists = ".py" in output
        checks.append(("12拓扑脚本", script_exists))

        # 9. NOMA拓扑配置
        success, output, _ = execute_command(
            ssh,
            "ls ~/pq-ntor-experiment/sagin-experiments/noma-topologies/configs/topology_*.json 2>/dev/null | wc -l",
            "9️⃣ NOMA拓扑配置文件"
        )
        try:
            config_count = int(output.strip())
            checks.append(("拓扑配置", config_count >= 12))
            if config_count > 0:
                print(f"   ✅ 找到 {config_count} 个拓扑配置文件")
        except:
            checks.append(("拓扑配置", False))

        # 10. Python环境
        success, output, _ = execute_command(
            ssh,
            "python3 --version && which python3",
            "🔟 Python环境"
        )
        checks.append(("Python3", success))

        # 11. sudo权限（网络模拟需要tc命令）
        success, output, _ = execute_command(
            ssh,
            "sudo -n tc qdisc show 2>/dev/null | head -3 && echo '✅ 有sudo免密权限' || echo '⚠️ 需要sudo密码'",
            "1️⃣1️⃣ sudo权限（网络模拟需要）"
        )
        has_sudo = "✅" in output or "qdisc" in output
        checks.append(("sudo权限", has_sudo))

        # 12. 磁盘空间
        success, output, _ = execute_command(
            ssh,
            "df -h ~ | tail -1",
            "1️⃣2️⃣ 磁盘空间"
        )

        # 13. 环境变量检查
        success, output, _ = execute_command(
            ssh,
            "echo $LD_LIBRARY_PATH | grep -q oqs && echo '✅ LD_LIBRARY_PATH已配置' || echo '⚠️ LD_LIBRARY_PATH未配置'",
            "1️⃣3️⃣ 环境变量"
        )

        # 汇总结果
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

        if not liboqs_found:
            print("\n❌ liboqs未安装，需要先安装:")
            print("  在飞腾派上执行:")
            print("  cd ~/pq-ntor-experiment")
            print("  ./setup_phytium.sh")
        elif not project_exists or not compiled:
            print("\n❌ 项目未部署或未编译")
            print("  需要从WSL部署代码到飞腾派:")
            print("  cd /home/ccc/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/scripts")
            print("  ./deploy_to_phytium.sh")
        elif passed >= total - 2:  # 允许2个非关键检查失败
            print("\n✅ 环境基本就绪！")
            print("\n可以开始12拓扑实验:")
            print("  方式1: 通过SSH手动运行")
            print("    ssh user@192.168.5.110")
            print("    cd ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/scripts")
            print("    python3 run_pq_ntor_12topologies.py --mode pq --runs 10")
            print("\n  方式2: 通过本脚本远程执行（添加--run参数）")
        else:
            print("\n⚠️ 部分检查未通过，请根据上述结果修复问题")

        print("\n")

        # 如果参数包含--run，执行12拓扑实验
        if len(sys.argv) > 1 and sys.argv[1] == '--run':
            print("="*70)
            print("  🚀 准备运行12拓扑实验")
            print("="*70)
            execute_command(
                ssh,
                "cd ~/pq-ntor-experiment/sagin-experiments/pq-ntor-12topo-experiment/scripts && python3 run_pq_ntor_12topologies.py --mode pq --runs 10",
                "执行12拓扑实验"
            )

        return 0 if passed >= total - 2 else 1

    except paramiko.AuthenticationException:
        print(f"❌ 认证失败：用户名或密码错误")
        return 1
    except paramiko.SSHException as e:
        print(f"❌ SSH连接失败: {e}")
        return 1
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return 1
    finally:
        ssh.close()
        print("🔌 SSH连接已关闭\n")

if __name__ == "__main__":
    sys.exit(main())
