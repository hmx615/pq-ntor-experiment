# NOMA协作链路补全说明

**文档版本**: v1.0
**创建时间**: 2025-11-20
**适用系统**: SAGIN NOMA 6+1分布式展示系统

---

## 🎯 概述

本文档详细说明为什么需要补全NOMA协作链路、补全了哪些拓扑、技术实现细节、以及NOMA协作原理。

---

## 🔍 问题发现

### 原始状态

**检查时间**: 2025-11-20

**发现**: 根据文档《12种NOMA网络拓扑定义.md》，**所有6个下行拓扑（7-12）都应该有NOMA组内协作链路**，但代码中只实现了拓扑7。

**缺失情况**:

| 拓扑 | 名称 | 协作链路状态 | 影响 |
|------|------|--------------|------|
| 拓扑7 | Z1 Down | ✅ **已实现** | S1→S2 协作链路正常 |
| 拓扑8 | Z2 Down | ❌ **缺失** | 无法展示NOMA协作 |
| 拓扑9 | Z3 Down | ⚠️ **不需要** | 只有单终端T |
| 拓扑10 | Z4 Down | ⚠️ **不需要** | 单向转发，非NOMA |
| 拓扑11 | Z5 Down | ❌ **缺失** | 无法展示NOMA协作 |
| 拓扑12 | Z6 Down | ❌ **缺失** | 无法展示NOMA协作 |

**统计**:
- 应有协作链路的拓扑: 4个 (7, 8, 11, 12)
- 已实现: 1个 (拓扑7)
- 需补全: 3个 (拓扑8, 11, 12)

---

## 📚 NOMA协作原理

### 什么是NOMA？

**NOMA (Non-Orthogonal Multiple Access)**: 非正交多址接入

**核心思想**:
- 在**同一频段、同一时间**服务多个用户
- 通过**功率域**区分不同用户
- 使用**SIC (Successive Interference Cancellation)** 串行干扰消除技术

**与传统OMA的区别**:

| 技术 | 频段使用 | 同时用户数 | 频谱效率 |
|------|----------|------------|----------|
| **OMA** | 正交分配 | 1个 | 低 |
| **NOMA** | 重叠使用 | 多个 | **高** |

### NOMA功率分配

**原则**: 信道质量差的用户分配更高功率

```
卫星总功率 P

近端用户 (高RSSI): α₁·P  (α₁ < 0.5, 例如0.3)
远端用户 (低RSSI): α₂·P  (α₂ > 0.5, 例如0.7)

α₁ + α₂ = 1
```

**为什么这样分配？**
- 远端用户信道质量差，需要更高功率补偿
- 近端用户信道质量好，低功率也能正常接收

### SIC 串行干扰消除

**下行通信场景**:

```
卫星广播信号: x = α₁·s₁ + α₂·s₂

近端用户接收:
  y₁ = h₁·(α₁·s₁ + α₂·s₂) + n₁
  步骤1: 先解码 s₂ (高功率信号)
  步骤2: 消除 s₂ 的干扰
  步骤3: 解码 s₁ (自己的信号)

远端用户接收:
  y₂ = h₂·(α₁·s₁ + α₂·s₂) + n₂
  步骤1: 直接解码 s₂ (功率高)
  步骤2: 将 s₁ 视为噪声
```

### 协作链路的作用

**问题**: 远端用户信道质量差，即使分配高功率也可能解码失败

**解决方案**: 近端用户帮助远端用户解码

**协作过程**:

```
步骤1: 卫星广播 → 近端用户和远端用户都接收

步骤2: 近端用户
  - 解码出 s₂ (远端用户的数据)
  - 通过协作链路转发给远端用户

步骤3: 远端用户
  - 结合直接接收的信号
  - 以及近端转发的信号
  - 提高解码成功率
```

**协作链路特点**:
- 🟣 紫色虚线显示
- 单向: 近端 → 远端
- 慢速动画 (2.0秒)
- 辅助性质，非主要数据通道

---

## 🔧 补全的协作链路

### 拓扑7: Z1 Down (原有)

