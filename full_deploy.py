#!/usr/bin/env python3
"""
完整部署到飞腾派 - 使用paramiko
修复版：添加pthread支持，跳过classic_ntor编译
"""
import paramiko
import sys
import time
import os

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"
PORT = 22

def execute_command(ssh, command, description="", show_output=True, timeout=120):
    """执行SSH命令并返回结果"""
    if description:
        print(f"\n{'='*70}")
        print(f"  {description}")
        print('='*70)

    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout, get_pty=True)
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

def upload_file(sftp, local_path, remote_path):
    """上传文件"""
    try:
        # 确保远程目录存在
        remote_dir = os.path.dirname(remote_path)
        try:
            sftp.stat(remote_dir)
        except:
            # 创建目录
            dirs = []
            while remote_dir and remote_dir != '/':
                dirs.insert(0, remote_dir)
                remote_dir = os.path.dirname(remote_dir)
            for d in dirs:
                try:
                    sftp.mkdir(d)
                except:
                    pass

        sftp.put(local_path, remote_path)
        return True
    except Exception as e:
        print(f"❌ 上传失败 {local_path}: {e}")
        return False

def upload_directory(sftp, local_dir, remote_dir):
    """递归上传目录"""
    try:
        # 创建远程目录
        try:
            sftp.mkdir(remote_dir)
        except:
            pass

        for item in os.listdir(local_dir):
            # 跳过特定目录
            if item in ['.git', '__pycache__', 'nvm', '.vscode']:
                continue

            local_path = os.path.join(local_dir, item)
            remote_path = f"{remote_dir}/{item}"

            if os.path.isfile(local_path):
                print(f"    上传: {item}")
                upload_file(sftp, local_path, remote_path)
            elif os.path.isdir(local_path):
                upload_directory(sftp, local_path, remote_path)

        return True
    except Exception as e:
        print(f"❌ 上传目录失败 {local_dir}: {e}")
        return False

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          飞腾派完整部署 - Paramiko版                          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\n🔌 连接到 {HOST}...\n")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 连接
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

        # 打开SFTP
        sftp = ssh.open_sftp()

        # 第1步：清理旧代码
        execute_command(
            ssh,
            "rm -rf ~/pq-ntor-experiment",
            "第1步：清理旧代码"
        )

        execute_command(
            ssh,
            "mkdir -p ~/pq-ntor-experiment",
            "创建项目目录"
        )

        # 第2步：上传代码
        print("\n" + "="*70)
        print("  第2步：上传代码到飞腾派")
        print("="*70)

        local_base = "/home/ccc/pq-ntor-experiment"
        remote_base = "/home/user/pq-ntor-experiment"

        # 上传c目录
        print("  上传 c/ 目录...")
        upload_directory(sftp, f"{local_base}/c", f"{remote_base}/c")

        # 上传last_experiment/phytium_deployment
        print("  上传 last_experiment/phytium_deployment...")
        execute_command(ssh, f"mkdir -p {remote_base}/last_experiment", show_output=False)
        upload_directory(sftp,
                        f"{local_base}/last_experiment/phytium_deployment",
                        f"{remote_base}/last_experiment/phytium_deployment")

        print("✅ 代码上传完成\n")
        sftp.close()

        # 第3步：编译（跳过classic_ntor，添加pthread）
        success, output, error = execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/c

            echo "编译核心源文件..."

            # 只编译需要的.o文件（跳过classic_ntor）
            gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc \\
                -c src/kyber_kem.c -o src/kyber_kem.o

            gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc \\
                -c src/crypto_utils.c -o src/crypto_utils.o

            gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc \\
                -c src/pq_ntor.c -o src/pq_ntor.o

            gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc \\
                -c src/cell.c -o src/cell.o

            gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc \\
                -c src/onion_crypto.c -o src/onion_crypto.o

            echo ""
            echo "编译benchmark_pq_ntor..."
            gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc \\
                -o benchmark_pq_ntor \\
                benchmark/benchmark_pq_ntor.c \\
                src/kyber_kem.o src/crypto_utils.o src/pq_ntor.o \\
                -L/home/user/_oqs/lib -loqs -lssl -lcrypto -lpthread -lm \\
                -Wl,-rpath,/home/user/_oqs/lib

            echo ""
            echo "编译directory_server..."
            gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc \\
                -c src/directory_server.c -o src/directory_server.o

            gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc \\
                -o directory \\
                programs/directory_main.c \\
                src/directory_server.o src/kyber_kem.o src/crypto_utils.o src/pq_ntor.o src/cell.o \\
                -L/home/user/_oqs/lib -loqs -lssl -lcrypto -lpthread -lm \\
                -Wl,-rpath,/home/user/_oqs/lib

            echo ""
            echo "编译relay_node..."
            gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc \\
                -c src/relay_node.c -o src/relay_node.o

            gcc -Wall -Wextra -O2 -g -std=c99 -I/home/user/_oqs/include -Isrc \\
                -o relay \\
                programs/relay_main.c \\
                src/relay_node.o src/onion_crypto.o src/kyber_kem.o src/crypto_utils.o src/pq_ntor.o src/cell.o \\
                -L/home/user/_oqs/lib -loqs -lssl -lcrypto -lpthread -lm \\
                -Wl,-rpath,/home/user/_oqs/lib

            echo ""
            echo "编译结果:"
            ls -lh benchmark_pq_ntor directory relay 2>&1
            """,
            "第3步：编译C程序（跳过classic_ntor）",
            timeout=180
        )

        if "benchmark_pq_ntor" not in output or "directory" not in output:
            print("\n⚠️ 编译可能失败，查看错误信息")
            return 1

        # 第4步：编译三跳测试程序
        execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/last_experiment/phytium_deployment

            gcc -o benchmark_3hop_circuit benchmark_3hop_circuit.c -lm -lpthread 2>&1
            ls -lh benchmark_3hop_circuit 2>&1 && echo "✅ 三跳程序编译成功" || echo "❌ 编译失败"
            """,
            "第4步：编译三跳测试程序"
        )

        # 第5步：运行握手测试
        execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/c
            if [ -f ./benchmark_pq_ntor ]; then
                echo "运行10次握手测试..."
                ./benchmark_pq_ntor 10
            else
                echo "❌ benchmark_pq_ntor 不存在"
                exit 1
            fi
            """,
            "第5步：运行握手测试"
        )

        # 第6步：启动完整系统
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
            sleep 2

            # 检查进程
            echo ""
            echo "运行中的进程:"
            pgrep -a directory
            pgrep -a relay
            """,
            "第6步：启动系统组件"
        )

        # 等待服务完全启动
        print("\n等待服务完全启动...")
        time.sleep(5)

        # 第7步：运行三跳电路测试
        execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/last_experiment/phytium_deployment
            echo "运行三跳电路测试（5次迭代）..."
            ./benchmark_3hop_circuit 5 localhost 5000 2>&1 | tee /tmp/3hop_test.log
            """,
            "第7步：运行三跳电路测试",
            timeout=120
        )

        # 第8步：清理进程
        execute_command(
            ssh,
            """
            pkill -f directory
            pkill -f relay
            sleep 1
            pgrep -f "directory|relay" && echo "⚠️ 部分进程未停止" || echo "✓ 所有测试进程已停止"
            """,
            "第8步：清理测试进程"
        )

        # 第9步：创建配置脚本
        execute_command(
            ssh,
            r"""
