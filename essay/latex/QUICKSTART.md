# 快速开始指南

**5分钟搞定 LaTeX 编译**

---

## 步骤1: 安装 LaTeX（首次使用）

### Ubuntu / Debian / WSL（推荐）

```bash
# 轻量级安装（约 500MB，5-10分钟）
sudo apt-get update
sudo apt-get install texlive-latex-base texlive-latex-extra \
    texlive-fonts-recommended texlive-fonts-extra

# 或完整安装（约 5GB，如果你有空间和时间）
sudo apt-get install texlive-full
```

### 验证安装

```bash
pdflatex --version
bibtex --version
```

如果显示版本信息，说明安装成功！

---

## 步骤2: 编译论文

```bash
# 进入 LaTeX 目录
cd /home/ccc/pq-ntor-experiment/essay/latex

# 完整编译（推荐）
./compile.sh full

# 如果上面报错，尝试快速编译
./compile.sh quick
```

**预计编译时间**: 30秒 - 2分钟

---

## 步骤3: 查看 PDF

```bash
# 检查 PDF 是否生成
ls -lh main.pdf

# 在 WSL 中用 Windows 打开
explorer.exe main.pdf

# 或复制到 Windows 目录
cp main.pdf /mnt/c/Users/你的用户名/Desktop/
```

---

## 🎉 成功了吗？

如果你看到了 PDF，恭喜！你的 LaTeX 环境已经就绪。

### PDF 应该包含的内容：

- ✅ 标题和作者信息
- ✅ Abstract（摘要）
- ✅ Section 1: Introduction（占位符）
- ✅ Section 5: Evaluation（完整内容，包含表格）
  - Table 1: Hardware Configuration
  - Table 2: Software Components
  - Table 3: Topology Categories
  - Table 4: 12种拓扑详细规格
  - Table 5: PQ-NTOR 性能数据
  - Table 6: 与 Berger 论文对比
- ✅ 其他章节占位符
- ✅ 参考文献

---

## 常见问题

### Q1: `pdflatex: command not found`

**A**: LaTeX 未安装，重新执行步骤1

### Q2: 编译报错 "Emergency stop"

**A**: 检查 `main.log` 文件查看详细错误：

```bash
tail -50 main.log
```

通常是某个 LaTeX 包缺失，安装缺失的包：

```bash
sudo apt-get install texlive-latex-extra
```

### Q3: 参考文献不显示

**A**: 需要完整编译（不要用 quick 模式）：

```bash
./compile.sh full
```

### Q4: 表格显示不正常

**A**: 确保安装了 `booktabs` 包：

```bash
sudo apt-get install texlive-latex-recommended
```

---

## 下一步

### 1. 修改内容

直接编辑 `.tex` 文件：

```bash
# 编辑 Section 5
nano sections/evaluation.tex

# 或使用你喜欢的编辑器
code sections/evaluation.tex
```

### 2. 重新编译

```bash
./compile.sh quick  # 快速预览
```

### 3. 查看效果

```bash
explorer.exe main.pdf
```

---

## 🔥 Pro Tips

### 快速开发工作流

```bash
# 1. 编辑文件
nano sections/evaluation.tex

# 2. 快速编译
./compile.sh quick

# 3. 查看 PDF
explorer.exe main.pdf

# 重复 1-3 直到满意
```

### 最终提交前

```bash
# 完整编译确保所有引用正确
./compile.sh full

# 清理临时文件
./compile.sh clean
```

---

**Have Fun Writing! 🚀**
