#!/usr/bin/env python3
"""
调试系统 - 检查directory日志和进程状态
"""
import paramiko
import sys

HOST = "192.168.5.110"
USER = "user"
PASSWORD = "user"
PORT = 22

def execute_command(ssh, command, description=""):
    """执行SSH命令"""
    if description:
        print(f"\n{'='*70}")
        print(f"  {description}")
        print('='*70)

    stdin, stdout, stderr = ssh.exec_command(command, timeout=60, get_pty=True)
    output = stdout.read().decode('utf-8')
    print(output)
    return output

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname=HOST, port=PORT, username=USER, password=PASSWORD,
                   timeout=10, allow_agent=False, look_for_keys=False)
        print("✅ 已连接\n")

        # 检查directory二进制
        execute_command(ssh, "ls -lh ~/pq-ntor-experiment/c/directory", "检查directory文件")

        # 清理旧进程
        execute_command(ssh, "pkill -f directory; pkill -f relay; sleep 1", "清理旧进程")

        # 手动启动directory（前台，看输出）
        execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/c
            timeout 3 ./directory 5000 2>&1 || true
            """,
            "手动启动directory（3秒超时）"
        )

        # 测试端口
        execute_command(ssh, "netstat -tuln | grep 5000 || echo '端口5000未监听'", "检查端口5000")

        # 启动后台directory
        execute_command(
            ssh,
            """
            cd ~/pq-ntor-experiment/c
            nohup ./directory 5000 > ~/directory.log 2>&1 &
            sleep 2
            pgrep -a directory
            """,
            "后台启动directory"
        )

        # 查看日志
        execute_command(ssh, "cat ~/directory.log", "Directory日志")

        # 测试HTTP连接
        execute_command(ssh, "curl -v http://localhost:5000/nodes 2>&1 || echo 'curl失败'", "测试HTTP连接")

        # 清理
        execute_command(ssh, "pkill -f directory", "清理")

        return 0

    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1
    finally:
        ssh.close()

if __name__ == "__main__":
    sys.exit(main())
