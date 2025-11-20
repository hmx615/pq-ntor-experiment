# 第一步：本地 Skyfield 环境配置指南

**日期**: 2025-11-12
**目标**: 在本地环境配置Skyfield，为SAGIN开发做准备
**预计耗时**: 30分钟 - 1小时
**状态**: ⏳ 进行中

---

## 📋 开始前确认

### 您当前应该在哪里？

✅ **推荐环境**（选一个）：
- Windows WSL2 (Ubuntu 22.04)
- Linux虚拟机 (Ubuntu/Debian)
- macOS (Intel 或 Apple Silicon)
- 原生Linux系统

❌ **不推荐**（现阶段）：
- 飞腾派（留待后期移植）

### 为什么先在本地？

- ⚡ 开发速度快3-5倍
- 🛠️ 调试工具完善
- 🟢 无硬件风险
- ✅ Skyfield完全跨平台

---

## 🚀 Step 1: 安装基础依赖

### 1.1 确认Python版本

```bash
python3 --version
```

**要求**: Python 3.8 或更高版本

**如果版本过低**：
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-pip

# macOS (使用Homebrew)
brew install python@3.10
```

---

### 1.2 安装系统依赖

```bash
# Ubuntu/Debian/WSL2
sudo apt update
sudo apt install -y \
    build-essential \
    python3-pip \
    python3-dev \
    git \
    curl \
    wget

# macOS
# (通常已经有这些工具，如果没有：)
xcode-select --install
brew install wget
```

---

### 1.3 安装Python依赖

```bash
# 升级pip
pip3 install --upgrade pip

# 安装Skyfield及相关库
pip3 install \
    skyfield \
    numpy \
    scipy \
    matplotlib \
    astropy \
    jplephem \
    sgp4
```

**预期输出**：
```
Successfully installed skyfield-1.48 numpy-1.26.2 ...
```

**预计耗时**: 2-5分钟（取决于网速）

---

## ✅ Step 2: 验证安装

### 2.1 创建测试脚本

在 `/home/ccc/pq-ntor-experiment/sagin-experiments/` 目录下创建测试文件：

```bash
cd /home/ccc/pq-ntor-experiment/sagin-experiments
```

创建 `test_skyfield_basic.py`:

```python
#!/usr/bin/env python3
"""
Skyfield基础功能测试
验证安装是否成功
"""

import sys
from skyfield.api import load, EarthSatellite, wgs84

