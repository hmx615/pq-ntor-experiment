# 📸 VSCode 运行 C 程序 - 图解步骤

## 🎯 目标

在 VSCode 中编译并运行 `test_kyber` 程序。

---

## 📋 步骤 1：打开 VSCode 终端

### 操作：
按键盘快捷键：`Ctrl + J`（或者 `Ctrl + ~`）

### 你会看到：
VSCode 底部出现终端面板，类似这样：

```
┌─────────────────────────────────────────────┐
│ TERMINAL                          ˅  +  🗑  │
├─────────────────────────────────────────────┤
│ PS C:\Users\Senseless>                      │
│                                             │
└─────────────────────────────────────────────┘
```

**注意看右上角**：
- `˅` - 下拉菜单（用来切换终端类型）
- `+` - 新建终端
- `🗑` - 删除终端

---

## 📋 步骤 2：切换到 WSL 终端

### 操作：
1. 点击终端右上角的 **`˅`（下拉箭头）**
2. 在弹出菜单中选择：**"Ubuntu (WSL)"** 或 **"Ubuntu-22.04 (WSL)"**

### 你会看到：
终端类型从 `bash` 或 `powershell` 变成了 `wsl`：

```
┌─────────────────────────────────────────────┐
│ TERMINAL: wsl                     ˅  +  🗑  │  ← 注意这里显示 wsl
├─────────────────────────────────────────────┤
│ ccc@DESKTOP-H9OFSNV:~$                      │  ← Linux 提示符
│                                             │
└─────────────────────────────────────────────┘
```

**如何确认在 WSL 中？**
- 提示符包含 `@`，比如 `ccc@DESKTOP-H9OFSNV`
- 显示当前目录，比如 `~` 或 `/home/ccc`

---

## 📋 步骤 3：进入项目目录

### 操作：
在终端中输入（复制粘贴即可）：
```bash
cd ~/pq-ntor-experiment/c
```

按回车键。

### 你会看到：
```
ccc@DESKTOP-H9OFSNV:~/pq-ntor-experiment/c$
```

提示符变成了项目目录路径。

### 验证：
输入 `ls` 查看文件：
```bash
ls
```

应该看到：
```
Makefile  README.md  src/  tests/  benchmark/  examples/
```

---

## 📋 步骤 4：查看配置信息（可选但推荐）

### 操作：
```bash
make info
```

### 你会看到：
```
=== Build Configuration ===
CC:              gcc
CFLAGS:          -Wall -Wextra -O2 -g -std=c99
liboqs dir:      /home/ccc/_oqs
liboqs include:  /home/ccc/_oqs/include
liboqs lib:      /home/ccc/_oqs/lib
==========================

Checking liboqs installation:
-rw-r--r-- 1 ccc ccc 8.0M Oct 28 11:41 /home/ccc/_oqs/lib/liboqs.so.0.11.0
```

**✅ 看到这些说明环境正常！**

---

## 📋 步骤 5：编译程序

### 操作：
```bash
make
```

### 你会看到：
```
Compiling src/kyber_kem.c...
gcc -Wall -Wextra -O2 -g -std=c99 -I/home/ccc/_oqs/include -Isrc -c src/kyber_kem.c -o src/kyber_kem.o
Building test_kyber...
gcc -Wall -Wextra -O2 -g -std=c99 -I/home/ccc/_oqs/include -Isrc -o test_kyber tests/test_kyber.c src/kyber_kem.o -L/home/ccc/_oqs/lib -loqs -Wl,-rpath,/home/ccc/_oqs/lib
✓ Built: test_kyber
```

**✅ 看到 "✓ Built: test_kyber" 说明编译成功！**

### 编译后会生成：
- `test_kyber` - 可执行文件（测试程序）
- `src/kyber_kem.o` - 目标文件

---

## 📋 步骤 6：运行测试程序

### 操作：
```bash
./test_kyber
```

**注意前面的 `./` 不能省略！**

### 你会看到：
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
  Alice public key: 8812363fe058d4d9... (800 bytes total)
  Alice secret key: 2bd75cb2602f8de8... (1632 bytes total)
✓ Keypair generated successfully