**链路配置**:
```javascript
7: [
    { source: 'SAT', target: 'S1', rssi: 'high', label: '高RSSI天基下行' },
    { source: 'SAT', target: 'S2', rssi: 'low', label: '低RSSI天基下行' },
    { source: 'S1', target: 'S2', rssi: 'coop', label: '协作链路' }  // ✅ 原有
]
```

**网络拓扑**:
```
        [SAT 卫星]
         ↓  ↓
        高  低
         ↓  ↓
        S1─→S2
        近端 远端
          协作
```

**NOMA分组**: {<S1 (近端), S2 (远端)>}

**数据流向**:
1. SAT → S1 (高RSSI, 低功率)
2. SAT → S2 (低RSSI, 高功率)
3. S1 → S2 (协作转发)

---

### 拓扑8: Z2 Down (新增) ⭐

**问题**: 原配置缺少协作链路，且RSSI标记错误

**原配置** (错误):
```javascript
8: [
    { source: 'SAT', target: 'SR', rssi: 'high', label: '高RSSI天基下行' },
    { source: 'SR', target: 'S1', rssi: 'high', label: '空/地链路' },      // ❌ 都是high
    { source: 'SR', target: 'S2', rssi: 'high', label: '空/地链路' }       // ❌ 应该是low
    // ❌ 缺少 S1→S2 协作链路
]
```

**修正后配置**:
```javascript
8: [
    { source: 'SAT', target: 'SR', rssi: 'high', label: '高RSSI天基下行' },
    { source: 'SR', target: 'S1', rssi: 'high', label: '高RSSI空/地' },    // ✅ 高RSSI
    { source: 'SR', target: 'S2', rssi: 'low', label: '低RSSI空/地' },     // ✅ 修正为low
    { source: 'S1', target: 'S2', rssi: 'coop', label: 'NOMA协作链路' }    // ✅ 新增协作
]
```

**网络拓扑**:
```
        [SAT 卫星]
            ↓
          [SR 无人机]
         ↓      ↓
        高      低
         ↓      ↓
        S1 ───→ S2
        近端   远端
            协作
```

**NOMA分组**: {<S1 (近端), S2 (远端)>}

**修正说明**:
1. SR→S2 的RSSI从 `high` 改为 `low` (远端用户)
2. 添加 S1→S2 协作链路 (紫色虚线)
3. 更新标签为 "NOMA协作链路"

**数据流向**:
1. SAT → SR (天基下行)
2. SR → S1 (高RSSI, 近端)
3. SR → S2 (低RSSI, 远端)
4. S1 → S2 (协作转发) ⭐ 新增

---

### 拓扑11: Z5 Down (新增) ⭐

**问题**: 原配置缺少协作链路，且RSSI标记不完整

**原配置** (错误):
```javascript
11: [
    { source: 'SAT', target: 'SR', rssi: 'high', label: '高RSSI天基下行' },
    { source: 'SR', target: 'S1R2', rssi: 'high', label: '空/空链路' },
    { source: 'SR', target: 'S1', rssi: 'high', label: '空/地链路' },      // ✅ 近端
    { source: 'S1R2', target: 'S2', rssi: 'high', label: '空/地链路' }     // ❌ 应该是low
    // ❌ 缺少 S1→S2 协作链路
]
```

**修正后配置**:
```javascript
11: [
    { source: 'SAT', target: 'SR', rssi: 'high', label: '高RSSI天基下行' },
    { source: 'SR', target: 'S1R2', rssi: 'high', label: '空/空链路' },
    { source: 'SR', target: 'S1', rssi: 'high', label: '高RSSI空/地' },     // ✅ 近端
    { source: 'S1R2', target: 'S2', rssi: 'low', label: '低RSSI空/地' },    // ✅ 修正为low
    { source: 'S1', target: 'S2', rssi: 'coop', label: 'NOMA协作链路' }     // ✅ 新增协作
]
```

**网络拓扑**:
```
        [SAT 卫星]
            ↓
          [SR 无人机]
         ↓      ↓
       S1R2     S1
         ↓      ↓
        低      高
         ↓      ↓
        S2 ←─── S1
        远端    近端
            协作
```

