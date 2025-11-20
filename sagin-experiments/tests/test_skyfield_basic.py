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
