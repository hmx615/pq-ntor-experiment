# 🚀 VSCode 中运行 PQ-Ntor C 程序指南

## 前提条件

- ✅ VSCode 已安装
- ✅ WSL (Ubuntu 22.04) 已安装
- ✅ liboqs 已安装在 `~/_oqs/`

---

## 方法一：使用 VSCode 内置终端（推荐）

### 步骤 1：打开项目文件夹

在 VSCode 中：
1. **File → Open Folder...**
2. 输入路径：`\\wsl.localhost\Ubuntu-22.04\home\ccc\pq-ntor-experiment\c`
3. 点击"选择文件夹"

或者在任意终端中运行：
```bash
cd /home/ccc/pq-ntor-experiment/c
code .
```

### 步骤 2：打开 WSL 终端

1. 按 `Ctrl + J` 打开终端面板
2. 在终端右上角的下拉菜单中，选择 **"Ubuntu (WSL)"**
3. 或点击 `+` 号旁边的 `˅` 选择 **"Ubuntu (WSL)"**

### 步骤 3：查看项目结构

在终端中输入：
```bash
ls -la
```

应该看到：
```
src/          # 源代码
tests/        # 测试程序
Makefile      # 构建脚本
README.md     # 文档
```

### 步骤 4：查看 liboqs 配置

```bash
make info
```

应该显示 liboqs 已正确安装在 `~/_oqs/lib/liboqs.so.0.11.0`。

### 步骤 5：编译程序

```bash
make clean
make
```

你会看到：
```
Cleaning...
✓ Clean complete
Compiling src/kyber_kem.c...
Building test_kyber...
✓ Built: test_kyber
```

### 步骤 6：运行测试程序

```bash
./test_kyber
```

或使用 make 命令：
```bash
make test
```

**预期输出**：
```
======================================================================
🧪 Testing Kyber KEM Wrapper
======================================================================

=== Kyber Parameters ===
Algorithm:     Kyber512
Public key:    800 bytes
Secret key:    1632 bytes
Ciphertext:    768 bytes
Shared secret: 32 bytes
========================

Step 1: Alice generates keypair
---------------------------------------
  Alice public key: 8812363f...
  ✓ Keypair generated successfully

... (更多测试步骤)

======================================================================
✅ All Kyber KEM tests passed!
======================================================================
```

---

## 方法二：使用 VSCode Tasks（自动化）

我们可以配置 VSCode Tasks 来一键编译和运行。

### 创建 `.vscode/tasks.json`

在项目根目录创建 `.vscode` 文件夹和配置文件：

```bash
mkdir -p .vscode
```

然后在 VSCode 中创建文件 `.vscode/tasks.json`，内容如下：

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Build (make)",
            "type": "shell",
            "command": "make",
            "group": {
                "kind": "build",
                "isDefault": true
            },
            "problemMatcher": ["$gcc"],
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Build and Test",
            "type": "shell",
            "command": "make test",
            "group": "test",
            "problemMatcher": ["$gcc"],
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": true,
                "panel": "shared"
            }
        },
        {
            "label": "Clean",
            "type": "shell",
            "command": "make clean",
            "problemMatcher": []
        },
        {
            "label": "Run test_kyber",
            "type": "shell",
            "command": "./test_kyber",
            "dependsOn": ["Build (make)"],
            "problemMatcher": [],
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": true,
                "panel": "shared"
            }
        }
    ]
}
```

### 使用 Tasks

创建完成后：
1. 按 `Ctrl + Shift + P` 打开命令面板
2. 输入 **"Tasks: Run Task"**
3. 选择：
   - **"Build (make)"** - 只编译
   - **"Build and Test"** - 编译并测试
   - **"Run test_kyber"** - 运行测试程序
   - **"Clean"** - 清理编译文件

或直接按快捷键：
- `Ctrl + Shift + B` - 执行默认构建任务（Build）

---

## 方法三：配置调试器（高级）

如果想使用 VSCode 的调试功能（打断点、单步执行），创建 `.vscode/launch.json`：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug test_kyber",
            "type": "cppdbg",
            "request": "launch",
            "program": "${workspaceFolder}/test_kyber",
            "args": [],
            "stopAtEntry": false,
            "cwd": "${workspaceFolder}",
            "environment": [],
            "externalConsole": false,
            "MIMode": "gdb",
            "setupCommands": [
                {
                    "description": "Enable pretty-printing for gdb",
                    "text": "-enable-pretty-printing",
                    "ignoreFailures": true
                }
            ],
            "preLaunchTask": "Build (make)",
            "miDebuggerPath": "/usr/bin/gdb"
        }
    ]
}
```

### 使用调试器

1. 在代码中点击行号左侧设置断点（红点）
2. 按 `F5` 开始调试
3. 使用调试工具栏：
   - **继续** (F5)
   - **单步跳过** (F10)
   - **单步进入** (F11)
   - **单步跳出** (Shift+F11)

---

## 常见问题

### ❌ 问题 1：找不到 liboqs.so

**错误信息**：
```
error while loading shared libraries: liboqs.so: cannot open shared object file
```

**解决方法**：
Makefile 已经设置了 `-Wl,-rpath`，但如果还是有问题，手动设置环境变量：

```bash
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH
./test_kyber
```

### ❌ 问题 2：make 命令找不到

**错误信息**：
```
bash: make: command not found
```

**解决方法**：
确保在 WSL 终端中运行，而不是 Git Bash 或 PowerShell。

### ❌ 问题 3：GCC 找不到

**解决方法**：
安装 GCC：
```bash
sudo apt update
sudo apt install build-essential
```

---

## 快速命令参考

```bash
# 查看配置
make info

# 清理旧文件
make clean

# 编译
make

# 编译并测试
make test

# 只运行测试
./test_kyber

# 使用 Kyber768 编译
make clean
make CFLAGS='-Wall -Wextra -O2 -g -std=c99 -DUSE_KYBER768'
./test_kyber
```

---

## 下一步

程序运行成功后，您可以：

1. ✅ 查看测试输出，确认 Kyber KEM 工作正常
2. 📝 开始实现 PQ-Ntor 握手协议 (`pq_ntor.c`)
3. 📊 编写性能基准测试程序
4. 🔬 收集论文数据

---

**遇到问题？**
- 检查 [README.md](README.md) 中的详细说明
- 查看 [Makefile](Makefile) 中的构建配置
- 阅读 [PQ-Tor项目工作日志-2025-10-29.md](~/PQ-Tor项目工作日志-2025-10-29.md)