**NOMA分组**: {<S1 (近端), S2 (远端)>}

**修正说明**:
1. S1R2→S2 的RSSI从 `high` 改为 `low` (远端用户)
2. 添加 S1→S2 协作链路 (紫色虚线)
3. 体现双路径下行: SR→S1 (直连), SR→S1R2→S2 (中继)

**数据流向**:
1. SAT → SR (天基下行)
2. SR → S1R2 (空/空链路)
3. SR → S1 (高RSSI, 近端)
4. S1R2 → S2 (低RSSI, 远端)
5. S1 → S2 (协作转发) ⭐ 新增

---

### 拓扑12: Z6 Down (新增) ⭐

**问题**: 原配置缺少协作链路，且RSSI标记不完整

**原配置** (错误):
```javascript
12: [
    { source: 'SAT', target: 'SR', rssi: 'high', label: '高RSSI天基下行' },
    { source: 'SR', target: 'S1R2', rssi: 'high', label: '空/空链路' },
    { source: 'S1R2', target: 'T', rssi: 'high', label: '空/地链路' },
    { source: 'SR', target: 'S1', rssi: 'high', label: '空/地链路' },      // ✅ 近端
    { source: 'SR', target: 'S2', rssi: 'high', label: '空/地链路' }       // ❌ 应该是low
    // ❌ 缺少 S1→S2 协作链路
]
```

**修正后配置**:
```javascript
12: [
    { source: 'SAT', target: 'SR', rssi: 'high', label: '高RSSI天基下行' },
    { source: 'SR', target: 'S1R2', rssi: 'high', label: '空/空链路' },
    { source: 'S1R2', target: 'T', rssi: 'high', label: '空/地链路' },
    { source: 'SR', target: 'S1', rssi: 'high', label: '高RSSI空/地' },     // ✅ 近端
    { source: 'SR', target: 'S2', rssi: 'low', label: '低RSSI空/地' },      // ✅ 修正为low
    { source: 'S1', target: 'S2', rssi: 'coop', label: 'NOMA协作链路' }     // ✅ 新增协作
]
```

**网络拓扑**:
```
        [SAT 卫星]
            ↓
          [SR 无人机]
        ↙  ↓  ↘
     S1R2  S1  S2
       ↓   ↓   ↓
       T  高  低
           ↓   ↓
          S1 → S2
          近端 远端
              协作
```

**NOMA分组**: {<S1 (近端), S2 (远端)>}

**修正说明**:
1. SR→S2 的RSSI从 `high` 改为 `low` (远端用户)
2. 添加 S1→S2 协作链路 (紫色虚线)
3. 多点下行: SR同时服务S1R2/S1/S2三个终端

**数据流向**:
1. SAT → SR (天基下行)
2. SR → S1R2 → T (中继到T)
3. SR → S1 (高RSSI, 近端)
4. SR → S2 (低RSSI, 远端)
5. S1 → S2 (协作转发) ⭐ 新增

---

## 📊 补全统计

### 修改前后对比

| 拓扑 | 修改前链路数 | 修改后链路数 | 新增 | 修正 |
|------|-------------|-------------|------|------|
| 拓扑7 | 3 | 3 | 0 | 0 |
| **拓扑8** | 3 | **4** | +1协作 | RSSI修正 |
| 拓扑9 | 2 | 2 | 0 | 0 |
| 拓扑10 | 3 | 3 | 0 | 0 |
| **拓扑11** | 4 | **5** | +1协作 | RSSI修正 |
| **拓扑12** | 5 | **6** | +1协作 | RSSI修正 |
| **总计** | **20** | **23** | **+3** | **3处** |

### RSSI修正详情

| 拓扑 | 链路 | 修改前 | 修改后 | 原因 |
|------|------|--------|--------|------|
| 拓扑8 | SR→S2 | `high` | **`low`** | S2是远端用户 |
| 拓扑11 | S1R2→S2 | `high` | **`low`** | S2是远端用户 |
| 拓扑12 | SR→S2 | `high` | **`low`** | S2是远端用户 |