cat > ~/pq-ntor-experiment/setup_node.sh << 'EOF'
#!/bin/bash
NODE_ID=$1
if [ -z "$NODE_ID" ] || [ "$NODE_ID" -lt 1 ] || [ "$NODE_ID" -gt 7 ]; then
    echo "用法: sudo $0 <node_id>"
    exit 1
fi
BASE_IP="192.168.5"
IP="${BASE_IP}.$((109 + NODE_ID))"
declare -A ROLES
ROLES[1]="client"
ROLES[2]="directory"
ROLES[3]="guard"
ROLES[4]="middle"
ROLES[5]="exit"
ROLES[6]="target"
ROLES[7]="monitor"
ROLE=${ROLES[$NODE_ID]}
HOSTNAME="phytium-pi${NODE_ID}-${ROLE}"
echo "配置飞腾派 #${NODE_ID}"
echo "角色: $ROLE"
echo "IP: $IP"
echo "$ROLE" > /home/user/pq-ntor-experiment/.node_role
echo "$NODE_ID" > /home/user/pq-ntor-experiment/.node_id
chown user:user /home/user/pq-ntor-experiment/.node_*
echo "✓ 配置完成"
EOF
chmod +x ~/pq-ntor-experiment/setup_node.sh
echo "✓ setup_node.sh 已创建"
            """,
            "第9步：创建节点配置脚本"
        )

        # 汇总结果
        print("\n" + "="*70)
        print("  📊 部署完成汇总")
        print("="*70)

        execute_command(
            ssh,
            """
            echo "1. 编译的二进制文件:"
            ls -lh ~/pq-ntor-experiment/c/{directory,relay,benchmark_pq_ntor} 2>&1 | tail -3
            echo ""
            echo "2. 三跳测试程序:"
            ls -lh ~/pq-ntor-experiment/last_experiment/phytium_deployment/benchmark_3hop_circuit 2>&1
            echo ""
            echo "3. 配置脚本:"
            ls -lh ~/pq-ntor-experiment/setup_node.sh 2>&1
            echo ""
            echo "4. 系统信息:"
            uname -a
            gcc --version | head -1
            """,
            "系统信息",
            show_output=True
        )

        print("\n" + "="*70)
        print("  ✅ 自动部署完成")
        print("="*70)
        print("\n下一步:")
        print("  1. 查看测试结果: ssh user@192.168.5.110 'cat /tmp/3hop_test.log'")
        print("  2. 如果成功，准备制作SD卡镜像")
        print("  3. 阅读 SINGLE_PI_TO_7PI_GUIDE.md 了解镜像制作步骤")
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
