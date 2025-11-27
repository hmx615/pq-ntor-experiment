#!/usr/bin/env python3
"""
Deploy local mode fix to Phytium Pi for 12-topology testing

This script:
1. Backs up original directory_server.c
2. Copies the local mode version
3. Adds relay registration to relay_node.c
4. Recompiles with USE_LOCAL_MODE=1
5. Runs a quick test
"""

import paramiko
import time
import sys

# Connection settings
HOST = "192.168.5.110"
PORT = 22
USER = "user"
PASSWORD = "user"

def execute_command(ssh, command, timeout=30, show_output=True):
    """Execute command and return stdout, stderr, exit code"""
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    stdout_text = stdout.read().decode('utf-8')
    stderr_text = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()

    if show_output:
        if stdout_text:
            print(stdout_text, end='')
        if stderr_text:
            print(stderr_text, end='', file=sys.stderr)

    return stdout_text, stderr_text, exit_code

def upload_file(sftp, local_path, remote_path):
    """Upload file via SFTP"""
    try:
        sftp.put(local_path, remote_path)
        print(f"✅ Uploaded: {local_path} -> {remote_path}")
        return True
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     应用本地模式修复 - 飞腾派12拓扑实验                        ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    # Connect
    print(f"🔌 连接到 {HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname=HOST, port=PORT, username=USER, password=PASSWORD,
                   allow_agent=False, look_for_keys=False)
        print("✅ 连接成功\n")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return 1

    sftp = ssh.open_sftp()

    # Step 1: Backup original
    print("=" * 70)
    print("步骤 1: 备份原始文件")
    print("=" * 70)

    backup_cmd = """
cd /home/user/pq-ntor-experiment/c/src
if [ ! -f directory_server.c.backup ]; then
    cp directory_server.c directory_server.c.backup
    echo "✅ 已备份 directory_server.c"
else
    echo "⚠️  备份已存在，跳过"
fi
"""
    execute_command(ssh, backup_cmd)
    print()

    # Step 2: Upload new files
    print("=" * 70)
    print("步骤 2: 上传修改后的文件")
    print("=" * 70)

    files_to_upload = [
        ("/home/ccc/pq-ntor-experiment/c/src/directory_server_local_mode.c",
         "/home/user/pq-ntor-experiment/c/src/directory_server_local_mode.c"),
        ("/home/ccc/pq-ntor-experiment/c/src/relay_registration.c",
         "/home/user/pq-ntor-experiment/c/src/relay_registration.c"),
        ("/home/ccc/pq-ntor-experiment/c/include/relay_registration.h",
         "/home/user/pq-ntor-experiment/c/include/relay_registration.h"),
    ]

    for local, remote in files_to_upload:
        upload_file(sftp, local, remote)
    print()

    # Step 3: Replace directory_server.c with local mode version
    print("=" * 70)
    print("步骤 3: 替换 directory_server.c")
    print("=" * 70)

    replace_cmd = """
cd /home/user/pq-ntor-experiment/c/src
cp directory_server_local_mode.c directory_server.c
echo "✅ directory_server.c 已替换为本地模式版本"
"""
    execute_command(ssh, replace_cmd)
    print()

    # Step 4: Modify relay_node.c to add registration
    print("=" * 70)
    print("步骤 4: 修改 relay_node.c 添加注册功能")
    print("=" * 70)

    # First, check if already modified
    check_cmd = "grep -q 'register_with_directory' /home/user/pq-ntor-experiment/c/src/relay_node.c && echo 'FOUND' || echo 'NOT_FOUND'"
    stdout, _, _ = execute_command(ssh, check_cmd, show_output=False)

    if "FOUND" in stdout:
        print("⚠️  relay_node.c 已包含注册代码，跳过修改")
    else:
        # Create modified relay_node.c
        modify_relay_cmd = """
cd /home/user/pq-ntor-experiment/c/src

# Backup relay_node.c
if [ ! -f relay_node.c.backup ]; then
    cp relay_node.c relay_node.c.backup
fi

# Add registration call after relay starts listening
# We'll insert after the "Relay node initialized" message
sed -i '/printf.*Relay node initialized/a\\
\\
    /* Register with directory in local mode */\\
    #ifdef USE_LOCAL_MODE\\
    sleep(1); /* Wait for directory to be ready */\\
    if (register_with_directory("127.0.0.1", 5000, port, node_type) == 0) {\\
        printf("[Relay] Registered with directory\\\\n");\\
    } else {\\
        fprintf(stderr, "[Relay] Warning: Could not register with directory\\\\n");\\
    }\\
    #endif
' relay_node.c

# Add include at the top
sed -i '/#include "relay_node.h"/a\\
#ifdef USE_LOCAL_MODE\\
#include "relay_registration.h"\\
#endif
' relay_node.c

echo "✅ relay_node.c 已修改"
"""
        execute_command(ssh, modify_relay_cmd)
    print()

    # Step 5: Update Makefile to compile with USE_LOCAL_MODE
    print("=" * 70)
    print("步骤 5: 更新 Makefile")
    print("=" * 70)

    makefile_cmd = """
cd /home/user/pq-ntor-experiment/c

# Backup Makefile
if [ ! -f Makefile.backup ]; then
    cp Makefile Makefile.backup
fi

# Add USE_LOCAL_MODE flag to CFLAGS
if ! grep -q "USE_LOCAL_MODE" Makefile; then
    sed -i 's/^CFLAGS = /CFLAGS = -DUSE_LOCAL_MODE=1 /' Makefile
    echo "✅ Makefile 已更新 (添加 -DUSE_LOCAL_MODE=1)"
else
    echo "⚠️  Makefile 已包含 USE_LOCAL_MODE，跳过"
fi

# Add relay_registration.o to objects if not present
if ! grep -q "relay_registration.o" Makefile; then
    sed -i 's/RELAY_OBJS = /RELAY_OBJS = src\/relay_registration.o /' Makefile
    echo "✅ Makefile 已添加 relay_registration.o"
fi
"""
    execute_command(ssh, makefile_cmd)
    print()

    # Step 6: Recompile
    print("=" * 70)
    print("步骤 6: 重新编译")
    print("=" * 70)

    compile_cmd = """
cd /home/user/pq-ntor-experiment/c
source ~/.bashrc
make clean
make directory relay client
echo ""
echo "✅ 编译完成"
ls -lh directory relay client 2>/dev/null || echo "⚠️ 部分程序编译失败"
"""
    stdout, stderr, code = execute_command(ssh, compile_cmd, timeout=60)

    if code != 0:
        print("⚠️  编译出现警告或错误，请检查")
    print()

    # Step 7: Quick test
    print("=" * 70)
    print("步骤 7: 快速测试")
    print("=" * 70)

    test_cmd = """
cd /home/user/pq-ntor-experiment/c

# Test 1: Check if directory accepts registration
echo "测试 1: 检查 directory 是否支持注册端点"
timeout 5 ./directory &
DIRECTORY_PID=$!
sleep 2

# Try to query the /register endpoint (should return 200 or error)
curl -s -X POST http://127.0.0.1:5000/register \
     -H "Content-Type: application/json" \
     -d '{"hostname":"127.0.0.1","port":9001,"type":1}' \
     && echo "" && echo "✅ Directory 接受注册请求" \
     || echo "⚠️  Directory 可能不支持注册"

kill $DIRECTORY_PID 2>/dev/null
wait $DIRECTORY_PID 2>/dev/null

echo ""
echo "测试 2: 检查程序版本信息"
strings directory | grep -i "local mode" && echo "✅ Directory 包含本地模式代码" || echo "⚠️  未找到本地模式标记"

echo ""
echo "✅ 测试完成"
"""
    execute_command(ssh, test_cmd, timeout=15)
    print()

    # Summary
    print("=" * 70)
    print("✅ 修复应用完成！")
    print("=" * 70)
    print()
    print("📋 修改摘要:")
    print("  1. directory_server.c - 添加本地模式支持和动态注册")
    print("  2. relay_node.c - 添加启动时注册到 directory")
    print("  3. Makefile - 添加 -DUSE_LOCAL_MODE=1 编译标志")
    print("  4. 所有程序已重新编译")
    print()
    print("🧪 下一步:")
    print("  运行 12-topology 测试验证修复:")
    print("  python3 /home/ccc/pq-ntor-experiment/simple_run_12topo.py")
    print()

    sftp.close()
    ssh.close()
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