**统一原则**:
- S1 = 近端用户 = 高RSSI
- S2 = 远端用户 = 低RSSI

---

## 🛠️ 代码实现

### 修改位置

**两个文件都需要修改**:
1. `frontend/control-panel/index.html`
   - 第428-432行: 拓扑8
   - 第443-448行: 拓扑11
   - 第450-456行: 拓扑12

2. `frontend/node-view/index.html`
   - 第468-472行: 拓扑8
   - 第483-488行: 拓扑11
   - 第490-496行: 拓扑12

### 代码模板

**添加协作链路的标准格式**:

```javascript
拓扑X: [
    // 原有链路...
    { source: '节点A', target: '节点B', rssi: 'high/low', label: '...' },

    // 新增协作链路
    { source: 'S1', target: 'S2', rssi: 'coop', label: 'NOMA协作链路' }  // ✅
]
```

**关键字段**:
- `source`: `'S1'` (近端用户，固定)
- `target`: `'S2'` (远端用户，固定)
- `rssi`: `'coop'` (协作类型，固定)
- `label`: `'NOMA协作链路'` (标签，固定)

---

## 🎨 视觉效果

### 协作链路显示

**颜色**: 🟣 紫色/品红色 `#ff00ff`

**样式**: 虚线

**动画**: 慢速流动 (2.0秒)

**视觉对比**:
```
普通链路:  ━━━ ━━━ ━━━ →  (实线段)
协作链路:  - - -  - - -  - - - →  (虚线)
```

### 拓扑视图示例

**拓扑8视图** (修改后):
```
        🛰 SAT (卫星)
           ↓ 绿色快速
         ✈ SR (无人机)
         ↙        ↘
      绿色快速    橙色中速
        ↙            ↘
     📱 S1 ─────────→ 📱 S2
       近端  紫色慢速   远端
             虚线
```

**用户看到的效果**:
1. 绿色线快速从SAT流向SR
2. 绿色线快速从SR流向S1
3. 橙色线中速从SR流向S2
4. 紫色虚线慢速从S1流向S2 ⭐ 新增

---

## ✅ 验证测试

### 测试步骤

1. **启动系统**
   ```bash
   cd distributed-demo/scripts
   ./test_local.sh restart
   ```

2. **打开控制台**
   - http://localhost:8080/control-panel/

3. **逐个测试拓扑**

   **拓扑7测试**:
   - 点击"拓扑7"按钮
   - 观察SAT→S1(绿), SAT→S2(橙), S1→S2(紫虚线)
   - ✅ 应该看到3条链路，1条紫色协作链路

   **拓扑8测试** ⭐:
   - 点击"拓扑8"按钮
   - 观察SAT→SR(绿), SR→S1(绿), SR→S2(橙), S1→S2(紫虚线)
   - ✅ 应该看到4条链路，1条紫色协作链路

   **拓扑11测试** ⭐:
   - 点击"拓扑11"按钮
   - 观察所有链路，重点看S1→S2(紫虚线)
   - ✅ 应该看到5条链路，1条紫色协作链路

   **拓扑12测试** ⭐:
   - 点击"拓扑12"按钮
   - 观察所有链路，重点看S1→S2(紫虚线)
   - ✅ 应该看到6条链路，1条紫色协作链路

### 验证清单

| 检查项 | 拓扑7 | 拓扑8 | 拓扑11 | 拓扑12 |
|--------|-------|-------|--------|--------|
| 链路总数 | 3 | 4 | 5 | 6 |
| 紫色协作链路 | ✅ | ✅ | ✅ | ✅ |
| S1→S2方向 | ✅ | ✅ | ✅ | ✅ |
| 虚线样式 | ✅ | ✅ | ✅ | ✅ |
| 慢速流动 | ✅ | ✅ | ✅ | ✅ |
| SR→S2橙色 | N/A | ✅ | N/A | ✅ |
| S1R2→S2橙色 | N/A | N/A | ✅ | N/A |

### 浏览器控制台验证

