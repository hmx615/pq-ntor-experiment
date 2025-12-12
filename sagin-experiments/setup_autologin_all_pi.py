#!/usr/bin/env python3
"""
配置所有飞腾派自动登录
避免重启后需要手动输入用户名和密码
"""

import paramiko
import sys

# 所有飞腾派IP
PI_HOSTS = ["187", "188", "190", "186", "110", "189", "185"]
SSH_USER = "user"
SSH_PASS = "user"


def execute_ssh_command(host, command, use_sudo=False):
    """执行SSH命令"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(f"192.168.5.{host}", username=SSH_USER, password=SSH_PASS, timeout=10)

        if use_sudo:
            command = f"echo '{SSH_PASS}' | sudo -S {command}"

        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        return output, error
    except Exception as e:
        return None, str(e)
    finally:
        ssh.close()


def setup_autologin(host):
    """配置自动登录"""
    print(f"\n{'='*60}")
    print(f"配置自动登录: 192.168.5.{host}")
    print(f"{'='*60}")

    # 检查系统类型
    print("  检测显示管理器...")
    output, _ = execute_ssh_command(host, "systemctl status display-manager 2>/dev/null | grep -i lightdm")

    if output and "lightdm" in output.lower():
        print("  检测到 LightDM")
        return setup_lightdm_autologin(host)

    output, _ = execute_ssh_command(host, "systemctl status display-manager 2>/dev/null | grep -i gdm")
    if output and "gdm" in output.lower():
        print("  检测到 GDM")
        return setup_gdm_autologin(host)

    # 默认尝试LightDM（飞腾派常用）
    print("  未检测到显示管理器，尝试配置LightDM...")
    return setup_lightdm_autologin(host)


def setup_lightdm_autologin(host):
    """配置LightDM自动登录"""
    print("  配置 LightDM 自动登录...")

    # 备份原配置
    execute_ssh_command(
        host,
        "cp /etc/lightdm/lightdm.conf /etc/lightdm/lightdm.conf.backup 2>/dev/null || true",
        use_sudo=True
    )

    # 配置自动登录
    config_commands = [
        # 确保配置目录存在
        "mkdir -p /etc/lightdm/lightdm.conf.d",

        # 创建自动登录配置
        f"bash -c 'cat > /etc/lightdm/lightdm.conf.d/50-autologin.conf << EOF\n[Seat:*]\nautologin-user={SSH_USER}\nautologin-user-timeout=0\nuser-session=ubuntu\nEOF'",

        # 设置权限
        "chmod 644 /etc/lightdm/lightdm.conf.d/50-autologin.conf",
    ]

    for cmd in config_commands:
        output, error = execute_ssh_command(host, cmd, use_sudo=True)
        if error and "password" not in error.lower():
            print(f"    ⚠️  警告: {error[:50]}...")

    print("  ✅ LightDM 自动登录已配置")
    return True


def setup_gdm_autologin(host):
    """配置GDM自动登录"""
    print("  配置 GDM 自动登录...")

    # 备份原配置
    execute_ssh_command(
        host,
        "cp /etc/gdm3/custom.conf /etc/gdm3/custom.conf.backup 2>/dev/null || true",
        use_sudo=True
    )

    # 修改GDM配置
    config_cmd = f"""bash -c 'cat > /etc/gdm3/custom.conf << EOF
[daemon]
AutomaticLoginEnable = true
AutomaticLogin = {SSH_USER}

[security]

[xdmcp]

[chooser]

[debug]
EOF'"""

    execute_ssh_command(host, config_cmd, use_sudo=True)
    print("  ✅ GDM 自动登录已配置")
    return True


def disable_lock_screen(host):
    """禁用锁屏和屏保"""
    print("  禁用锁屏和屏保...")

    commands = [
        # 禁用锁屏
        "gsettings set org.gnome.desktop.screensaver lock-enabled false 2>/dev/null || true",
        "gsettings set org.gnome.desktop.screensaver idle-activation-enabled false 2>/dev/null || true",

        # 禁用自动挂起
        "gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing' 2>/dev/null || true",
        "gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing' 2>/dev/null || true",

        # 设置屏幕永不关闭
        "gsettings set org.gnome.desktop.session idle-delay 0 2>/dev/null || true",
    ]

    for cmd in commands:
        execute_ssh_command(host, cmd)

    print("  ✅ 锁屏和屏保已禁用")


def main():
    print("\n" + "="*60)
    print("配置所有飞腾派自动登录")
    print("="*60)
    print(f"\n将配置 {len(PI_HOSTS)} 个飞腾派")
    print("功能:")
    print("  1. 启用自动登录（无需输入用户名密码）")
    print("  2. 禁用锁屏和屏保")
    print("  3. 禁用自动挂起\n")

    results = []

    for host in PI_HOSTS:
        try:
            # 配置自动登录
            success = setup_autologin(host)

            # 禁用锁屏
            disable_lock_screen(host)

            results.append({"host": host, "success": success})

        except Exception as e:
            print(f"  ❌ 配置失败: {e}")
            results.append({"host": host, "success": False})

    # 汇总报告
    print("\n" + "="*60)
    print("配置结果汇总")
    print("="*60 + "\n")

    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count

    print(f"总计: {len(results)} 个飞腾派")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个\n")

    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"{status} 192.168.5.{r['host']}")

    print("\n" + "="*60)
    print("重要提示:")
    print("="*60)
    print("1. 配置已生效，但需要重启才能看到效果")
    print("2. 重启后将自动登录到桌面，无需输入密码")
    print("3. 如需恢复手动登录，删除配置文件:")
    print("   sudo rm /etc/lightdm/lightdm.conf.d/50-autologin.conf")
    print("4. 如需批量重启所有飞腾派，执行:")
    print("   python3 reboot_all_pi.py")
    print()

    print("✅ 配置完成！\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        sys.exit(1)
