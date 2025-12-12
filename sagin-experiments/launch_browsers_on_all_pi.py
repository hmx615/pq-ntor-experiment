#!/usr/bin/env python3
"""
批量在飞腾派上启动浏览器访问SAGIN节点视图
通过SSH连接各飞腾派，启动全屏浏览器
"""

import paramiko
import time
import sys

# 节点配置映射
NODE_CONFIG = {
    "187": {"node_id": "SAT", "name": "卫星节点"},
    "188": {"node_id": "control", "name": "控制面板"},  # 特殊：控制面板
    "190": {"node_id": "UAV1", "name": "无人机1"},
    "186": {"node_id": "UAV2", "name": "无人机2"},
    "110": {"node_id": "Ground1", "name": "地面终端1"},
    "189": {"node_id": "Ground2", "name": "地面终端2"},
    "185": {"node_id": "Ground3", "name": "地面终端3"},
}

BASE_URL = "http://192.168.5.83:8080"
SSH_USER = "user"
SSH_PASS = "user"


def execute_ssh_command(host, command, timeout=10):
    """执行SSH命令"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(f"192.168.5.{host}", username=SSH_USER, password=SSH_PASS, timeout=timeout)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        return output, error
    except Exception as e:
        return None, str(e)
    finally:
        ssh.close()


def kill_existing_browsers(host):
    """关闭已有的浏览器进程"""
    print(f"  关闭已有浏览器进程...")

    # 关闭chromium
    execute_ssh_command(host, "pkill -9 chromium")
    # 关闭firefox
    execute_ssh_command(host, "pkill -9 firefox")

    time.sleep(1)


def launch_browser_on_pi(host, url, node_name):
    """在指定飞腾派上启动全屏浏览器"""
    print(f"\n{'='*60}")
    print(f"启动浏览器: {node_name} (192.168.5.{host})")
    print(f"访问地址: {url}")
    print(f"{'='*60}")

    # 1. 关闭已有浏览器
    kill_existing_browsers(host)

    # 2. 检查DISPLAY环境
    print(f"  检查显示环境...")
    output, error = execute_ssh_command(host, "echo $DISPLAY")
    display = output if output else ":0"
    print(f"  DISPLAY: {display}")

    # 3. 启动Firefox浏览器（全屏模式）
    print(f"  启动全屏浏览器 (Firefox)...")

    # 使用Firefox全屏模式
    firefox_cmd = f"DISPLAY={display} firefox --kiosk {url} </dev/null >/dev/null 2>&1 &"
    output, error = execute_ssh_command(host, firefox_cmd, timeout=5)

    time.sleep(2)

    # 验证浏览器是否启动
    output, _ = execute_ssh_command(host, "pgrep -f firefox | wc -l")
    if output and int(output.strip()) > 0:
        print(f"  ✅ Firefox 已启动 ({output.strip()} 进程)")
        return True

    print(f"  ❌ Firefox 启动失败")
    return False


def main():
    print("\n" + "="*60)
    print("SAGIN 6+1 系统批量启动浏览器")
    print("="*60)
    print(f"\n将在 {len(NODE_CONFIG)} 个飞腾派上启动浏览器\n")

    results = []

    for host, config in NODE_CONFIG.items():
        node_id = config["node_id"]
        node_name = config["name"]

        # 构建URL
        if node_id == "control":
            # 控制面板特殊处理
            url = f"{BASE_URL}/control-panel/index.html"
        else:
            # 普通节点视图
            url = f"{BASE_URL}/node-view/index.html?node_id={node_id}"

        # 启动浏览器
        success = launch_browser_on_pi(host, url, node_name)

        results.append({
            "host": host,
            "name": node_name,
            "node_id": node_id,
            "url": url,
            "success": success
        })

        # 稍微延迟避免同时SSH过多
        time.sleep(1)

    # 汇总报告
    print("\n" + "="*60)
    print("启动结果汇总")
    print("="*60 + "\n")

    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count

    print(f"总计: {len(results)} 个节点")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个\n")

    print("详细结果:")
    print("-" * 60)
    for r in results:
        status_icon = "✅" if r["success"] else "❌"
        print(f"{status_icon} {r['name']} (192.168.5.{r['host']})")
        print(f"   节点ID: {r['node_id']}")
        print(f"   地址: {r['url']}")
        print()

    print("="*60)
    print("提示:")
    print("="*60)
    print("1. 如需关闭所有浏览器，执行:")
    print("   python3 close_all_browsers.py")
    print()
    print("2. 如需重启单个节点浏览器，执行:")
    print("   ssh user@192.168.5.XXX 'pkill chromium && DISPLAY=:0 chromium-browser --kiosk --app=<URL> &'")
    print()
    print("3. 查看节点浏览器进程:")
    print("   ssh user@192.168.5.XXX 'ps aux | grep chromium'")
    print()

    if fail_count > 0:
        print("⚠️  部分节点启动失败，请检查:")
        print("   - 飞腾派是否有图形界面")
        print("   - DISPLAY环境变量是否正确")
        print("   - 是否安装了chromium-browser或firefox")
        print()

    print("✅ 批量启动完成！\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        sys.exit(1)