**查看链路数据** (F12 → Console):
```javascript
// 应该看到包含 rssi: 'coop' 的链路
console.log('拓扑8链路:', topologyLinks[8]);
console.log('拓扑11链路:', topologyLinks[11]);
console.log('拓扑12链路:', topologyLinks[12]);

// 输出应该包含
{ source: 'S1', target: 'S2', rssi: 'coop', label: 'NOMA协作链路' }
```

---

## 📚 理论依据

### 为什么需要协作链路？

**NOMA原理要求**:
1. 同时传输多用户数据
2. 近端用户帮助远端用户
3. 提高系统总吞吐量

**文档依据**:
- 《12种NOMA网络拓扑定义.md》明确说明
- 下行通信拓扑(7-12)都有组内协作
- 协作链路是NOMA的核心特性

### 学术背景

**相关论文**:
- "Cooperative NOMA for Downlink Transmission"
- "Relay-Assisted NOMA in Wireless Networks"
- "SIC-Based NOMA with User Cooperation"

**核心公式**:

**近端用户解码能力**:
```
R₁ = log₂(1 + (α₁·P·|h₁|²) / (α₂·P·|h₁|² + N₀))
```

**远端用户解码能力** (无协作):
```
R₂ = log₂(1 + (α₂·P·|h₂|²) / N₀)
```

**远端用户解码能力** (有协作):
```
R₂' = log₂(1 + (α₂·P·|h₂|² + P_coop·|h_coop|²) / N₀)

R₂' > R₂  (协作提升性能)
```

**其中**:
- P: 发射功率
- α₁, α₂: 功率分配系数
- h: 信道增益
- N₀: 噪声功率
- P_coop: 协作功率

---

## 🔧 故障排查

### 问题1: 看不到紫色协作链路

**可能原因**:
1. 拓扑定义未更新
2. 浏览器缓存
3. 服务器未重启

**解决方案**:
```bash
# 1. 检查代码是否已修改
grep "rssi: 'coop'" distributed-demo/frontend/control-panel/index.html

# 应该在拓扑7,8,11,12中各出现一次

# 2. 重启服务器
cd distributed-demo/scripts
./test_local.sh restart

# 3. 硬刷新浏览器
Ctrl + Shift + R
```

### 问题2: 协作链路不是虚线

**可能原因**:
- 动画配置未更新

**检查代码**:
```javascript
// 应该有虚线配置
.arcDashLength(d => {
    if (d.rssi === 'coop') return 0.5;  // ✓ 虚线
    return 0.4;
})
.arcDashGap(d => {
    if (d.rssi === 'coop') return 0.2;  // ✓ 间隙
    return 0.1;
})
```

### 问题3: SR→S2不是橙色

**可能原因**:
- RSSI未修正为 `low`

**检查代码**:
```javascript
// 拓扑8
{ source: 'SR', target: 'S2', rssi: 'low', label: '低RSSI空/地' }  // ✓

// 拓扑12
{ source: 'SR', target: 'S2', rssi: 'low', label: '低RSSI空/地' }  // ✓
```

---

## 📝 总结

### 补全成果

✅ **新增3条NOMA协作链路**:
- 拓扑8: S1→S2 (NOMA协作)
- 拓扑11: S1→S2 (NOMA协作)
- 拓扑12: S1→S2 (NOMA协作)

✅ **修正3处RSSI标记**:
- 拓扑8: SR→S2 (high → low)
- 拓扑11: S1R2→S2 (high → low)
- 拓扑12: SR→S2 (high → low)

✅ **符合NOMA原理**:
- 下行拓扑都有协作
- 近端帮助远端
- 功率分配合理

### 关键要点

1. ✅ 4个下行拓扑(7,8,11,12)都有协作链路
2. ✅ 紫色虚线慢速流动
3. ✅ S1(近端) → S2(远端)
4. ✅ 远端用户使用低RSSI(橙色)
5. ✅ 符合《12种NOMA网络拓扑定义.md》

### 修改文件

```
distributed-demo/frontend/
├── control-panel/index.html  (第428-456行) ⭐
└── node-view/index.html      (第468-496行) ⭐
```

---

**文档作者**: Claude AI Assistant
**最后更新**: 2025-11-20
**版本**: v1.0
**状态**: ✅ 完整
