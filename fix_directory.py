#!/usr/bin/env python3
"""
修复directory编译问题 - 添加test_server.o
"""
import paramiko
import sys

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"
PORT = 22

def execute_command(ssh, command, description="", timeout=120):
    """执行SSH命令"""
    if description:
        print(f"\n{'='*70}")
        print(f"  {description}")
        print('='*70)

    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout, get_pty=True)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        print(output)
        return exit_code == 0, output
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False, ""

def main():
    print("="*70)
    print("  修复directory编译")
    print("="*70)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname=HOST, port=PORT, username=USER, password=PASSWORD,
                   timeout=10, allow_agent=False, look_for_keys=False)
        print("✅ SSH连接成功！\n")

        # 编译test_server.o和directory
        execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/c

            echo "编译test_server.o..."
            gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc \\
                -c src/test_server.c -o src/test_server.o

            echo ""
            echo "编译directory（带test_server依赖）..."
            gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc \\
                -o directory \\
                programs/directory_main.c \\
                src/directory_server.o src/test_server.o src/kyber_kem.o src/crypto_utils.o src/pq_ntor.o src/cell.o \\
                -L/home/user/_oqs/lib -loqs -lssl -lcrypto -lpthread -lm \\
                -Wl,-rpath,/home/user/_oqs/lib

            echo ""
            echo "检查所有程序:"
            ls -lh directory relay benchmark_pq_ntor 2>&1
            """,
            "编译directory服务器"
        )

        # 运行完整系统测试
        execute_command(
            ssh,
            """
            # 清理旧进程
            pkill -f directory 2>/dev/null || true
            pkill -f relay 2>/dev/null || true
            sleep 1

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
            sleep 3

            # 检查进程
            echo ""
            echo "运行中的进程:"
            pgrep -a directory || echo "  ❌ directory未启动"
            pgrep -a relay || echo "  ❌ relay未启动"

            # 检查日志
            echo ""
            echo "检查directory日志（最后10行）:"
            tail -10 ~/directory.log
            """,
            "启动系统组件"
        )

        import time
        print("\n等待5秒...")
        time.sleep(5)

        # 运行三跳测试
        execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/last_experiment/phytium_deployment
            echo "运行三跳电路测试（5次迭代）..."
            ./benchmark_3hop_circuit 5 localhost 5000 2>&1 | tee /tmp/3hop_test.log
            """,
            "运行三跳电路测试",
            timeout=120
        )

        # 清理
        execute_command(
            ssh,
            """
            pkill -f directory
            pkill -f relay
            echo "✓ 测试进程已清理"
            """,
            "清理进程"
        )

        print("\n" + "="*70)
        print("  ✅ 测试完成")
        print("="*70)
        return 0

    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1
    finally:
        ssh.close()

if __name__ == "__main__":
    sys.exit(main())