def test_imports():
    """测试1: 验证所有必要模块能否导入"""
    print("=" * 60)
    print("测试1: 导入模块")
    print("=" * 60)

    try:
        from skyfield.api import load, EarthSatellite, wgs84
        from skyfield import almanac
        import numpy as np
        import matplotlib
        print("✓ 所有必要模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_timescale():
    """测试2: 验证时间尺度加载"""
    print("\n" + "=" * 60)
    print("测试2: 加载时间尺度")
    print("=" * 60)

    try:
        ts = load.timescale()
        t = ts.now()
        print(f"✓ 时间尺度加载成功")
        print(f"  当前UTC时间: {t.utc_iso()}")
        return True
    except Exception as e:
        print(f"✗ 时间尺度加载失败: {e}")
        return False

def test_iss_position():
    """测试3: 计算国际空间站位置"""
    print("\n" + "=" * 60)
    print("测试3: 计算ISS位置")
    print("=" * 60)

    try:
        # 国际空间站的TLE（示例，可能已过时）
        line1 = '1 25544U 98067A   25315.50000000  .00016717  00000-0  10270-3 0  9005'
        line2 = '2 25544  51.6461 339.8014 0001449  89.4721 270.6484 15.54225995427869'

        ts = load.timescale()
        iss = EarthSatellite(line1, line2, 'ISS', ts)

        # 计算当前位置
        t = ts.now()
        geocentric = iss.at(t)
        subpoint = geocentric.subpoint()

        print(f"✓ ISS位置计算成功")
        print(f"  纬度:   {subpoint.latitude.degrees:8.3f}°")
        print(f"  经度:   {subpoint.longitude.degrees:8.3f}°")
        print(f"  高度:   {subpoint.elevation.km:8.1f} km")

        # 计算速度
        velocity = geocentric.velocity.km_per_s
        import numpy as np
        speed = np.linalg.norm(velocity)
        print(f"  速度:   {speed:8.2f} km/s")

        return True
    except Exception as e:
        print(f"✗ ISS位置计算失败: {e}")
        return False

def test_ground_station():
    """测试4: 地面站位置和可见性"""
    print("\n" + "=" * 60)
    print("测试4: 地面站位置")
    print("=" * 60)

    try:
        # 创建北京地面站
        beijing = wgs84.latlon(39.9, 116.4, elevation_m=50)

        ts = load.timescale()
        t = ts.now()

        # 计算地面站在地心坐标系的位置
        gs_geocentric = beijing.at(t)

        print(f"✓ 地面站位置创建成功")
        print(f"  位置: 北京")
        print(f"  纬度: 39.9°N")
        print(f"  经度: 116.4°E")
        print(f"  海拔: 50 m")

        return True
    except Exception as e:
        print(f"✗ 地面站创建失败: {e}")
        return False

def test_visibility():
    """测试5: 卫星可见性判断"""
    print("\n" + "=" * 60)
    print("测试5: 卫星可见性判断")
    print("=" * 60)

    try:
        # ISS TLE
        line1 = '1 25544U 98067A   25315.50000000  .00016717  00000-0  10270-3 0  9005'
        line2 = '2 25544  51.6461 339.8014 0001449  89.4721 270.6484 15.54225995427869'

        ts = load.timescale()
        iss = EarthSatellite(line1, line2, 'ISS', ts)

        # 北京地面站
        beijing = wgs84.latlon(39.9, 116.4, elevation_m=50)

        # 当前时间
        t = ts.now()

        # 从地面站观测卫星
        difference = iss - beijing
        topocentric = difference.at(t)
        alt, az, distance = topocentric.altaz()

        visible = alt.degrees > 10  # 仰角>10度认为可见

        print(f"✓ 可见性计算成功")
        print(f"  仰角:   {alt.degrees:8.2f}°")
        print(f"  方位角: {az.degrees:8.2f}°")
        print(f"  距离:   {distance.km:8.1f} km")
        print(f"  可见:   {'是' if visible else '否'} (仰角{'>' if visible else '<'}10°)")

        return True
    except Exception as e:
        print(f"✗ 可见性计算失败: {e}")
        return False

def test_distance_calculation():
    """测试6: 两点距离计算"""
    print("\n" + "=" * 60)
    print("测试6: 距离计算")
    print("=" * 60)

    try:
        # 两个卫星的TLE（模拟）
        line1_sat1 = '1 44713U 19074A   25315.50000000  .00001234  00000-0  12345-4 0  9999'
        line2_sat1 = '2 44713  53.0542 123.4567 0001234  90.1234 269.8765 15.05123456123456'

        line1_sat2 = '1 44714U 19074B   25315.50000000  .00001234  00000-0  12345-4 0  9999'
        line2_sat2 = '2 44714  53.0542 133.4567 0001234  90.1234 269.8765 15.05123456123456'

        ts = load.timescale()
        sat1 = EarthSatellite(line1_sat1, line2_sat1, 'SAT-1', ts)
        sat2 = EarthSatellite(line1_sat2, line2_sat2, 'SAT-2', ts)

        t = ts.now()

        # 计算距离
        difference = sat1 - sat2
        distance = difference.at(t).distance().km

        # 计算传播延迟（光速 = 300,000 km/s）
        delay_ms = (distance / 300000.0) * 1000

        print(f"✓ 距离计算成功")
        print(f"  星间距离: {distance:8.1f} km")
        print(f"  光速延迟: {delay_ms:8.2f} ms")

        return True
    except Exception as e:
        print(f"✗ 距离计算失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "  Skyfield 基础功能测试套件".center(58) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60 + "\n")

    tests = [
        ("模块导入", test_imports),
        ("时间尺度", test_timescale),
        ("ISS位置计算", test_iss_position),
        ("地面站位置", test_ground_station),
        ("可见性判断", test_visibility),
        ("距离计算", test_distance_calculation),
    ]

    results = []
    for name, test_func in tests:
        try:
            results.append((name, test_func()))
        except Exception as e:
            print(f"\n✗ 测试 '{name}' 异常: {e}")
            results.append((name, False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status:8s} - {name}")

    print("=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)

    if passed == total:
        print("\n🎉 恭喜！Skyfield环境配置成功！")
        print("\n下一步:")
        print("  1. 查看工作列表: Skyfield-SAGIN实施工作列表.md")
        print("  2. 继续Task 1.2: 创建SAGIN拓扑配置文件")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查环境配置")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

---

### 2.2 运行测试脚本

```bash
# 确保在正确目录
cd /home/ccc/pq-ntor-experiment/sagin-experiments

# 添加执行权限
chmod +x test_skyfield_basic.py

# 运行测试
python3 test_skyfield_basic.py
```

**预期输出**：

```
████████████████████████████████████████████████████████████
█                                                          █
█          Skyfield 基础功能测试套件                       █
█                                                          █
████████████████████████████████████████████████████████████

============================================================
测试1: 导入模块
============================================================
✓ 所有必要模块导入成功

============================================================
测试2: 加载时间尺度
============================================================
✓ 时间尺度加载成功
  当前UTC时间: 2025-11-12T08:30:45Z

============================================================
测试3: 计算ISS位置
============================================================
✓ ISS位置计算成功
  纬度:      23.456°
  经度:     -87.123°
  高度:     418.5 km
  速度:       7.66 km/s

============================================================
测试4: 地面站位置
============================================================
✓ 地面站位置创建成功
  位置: 北京
  纬度: 39.9°N
  经度: 116.4°E
  海拔: 50 m

============================================================
测试5: 卫星可见性判断
============================================================
✓ 可见性计算成功
  仰角:      45.23°
  方位角:   125.67°
  距离:     567.8 km
  可见:   是 (仰角>10°)

============================================================
测试6: 距离计算
============================================================
✓ 距离计算成功
  星间距离:  3245.6 km
  光速延迟:    10.82 ms

============================================================
测试结果汇总
============================================================
  ✓ 通过   - 模块导入
  ✓ 通过   - 时间尺度
  ✓ 通过   - ISS位置计算
  ✓ 通过   - 地面站位置
  ✓ 通过   - 可见性判断
  ✓ 通过   - 距离计算
============================================================
总计: 6/6 测试通过
============================================================

🎉 恭喜！Skyfield环境配置成功！

下一步:
  1. 查看工作列表: Skyfield-SAGIN实施工作列表.md
  2. 继续Task 1.2: 创建SAGIN拓扑配置文件
```

---

## 🔍 Step 3: 故障排除

### 问题1: pip安装失败

**错误信息**:
```
ERROR: Could not find a version that satisfies the requirement skyfield
```

**解决方案**:
```bash
# 升级pip
pip3 install --upgrade pip setuptools wheel

# 使用清华镜像加速
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    skyfield numpy scipy matplotlib astropy
```

---

### 问题2: 权限错误

**错误信息**:
```
PermissionError: [Errno 13] Permission denied
```

**解决方案**:
```bash
# 使用--user参数安装到用户目录
pip3 install --user skyfield numpy scipy matplotlib astropy

# 或者使用虚拟环境（推荐）
python3 -m venv ~/skyfield-env
source ~/skyfield-env/bin/activate
pip3 install skyfield numpy scipy matplotlib astropy
```

---

### 问题3: 网络连接失败

**错误信息**:
```
URLError: <urlopen error [Errno -3] Temporary failure in name resolution>
```

**说明**: Skyfield在首次运行时会下载星历表数据（约20MB）

**解决方案**:
```bash
# 检查网络连接
ping 8.8.8.8

# 如果在中国大陆，使用代理或手动下载数据文件
# 参考: https://rhodesmill.org/skyfield/installation.html#downloading-timescale-files
```

---

### 问题4: 测试脚本某些项失败

**如果只有个别测试失败**：

- **测试5失败** (可见性): ISS可能真的不可见，这是正常的
- **测试6失败** (距离计算): TLE数据可能过时，不影响功能

**只要测试1-4通过，就可以继续下一步**

---

## ✅ Step 4: 验证完成

### 完成标准

- ✅ Python 3.8+ 已安装
- ✅ Skyfield及依赖库安装成功
- ✅ 至少4个测试通过（测试1-4）
- ✅ 能正确计算卫星位置
- ✅ 能正确计算距离和延迟

### 环境信息记录

```bash
# 记录Python版本
python3 --version > skyfield_env_info.txt

# 记录安装的包版本
pip3 list | grep -E "(skyfield|numpy|scipy|matplotlib)" >> skyfield_env_info.txt

# 记录操作系统
uname -a >> skyfield_env_info.txt

cat skyfield_env_info.txt
```

---

## 📝 下一步行动

### 立即可做（如果测试全部通过）

```bash
# 查看下一步任务
cat Skyfield-SAGIN实施工作列表.md | grep -A 20 "Task 1.2"
```

**Task 1.2**: 创建SAGIN拓扑配置文件
- 定义2颗卫星（LEO + MEO）
- 定义2架飞机
- 定义3个地面站
- 配置链路约束参数

**预计耗时**: 30分钟

---

### 本周计划（参考）

```
本周目标: 完成本地开发环境和基础功能

✅ Day 1 (今天):
   ├─ Step 1: Skyfield环境配置 (1h) ← 当前步骤
   ├─ Step 2: 创建拓扑配置文件 (0.5h)
   └─ Step 3: 开始开发轨道仿真器 (3h)

⏳ Day 2:
   ├─ 完成轨道仿真器核心功能 (4h)
   └─ 单元测试 (2h)

⏳ Day 3-4:
   └─ Directory Server扩展 + Client路径指定

⏳ Day 5:
   └─ 集成测试
```

---

## 📞 需要帮助？

### 如果遇到问题

1. **查看详细文档**: `代码重构评估与本地验证方案.md`
2. **查看工作列表**: `Skyfield-SAGIN实施工作列表.md`
3. **联系或反馈**: 提供错误信息和环境信息

### 提供信息时包括

```bash
# 收集诊断信息
echo "=== Python版本 ===" > diagnostic.txt
python3 --version >> diagnostic.txt

echo -e "\n=== Pip版本 ===" >> diagnostic.txt
pip3 --version >> diagnostic.txt

echo -e "\n=== 安装的包 ===" >> diagnostic.txt
pip3 list >> diagnostic.txt

echo -e "\n=== 操作系统 ===" >> diagnostic.txt
uname -a >> diagnostic.txt

echo -e "\n=== 测试脚本输出 ===" >> diagnostic.txt
python3 test_skyfield_basic.py 2>&1 >> diagnostic.txt

cat diagnostic.txt
```

---

## 🎯 关键检查点

在继续下一步之前，确认：

- [ ] Python 3.8+ 已安装并能正常运行
- [ ] pip3 能正常安装包
- [ ] Skyfield库导入无错误
- [ ] 能计算ISS位置（测试3通过）
- [ ] 能创建地面站（测试4通过）
- [ ] 测试脚本至少4/6通过

**如果所有检查点都通过** ✅
→ 恭喜！可以继续Task 1.2

**如果有检查点失败** ⚠️
→ 查看故障排除章节，或提供诊断信息

---

**创建日期**: 2025-11-12
**预计完成**: 30分钟 - 1小时
**当前状态**: ⏳ 等待用户执行

**祝配置顺利！遇到问题随时询问。** 🚀