Step 2: Bob encapsulates (using Alice's public key)
---------------------------------------
  Ciphertext: 01cf47b957923268... (768 bytes total)
  Bob's shared secret: 046a60be641d441a588a018def92d4ec... (32 bytes total)
✓ Encapsulation successful

Step 3: Alice decapsulates (using her secret key)
---------------------------------------
  Alice's shared secret: 046a60be641d441a588a018def92d4ec... (32 bytes total)
✓ Decapsulation successful

Step 4: Verify shared secrets match
---------------------------------------
✅ SUCCESS: Shared secrets match!
   Shared secret (full): 046a60be641d441a588a018def92d4ecb17dea1f3e5599c5067b8d616a15b7a6

======================================================================
✅ All Kyber KEM tests passed!
======================================================================
```

**🎉 看到这个输出说明程序运行成功！**

---

## 🚀 更快的方法：使用 VSCode 任务

### 方法 A：使用快捷键

1. **按 `Ctrl + Shift + B`**
   - 功能：编译程序（等同于 `make`）

2. **按 `Ctrl + Shift + P`**
   - 输入：`Tasks: Run Task`
   - 选择：**"🧪 编译并测试 (make test)"**
   - 功能：自动编译+运行

### 方法 B：使用菜单

1. 点击顶部菜单：**Terminal → Run Task...**
2. 选择任务：
   ```
   🧪 编译并测试 (make test)     ← 一键编译+测试
   ▶️  运行 test_kyber           ← 只运行程序
   🔨 编译程序 (make)            ← 只编译
   ℹ️  显示配置信息              ← 查看环境
   🧹 清理编译文件               ← 删除编译产物
   ```

### 任务运行的样子：

当你选择 "🧪 编译并测试" 后，终端会自动执行：
```
> Executing task: make test <

Compiling src/kyber_kem.c...
Building test_kyber...
✓ Built: test_kyber

Running Kyber KEM test...
==============================
./test_kyber

[测试输出...]

✅ All Kyber KEM tests passed!

Terminal will be reused by tasks, press any key to close it.
```

---

## 🐛 调试功能（可选）

### 如何使用断点调试：

1. **打开源文件**
   - 在左侧文件树中，点击 `tests/test_kyber.c`

2. **设置断点**
   - 在代码行号左侧点击，出现红点 🔴
   - 比如在第 30 行 `printf("Step 1...")` 处设置断点

3. **启动调试**
   - 按 `F5` 键
   - 或点击左侧边栏的 🐛 图标，然后点击绿色播放按钮

4. **调试控制**
   - `F5` - 继续执行到下一个断点
   - `F10` - 单步跳过（执行当前行，不进入函数）
   - `F11` - 单步进入（进入函数内部）
   - `Shift + F11` - 单步跳出（退出当前函数）
   - `Shift + F5` - 停止调试

5. **查看变量**
   - 左侧会显示 "变量" 面板
   - 可以看到 `public_key`, `secret_key` 等变量的值
   - 鼠标悬停在变量上也能看到值

---

## ❓ 常见问题排查

### ❌ 问题 1：命令找不到

**现象**：
```
bash: make: command not found
```

**原因**：不在 WSL 终端中

**解决**：
1. 检查终端类型（右上角应显示 "wsl"）
2. 如果不是，点击 `˅` 切换到 "Ubuntu (WSL)"

---

### ❌ 问题 2：找不到 liboqs

**现象**：
```
error while loading shared libraries: liboqs.so: cannot open shared object file
```

**解决方法 1**（临时）：
```bash
export LD_LIBRARY_PATH=$HOME/_oqs/lib:$LD_LIBRARY_PATH
./test_kyber
```

**解决方法 2**（检查安装）：
```bash
ls -la ~/_oqs/lib/liboqs.so*
```

应该看到：
```
liboqs.so -> liboqs.so.6
liboqs.so.0.11.0
liboqs.so.6 -> liboqs.so.0.11.0
```

---

### ❌ 问题 3：权限问题

**现象**：
```
bash: ./test_kyber: Permission denied
```

**解决**：
```bash
chmod +x test_kyber
./test_kyber
```

---

## 📝 命令速查表

| 命令 | 功能 | 说明 |
|------|------|------|
| `make info` | 显示配置 | 查看 liboqs 路径 |
| `make` | 编译 | 编译所有源文件 |
| `make clean` | 清理 | 删除编译产物 |
| `make test` | 测试 | 编译+运行测试 |
| `./test_kyber` | 运行 | 直接运行程序 |
| `ls` | 列出文件 | 查看当前目录 |
| `pwd` | 显示路径 | 查看当前目录完整路径 |
| `cd ~` | 回家目录 | 返回用户主目录 |

---

## 🎉 完成！

如果你看到了 "✅ All Kyber KEM tests passed!"，恭喜你成功运行了第一个后量子密码程序！

### 下一步可以：

1. **修改代码做实验**
   - 打开 `tests/test_kyber.c`
   - 修改打印内容或测试逻辑
   - 保存后重新 `make` 和运行

2. **切换到 Kyber768**
   - 编辑 `Makefile`
   - 取消注释 `# CFLAGS += -DUSE_KYBER768`
   - 重新编译测试

3. **开始实现 PQ-Ntor**
   - 参考 Python 版本 `../python/simple_pq_ntor.py`
   - 实现 `src/pq_ntor.c`

---

**需要帮助？** 查看：
- [快速开始.md](快速开始.md)
- [VSCode运行指南.md](VSCode运行指南.md)
- [README.md](README.md)
