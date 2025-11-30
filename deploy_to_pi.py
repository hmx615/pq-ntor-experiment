#!/usr/bin/env python3
"""
自动部署到飞腾派 - 单Pi测试版
使用paramiko自动化所有部署和测试步骤
"""

import paramiko
import sys
import time
import os

# 配置
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

def upload_file(sftp, local_path, remote_path):
    """上传文件到飞腾派"""
    try:
        sftp.put(local_path, remote_path)
        return True
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        return False

def upload_directory(sftp, local_dir, remote_dir):
    """递归上传目录"""
    try:
        # 创建远程目录
        try:
            sftp.mkdir(remote_dir)
        except:
            pass  # 目录可能已存在

        for item in os.listdir(local_dir):
            local_path = os.path.join(local_dir, item)
            remote_path = f"{remote_dir}/{item}"

            if os.path.isfile(local_path):
                sftp.put(local_path, remote_path)
            elif os.path.isdir(local_path):
                upload_directory(sftp, local_path, remote_path)

        return True
    except Exception as e:
        print(f"❌ 上传目录失败: {e}")
        return False

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          飞腾派自动部署 - 单Pi测试版                          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\n🔌 连接信息:")
    print(f"   主机: {HOST}")
    print(f"   用户: {USER}")
    print(f"   端口: {PORT}\n")

    # 创建SSH客户端
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 连接
        print(f"🔄 正在连接到 {HOST}...")
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

        # ===== 第1步：检查并清理旧代码 =====
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

        # ===== 第2步：上传代码 =====
        print("\n" + "="*70)
        print("  第2步：上传代码到飞腾派")
        print("="*70)
        print("这可能需要几分钟，请耐心等待...")

        local_base = "/home/ccc/pq-ntor-experiment"
        remote_base = "/home/user/pq-ntor-experiment"

        # 上传关键目录
        key_dirs = [
            "c",
            "deployment",
            "last_experiment/phytium_deployment",
            "scripts",
        ]

        for dir_name in key_dirs:
            local_dir = f"{local_base}/{dir_name}"
            remote_dir = f"{remote_base}/{dir_name}"

            if os.path.exists(local_dir):
                print(f"  上传 {dir_name}...")
                upload_directory(sftp, local_dir, remote_dir)
            else:
                print(f"  ⚠️ 跳过 {dir_name} (不存在)")

        # 上传关键文件
        key_files = [
            "7PI_PROJECT_SUMMARY.md",
            "SINGLE_PI_TO_7PI_GUIDE.md",
            "DEPLOY_NOW.md",
        ]

        for file_name in key_files:
            local_file = f"{local_base}/{file_name}"
            remote_file = f"{remote_base}/{file_name}"

            if os.path.exists(local_file):
                print(f"  上传 {file_name}...")
                sftp.put(local_file, remote_file)

        print("✅ 代码上传完成")

        sftp.close()

        # ===== 第3步：检查依赖 =====
        success, output, _ = execute_command(
            ssh,
            """
            dpkg -l | grep -E "gcc|make|liboqs" > /tmp/deps.txt 2>&1
            echo "已安装的依赖:"
            cat /tmp/deps.txt | grep -E "ii.*gcc|ii.*make|ii.*liboqs" | awk '{print $2}' || echo "无"
            """,
            "第3步：检查依赖"
        )

        # ===== 第4步：编译C代码 =====
        success, output, error = execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/c
            make clean 2>/dev/null || true
            make all 2>&1
            echo ""
            echo "编译结果:"
            ls -lh directory relay benchmark_pq_ntor 2>/dev/null || echo "部分文件编译失败"
            """,
            "第4步：编译C代码",
            timeout=120
        )

        if not success or "directory" not in output:
            print("\n⚠️ C代码编译可能失败，尝试安装依赖...")
            execute_command(
                ssh,
                "sudo apt update && sudo apt install -y gcc make liboqs-dev",
                "安装依赖",
                timeout=300
            )

            # 重新编译
            execute_command(
                ssh,
                "cd ~/pq-ntor-experiment/c && make clean && make all",
                "重新编译",
                timeout=120
            )

        # ===== 第5步：编译三跳测试程序 =====
        execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/last_experiment/phytium_deployment
            gcc -o benchmark_3hop_circuit benchmark_3hop_circuit.c -lm -lpthread 2>&1
            ls -lh benchmark_3hop_circuit 2>/dev/null && echo "✅ 三跳程序编译成功" || echo "❌ 编译失败"
            """,
            "第5步：编译三跳测试程序"
        )

        # ===== 第6步：运行握手测试 =====
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
            "第6步：运行握手测试"
        )

        # ===== 第7步：启动完整系统 =====
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
            "第7步：启动系统组件"
        )

        # 等待服务完全启动
        print("\n等待服务完全启动...")
        time.sleep(5)

        # ===== 第8步：运行三跳电路测试 =====
        execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/last_experiment/phytium_deployment
            echo "运行三跳电路测试（5次迭代）..."
            ./benchmark_3hop_circuit 5 localhost 5000 2>&1 | tee /tmp/3hop_test.log
            """,
            "第8步：运行三跳电路测试",
            timeout=120
        )

        # ===== 第9步：清理进程 =====
        execute_command(
            ssh,
            """
            pkill -f directory
            pkill -f relay
            sleep 1
            pgrep -f "directory|relay" && echo "⚠️ 部分进程未停止" || echo "✓ 所有测试进程已停止"
            """,
            "第9步：清理测试进程"
        )

        # ===== 第10步：创建配置脚本 =====
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
            "第10步：创建节点配置脚本"
        )

        # ===== 汇总结果 =====
        print("\n" + "="*70)
        print("  📊 部署完成汇总")
        print("="*70)

        success, output, _ = execute_command(
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
