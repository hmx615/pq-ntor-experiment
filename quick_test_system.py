#!/usr/bin/env python3
"""
快速系统测试 - 不重新部署，只测试现有系统
"""
import paramiko
import sys
import time

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"
PORT = 22

def execute_command(ssh, command, description="", show_output=True, timeout=60):
    """执行SSH命令并返回结果"""
    if description:
        print(f"\n{'='*70}")
        print(f"  {description}")
        print('='*70)

    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')

        if show_output:
            if output:
                print(output)
            if error and exit_code != 0:
                print(f"错误: {error}")

        return exit_code == 0, output, error
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False, "", str(e)

def main():
    print("="*70)
    print("  快速系统测试 - 使用现有代码")
    print("="*70)
    print(f"\n🔌 连接到 {HOST}...\n")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
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

        # 检查现有文件
        execute_command(
            ssh,
            """
            echo "检查已编译的二进制文件:"
            ls -lh ~/pq-ntor-experiment/c/benchmark_pq_ntor 2>&1 || echo "  ❌ benchmark_pq_ntor 不存在"
            ls -lh ~/pq-ntor-experiment/c/directory 2>&1 || echo "  ❌ directory 不存在"
            ls -lh ~/pq-ntor-experiment/c/relay 2>&1 || echo "  ❌ relay 不存在"
            ls -lh ~/pq-ntor-experiment/last_experiment/phytium_deployment/benchmark_3hop_circuit 2>&1 || echo "  ❌ benchmark_3hop_circuit 不存在"
            """,
            "第1步：检查现有文件"
        )

        # 清理旧进程
        execute_command(
            ssh,
            """
            pkill -f directory 2>/dev/null || true
            pkill -f relay 2>/dev/null || true
            sleep 1
            pgrep -f "directory|relay" && echo "⚠️ 部分进程未停止" || echo "✓ 所有旧进程已清理"
            """,
            "第2步：清理旧进程"
        )

        # 启动系统组件
        execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/c

            # 启动目录服务器
            echo "启动目录服务器..."
            nohup ./directory 5000 > ~/directory.log 2>&1 &
            sleep 2

            # 启动3个中继
            echo "启动中继节点..."
            nohup ./relay 6000 guard localhost:5000 > ~/guard.log 2>&1 &
            nohup ./relay 6001 middle localhost:5000 > ~/middle.log 2>&1 &
            nohup ./relay 6002 exit localhost:5000 > ~/exit.log 2>&1 &
            sleep 2

            # 检查进程
            echo ""
            echo "运行中的进程:"
            pgrep -a directory
            pgrep -a relay
            """,
            "第3步：启动系统组件"
        )

        # 等待服务完全启动
        print("\n等待服务完全启动...")
        time.sleep(5)

        # 运行三跳电路测试
        execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/last_experiment/phytium_deployment
            echo "运行三跳电路测试（5次迭代）..."
            ./benchmark_3hop_circuit 5 localhost 5000 2>&1 | tee /tmp/3hop_test.log
            """,
            "第4步：运行三跳电路测试",
            timeout=120
        )

        # 清理进程
        execute_command(
            ssh,
            """
            pkill -f directory
            pkill -f relay
            sleep 1
            pgrep -f "directory|relay" && echo "⚠️ 部分进程未停止" || echo "✓ 所有测试进程已停止"
            """,
            "第5步：清理测试进程"
        )

        # 显示测试结果
        print("\n" + "="*70)
        print("  ✅ 测试完成")
        print("="*70)
        print("\n查看详细结果:")
        print(f"  ssh {USER}@{HOST} 'cat /tmp/3hop_test.log'")
        print("")

        return 0

    except paramiko.AuthenticationException:
        print(f"❌ 认证失败：用户名或密码错误")
        return 1
    except paramiko.SSHException as e:
        print(f"❌ SSH连接失败: {e}")
        return 1
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        ssh.close()
        print("🔌 SSH连接已关闭\n")

if __name__ == "__main__":
    sys.exit(main())
