# 归档文件快速参考

**更新时间**: 2025-11-28

---

## 🔍 常用归档文件快速查找

### 需要调试时

```bash
# SSH连接飞腾派
archived/phytium-scripts/ssh_phytium.py

# 检查飞腾派状态
archived/phytium-scripts/check_phytium_status.py

# 快速测试
archived/debug-scripts/quick_test.py

# 诊断失败原因
archived/debug-scripts/diagnose_failure.py
```

### 需要运行飞腾派实验

```bash
# 在飞腾派上运行12拓扑
archived/phytium-scripts/run_12topo_on_phytium.py

# 飞腾派环境配置
archived/phytium-scripts/setup_phytium.sh

# 下载实验数据
archived/phytium-scripts/download_phytium_data.py
```

### 需要查看历史

```bash
# 2025-11-10工作记录
archived/work-logs/2025-11-10-工作完成确认.md

# 参数对比
archived/work-logs/参数对比表.md

# 问题分析
archived/work-logs/实验结果100%问题分析与解决.md
```

---

## 📋 按功能分类

### 🔧 环境和编译修复
- `fix_include_path.py` - 修复include路径
- `fix_makefile_*.py` - 修复Makefile
- `recompile_all.py` - 重新编译
- `verify_liboqs.py` - 验证liboqs

### 🐛 调试工具
- `check_*.py` - 各种检查工具
- `debug_*.py` - 调试脚本
- `diagnose_*.py` - 诊断工具

### 🖥️ 飞腾派操作
- `ssh_phytium.py` - SSH连接
- `setup_phytium.sh` - 环境配置
- `run_*_phytium.py` - 远程运行
- `download_phytium_data.py` - 数据下载

### 📊 测试运行
- `quick_test.py` - 快速测试
- `simple_run_12topo.py` - 简单运行
- `test_sagin_loop.sh` - 循环测试

---

## 🚀 一键恢复常用脚本

```bash
# 恢复飞腾派工具集
cp archived/phytium-scripts/{ssh_phytium.py,check_phytium_status.py,download_phytium_data.py} .

# 恢复调试工具集
cp archived/debug-scripts/{quick_test.py,diagnose_failure.py,check_log.py} .

# 恢复编译修复工具
cp archived/debug-scripts/{recompile_all.py,verify_liboqs.py} .
```

---

## 📁 目录结构速查

```
archived/
├── debug-scripts/          23个文件
│   ├── 检查工具 (4个)
│   ├── 测试脚本 (5个)
│   ├── 修复脚本 (7个)
│   ├── 查找工具 (3个)
│   └── 手动操作 (4个)
│
├── phytium-scripts/        8个文件
│   ├── ssh_phytium.py
│   ├── setup_phytium.sh
│   └── run_*_phytium.py
│
├── work-logs/              5个文件
│   └── 历史工作日志
│
└── old-docs/               1个文件
    └── Word文档
```

---

**提示**: 查看完整说明请阅读 `archived/README.md`
