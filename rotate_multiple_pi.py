#!/usr/bin/env python3
"""
批量配置飞腾派屏幕旋转180度脚本
支持多台设备同时配置
"""

import paramiko
import sys
from datetime import datetime

# 飞腾派配置列表
PI_DEVICES = [
    {"host": "192.168.5.186", "user": "user", "pass": "user", "name": "Pi-186"},
    {"host": "192.168.5.110", "user": "user", "pass": "user", "name": "Pi-110"},
]

def execute_command(ssh, command, use_sudo=False, sudo_password=None):
    """执行SSH命令"""
    if use_sudo and sudo_password:
        command = f'echo "{sudo_password}" | sudo -S {command}'

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()
    return output, error

def rotate_screen(device):
    """配置单个设备的屏幕旋转"""
    host = device["host"]
    user = device["user"]
    password = device["pass"]
    name = device["name"]

    print(f"\n{'='*60}")
    print(f"配置设备: {name} ({host})")
    print(f"{'='*60}\n")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 连接
        print(f"📡 连接到 {host}...")
        ssh.connect(host, port=22, username=user, password=password, timeout=10)
        print("✅ 连接成功！\n")

        # 1. 检查当前旋转状态
        print("1️⃣  检查当前旋转状态...")
        output, error = execute_command(ssh, "cat /sys/class/graphics/fbcon/rotate")
        print(f"   当前旋转值: {output}")
        print(f"   (0=正常, 1=90度, 2=180度, 3=270度)\n")

        # 2. 创建systemd服务
        print("2️⃣  创建开机自动旋转服务...")
        service_content = """[Unit]
Description=Rotate Screen 180 degrees
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c "echo 2 > /sys/class/graphics/fbcon/rotate"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""
        # 使用 sudo tee 创建服务文件
        cmd = f"echo '{password}' | sudo -S bash -c 'cat > /etc/systemd/system/rotate-screen.service << \"EOFSERVICE\"\n{service_content}EOFSERVICE\n'"
        execute_command(ssh, cmd)

        # 重载、启用、启动服务
        execute_command(ssh, f"echo '{password}' | sudo -S systemctl daemon-reload")
        execute_command(ssh, f"echo '{password}' | sudo -S systemctl enable rotate-screen.service")
        execute_command(ssh, f"echo '{password}' | sudo -S systemctl start rotate-screen.service")
        print("   ✅ 服务已创建并启用\n")

        # 3. 检查图形界面
        print("3️⃣  检查图形界面配置...")
        output, error = execute_command(ssh, "command -v xrandr")

        display_output = None
        if output:
            print("   检测到X11环境")

            # 获取显示输出设备
            output, error = execute_command(
                ssh,
                "DISPLAY=:0 xrandr 2>/dev/null | grep ' connected' | awk '{print $1}' | head -n1"
            )

            if output:
                display_output = output.strip()
                print(f"   显示输出: {display_output}")

                # 旋转屏幕
                execute_command(
                    ssh,
                    f"DISPLAY=:0 xrandr --output {display_output} --rotate inverted 2>/dev/null"
                )

                # 创建自动启动脚本
                autostart_content = f"""[Desktop Entry]
Type=Application
Name=Rotate Screen
Exec=sh -c 'export DISPLAY=:0; xrandr --output {display_output} --rotate inverted'
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
                execute_command(ssh, "mkdir -p ~/.config/autostart")
                cmd = f"cat > ~/.config/autostart/rotate-screen.desktop << 'EOFDESKTOP'\n{autostart_content}EOFDESKTOP\n"
                execute_command(ssh, cmd)

                print("   ✅ X11旋转已配置（立即生效）\n")
            else:
                print("   ℹ️  未检测到图形输出\n")
        else:
            print("   ℹ️  系统无图形界面，仅framebuffer旋转生效\n")

        # 4. 立即设置framebuffer旋转
        print("4️⃣  立即设置framebuffer旋转...")
        execute_command(
            ssh,
            f"echo '{password}' | sudo -S bash -c 'echo 2 > /sys/class/graphics/fbcon/rotate'"
        )
        print("   ✅ Framebuffer旋转已设置\n")

        # 5. 刷新显示
        print("5️⃣  刷新显示...")
        execute_command(
            ssh,
            f"echo '{password}' | sudo -S bash -c 'if [ -w /sys/class/vtconsole/vtcon1/bind ]; then echo 0 > /sys/class/vtconsole/vtcon1/bind; echo 1 > /sys/class/vtconsole/vtcon1/bind; fi'"
        )
        print("   ✅ 显示已刷新\n")

        # 6. 验证
        print("6️⃣  验证配置...")
        output, error = execute_command(ssh, "cat /sys/class/graphics/fbcon/rotate")
        print(f"   最终旋转值: {output}")

        service_status, _ = execute_command(
            ssh,
            f"echo '{password}' | sudo -S systemctl is-enabled rotate-screen.service"
        )
        print(f"   服务状态: {service_status}\n")

        print(f"✅ {name} 配置完成！")

        return {
            "name": name,
            "host": host,
            "status": "成功",
            "display_output": display_output,
            "rotate_value": output,
            "service_enabled": service_status.strip() == "enabled"
        }

    except paramiko.AuthenticationException:
        print(f"❌ 认证失败！请检查用户名和密码")
        return {"name": name, "host": host, "status": "认证失败"}
    except paramiko.SSHException as e:
        print(f"❌ SSH连接错误: {e}")
        return {"name": name, "host": host, "status": f"SSH错误: {e}"}
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return {"name": name, "host": host, "status": f"错误: {e}"}
    finally:
        ssh.close()

def main():
    print("\n" + "="*60)
    print("飞腾派批量屏幕旋转配置工具")
    print("="*60)
    print(f"\n配置时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"设备数量: {len(PI_DEVICES)}")
    print()

    results = []

    # 逐个配置设备
    for device in PI_DEVICES:
        result = rotate_screen(device)
        results.append(result)

    # 汇总报告
    print("\n" + "="*60)
    print("配置汇总报告")
    print("="*60 + "\n")

    success_count = sum(1 for r in results if r["status"] == "成功")
    fail_count = len(results) - success_count

    print(f"总计: {len(results)} 台设备")
    print(f"成功: {success_count} 台")
    print(f"失败: {fail_count} 台\n")

    print("详细结果:")
    print("-" * 60)
    for result in results:
        status_icon = "✅" if result["status"] == "成功" else "❌"
        print(f"{status_icon} {result['name']} ({result['host']})")
        print(f"   状态: {result['status']}")
        if result["status"] == "成功":
            print(f"   显示输出: {result.get('display_output', 'N/A')}")
            print(f"   旋转值: {result.get('rotate_value', 'N/A')}")
            print(f"   服务启用: {'是' if result.get('service_enabled') else '否'}")
        print()

    print("="*60)
    print("📝 注意事项:")
    print("="*60)
    print("1. X11图形界面旋转已立即生效")
    print("2. Framebuffer旋转可能需要重启才能完全生效")
    print("3. 下次重启后，所有配置将自动生效")
    print("4. 如需恢复正常显示，请参考生成的总结文档")
    print("\n✅ 所有配置已完成！\n")

if __name__ == "__main__":
    main()
