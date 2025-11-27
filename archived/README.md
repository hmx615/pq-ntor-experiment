# 归档文件说明

**整理时间**: 2025-11-28
**整理原因**: 主目录文件过多(51个)，影响项目导航

---

## 📁 归档目录结构

```
archived/
├── debug-scripts/      # 调试和临时修复脚本
├── phytium-scripts/    # 飞腾派部署相关脚本
├── work-logs/          # 历史工作日志
├── old-docs/           # 旧版本文档
└── README.md           # 本文件
```

---

## 🔧 debug-scripts/ (23个文件)

**用途**: 开发过程中的调试、修复、测试脚本

### 调试工具
- `check_directory_server.py` - 检查目录服务器状态
- `check_log.py` - 日志检查工具
- `check_original_relay.py` - 验证原始relay实现
- `check_results_now.py` - 快速查看实验结果

### 调试和测试脚本
- `debug_12topo_test.py` - 12拓扑测试调试 (v1)
- `debug_12topo_test_v2.py` - 12拓扑测试调试 (v2)
- `diagnose_failure.py` - 故障诊断工具
- `quick_test.py` - 快速测试脚本
- `simple_run_12topo.py` - 简化版12拓扑运行

### 修复脚本
- `apply_local_mode_fix.py` - 应用本地模式修复
- `fix_identity_check_final.py` - 修复身份检查
- `fix_include_path.py` - 修复include路径
- `fix_makefile_include.py` - 修复Makefile include
- `fix_makefile_relay_target.py` - 修复Makefile relay目标
- `fix_relay_registration.py` - 修复relay注册
- `fix_directory_for_local.patch` - 本地模式补丁

### 查找工具
- `find_identity_check.py` - 查找身份检查代码
- `find_liboqs.py` - 查找liboqs库
- `verify_liboqs.py` - 验证liboqs安装

### 手动操作脚本
- `manual_compile_relay.py` - 手动编译relay
- `manual_fix_pq_ntor.py` - 手动修复PQ-NTOR
- `recompile_all.py` - 重新编译所有组件
- `restore_and_fix_relay.py` - 恢复并修复relay
- `skip_identity_check.py` - 跳过身份检查

### Shell脚本
- `kill_processes.sh` - 清理测试进程
- `test_sagin_loop.sh` - SAGIN循环测试
- `运行真实SAGIN实验.sh` - 运行真实SAGIN实验

**状态**: ✅ 这些脚本已完成使命，保留用于参考和紧急修复

---

## 🖥️ phytium-scripts/ (8个文件)

**用途**: 飞腾派ARM硬件部署和远程操作脚本

### 部署和配置
- `setup_phytium.sh` - 飞腾派环境配置脚本
- `deploy_configs_env.py` - 部署配置和环境

### 远程操作
- `ssh_phytium.py` - SSH连接飞腾派工具
- `check_phytium_status.py` - 检查飞腾派状态
- `monitor_progress.py` - 监控实验进度

### 数据传输
- `download_phytium_data.py` - 从飞腾派下载数据

### 实验运行
- `run_12topo_on_phytium.py` - 在飞腾派上运行12拓扑测试
- `run_12topo_fixed.py` - 修正版12拓扑运行
- `run_benchmark_phytium.py` - 飞腾派性能基准测试

**状态**: ⏸️ 当前使用WSL本地测试，飞腾派部署暂缓，保留备用

---

## 📝 work-logs/ (5个文件)

**用途**: 历史工作日志和阶段性总结

### 工作日志
- `2025-11-10-工作完成确认.md` - 2025-11-10工作确认
- `README_2025-11-12工作总结.md` - 2025-11-12总结

### 技术文档
- `参数对比表.md` - SAGIN参数对比
- `实验结果100%问题分析与解决.md` - 100%成功率问题分析
- `SAGIN参数真实化修改说明.md` - 参数真实化说明

**状态**: 📚 历史参考价值，已有更新版本在主目录或子目录

---

## 📄 old-docs/ (1个文件)

**用途**: 过时或已被替代的文档

- `速率计算.docx` - Word版速率计算文档 (已有Markdown版本)

**状态**: 🗂️ 保留备份，不再更新

---

## ✅ 主目录保留文件 (9个)

经过整理后，主目录只保留核心文件：

### 核心文档 (7个.md)
- `README.md` - 项目主文档 ⭐
- `PHYTIUM_SETUP_README.md` - 飞腾派配置指南
- `SAGIN_PQ-NTOR实验设计方案.md` - PQ-NTOR实验设计
- `SAGIN_分布式实验设计方案.md` - 分布式实验设计
- `SAGIN_速率计算实现指南.md` - 速率计算指南
- `实验设计完成报告.md` - 实验完成报告
- `实验速率计算结果总结.md` - 速率计算结果

### 核心脚本 (2个.sh)
- `check_full_environment.sh` - 环境检测脚本 (常用)
- `push_to_github.sh` - Git推送脚本 (常用)

### 其他核心目录
- `c/` - C语言实现
- `sagin-experiments/` - SAGIN实验
- `essay/` - 论文工作区
- `scripts/` - 活跃脚本
- `results/` - 实验结果
- 等等...

---

## 🔍 如何找回文件

### 方法1: 直接访问归档目录

```bash
# 查看调试脚本
ls archived/debug-scripts/

# 查看飞腾派脚本
ls archived/phytium-scripts/

# 查看历史文档
ls archived/work-logs/
```

### 方法2: 搜索文件

```bash
# 搜索特定文件
find archived/ -name "check_phytium_status.py"

# 搜索包含关键词的文件
grep -r "关键词" archived/
```

### 方法3: 恢复到主目录

```bash
# 如果需要使用某个归档脚本
cp archived/phytium-scripts/ssh_phytium.py .

# 或者创建软链接
ln -s archived/phytium-scripts/ssh_phytium.py .
```

---

## 📊 整理统计

| 类别 | 归档前 | 归档后 | 减少 |
|------|--------|--------|------|
| 主目录文件 | 51个 | 9个 | **-82%** ✨ |
| Python脚本 | 31个 | 0个 | -100% |
| Shell脚本 | 6个 | 2个 | -67% |
| Markdown文档 | 12个 | 7个 | -42% |

---

## ⚠️ 重要提示

1. **不要删除归档目录**: 这些脚本可能在紧急情况下需要
2. **Git已追踪**: 所有文件都在Git历史中，可随时恢复
3. **定期备份**: 归档目录应包含在备份中

---

## 🔄 未来整理建议

当主目录再次变得混乱时，考虑：

1. 创建 `archived/YYYY-MM-DD/` 按日期归档
2. 将临时脚本移到 `tmp/` 目录
3. 将实验数据移到 `results/` 目录
4. 将文档移到 `docs/` 或 `essay/` 目录

---

**整理完成**: 2025-11-28
**整理工具**: Claude Code
**整理效果**: 主目录清爽，文件易查找 ✅
