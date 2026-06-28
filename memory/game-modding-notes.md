# 游戏 Mod 原理 · 学习笔记

> 写于 2026-06-03，桐希安排学习 NexusMods 网站 mod 原理

---

## 一、什么是 Mod

Mod = Modification（修改/模组）。对游戏文件进行修改或扩展，改变游戏的外观、玩法、内容。

Nexus Mods 是全球最大的 Mod 托管平台，支持《上古卷轴》《辐射》《赛博朋克2077》《巫师3》《星空》等上千款游戏。

---

## 二、Mod 的几种技术原理

### 2.1 文件替换型（最原始）

**原理：** 直接替换游戏安装目录下的原始文件。

- 替换贴图（`.dds` `.png`）
- 替换模型（`.nif` `.mesh`）
- 替换音频（`.wav` `.ogg`）
- 替换配置文件（`.ini` `.cfg`）

**优点：** 简单直接
**缺点：** 容易丢失，游戏更新会被覆盖，卸载麻烦
**工具：** 手动复制粘贴

---

### 2.2 打包文件注入型

**原理：** 现代游戏把资源打包进一个大文件（Archive），Mod 工具修改这个包。

常见打包格式：
| 游戏引擎 | 打包格式 | 工具 |
|---------|---------|------|
| Bethesda | `.bsa` / `.ba2` | Archive2, BAE |
| Unreal Engine | `.pak` | UnrealPak |
| Source | `.vpk` | GCFScape |
| REDengine (2077) | `.archive` | WolvenKit |
| Unity | `.assets` | AssetStudio |
| Frostbite | `.sb` `.cas` | Frosty Editor |

**流程：** 解包 → 修改 → 重新打包 → 替换原文件

---

### 2.3 引擎脚本覆盖型

**原理：** 游戏引擎支持脚本（Script），Mod 编写新脚本或覆盖原有脚本。

| 游戏 | 脚本语言 | 工具/框架 |
|:----|:--------|:----------|
| 上古卷轴/辐射 | Papyrus | Creation Kit |
| 巫师3 | RedScript / Lua | WolvenKit |
| 赛博朋克2077 | RedScript | CET (Cyber Engine Tweaks) |
| 我的世界 | Java | Forge / Fabric / NeoForge |
| Larian (博德之门3) | Lua / Osiris | Script Extender |
| RimWorld | C# (Harmony) | Harmony Patcher |
| 星露谷物语 | C# | SMAPI |

**核心：** 利用游戏引擎的原生脚本扩展能力，挂载或替换逻辑。

---

### 2.4 DLL / 代码注入型 (Advanced)

**原理：** 通过注入 DLL 或 Hook 游戏进程内存，修改运行时行为。

**典型框架：**
- **Script Extender (SKSE/F4SE/OBSE)** — 为上古卷轴/辐射系列扩展脚本能力
- **Harmony Patcher (C#)** — 运行时 Patch 方法，用在 RimWorld、星露谷等 Unity 游戏
- **ASI Loader** — GTA 系列的 DLL 注入方式
- **Detours** — Windows API Hook 技术

**工作流程：**
1. 游戏启动时加载 `mod_loader.dll`（通过修改导入表或注入）
2. Loader 扫描 mod 目录下所有 `.dll` 文件
3. 每个 DLL 在初始化时 Hook 游戏函数地址
4. 替换函数指针，插入自定义逻辑
5. 执行完毕再调回原函数（或者跳过原函数）

**技术栈：** C/C++、Win32 API、逆向工程、内存偏移计算

---

### 2.5 Resource / Asset 覆盖型

**原理：** 利用游戏的"资源优先级加载"机制。

- 很多引擎会按优先级加载资源
- 把 Mod 文件放在更高优先级的路径（通常是 `Data/` 或 `Mods/`）
- 引擎在读取 `textures/armor.dds` 时，先看到 Mod 目录的版本，就用它
- 这就是 **"松散文件优先"** 原则

**例子：**
- 老滚 5：`Data/Textures/` → 覆盖 `Skyrim - Textures.bsa`
- 赛博朋克：`archive/pc/mod/` → 覆盖 `basegame_*.archive`
- 博德之门 3：`Data/Mods/` → 覆盖官方 `Gustav.pak`

---

## 三、Mod 管理工具的工作原理

### Vortex（Nexus Mods 官方工具）

**核心功能：**
1. **符号链接/硬链接部署** — 不复制文件到游戏目录，而是创建链接，方便开关
2. **冲突解决** — 两个 Mod 改同一个文件时，显示冲突树，让用户选优先级
3. **排序** — LOOT 算法自动排序加载顺序（尤其是 Plugins/ESPs）
4. **配置文件 Profile** — 不同 Mod 组合保存为不同 Profile，随时切换
5. **自动更新检测** — 扫描已安装 Mod 的新版本

### Mod Organizer 2（MO2，社区更爱用）

**核心原理：** **虚拟文件系统 (VFS)**

- 不碰游戏目录一个字
- 通过 USVFS (User Space Virtual File System) Hook 游戏进程的文件读取 API
- 游戏想读 `data/textures/xxx.dds` 时，MO2 拦截这个请求
- 先在 Mod 目录中查找，找到了就用 Mod 版本，找不到才用游戏原始文件
- **优点：** 游戏目录干干净净，Mod 随意开关，换 Profile 秒切

### 技术对比：

| 特性 | Vortex | MO2 |
|:----|:-------|:----|
| 部署方式 | 硬链接/符号链接 | VFS 文件系统 Hook |
| 是否污染游戏目录 | 是（创建硬链接） | 否（完全不碰） |
| 安装/卸载速度 | 快（创建/删除链接） | 极快（改 VFS 配置即可） |
| 冲突管理 | 规则引擎 | 左侧列表排序 |
| 适合新手 | ✅ | ⚠️ 需要一点概念 |
| 适合老油条 | ⚠️ | ✅ 更灵活 |

---

## 四、Nexus Mods 平台如何工作

### 网站功能
- **Mod 托管** — 上传/下载 Mod 文件，版本管理
- **分类标签** — 按游戏、类型（服装、武器、玩法、UI、角色等）
- **评分/评论/点赞** — 社区反馈
- **图片/视频预览** — Mod 展示
- **文件校验** — 通过 Premium 会员直接高速下载，免费用户限速
- **合集 (Collections)** — 一键安装整套 Mod 组合

### API
- Nexus Mods 提供 REST API 供工具（Vortex/MO2）使用
- 需要 API Key
- 功能：搜索 Mod、获取下载链接、检查更新、获取 Mod 元数据
- 端点示例：`https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}.json`

### Mod 的常见文件格式
| 后缀 | 说明 |
|:----|:------|
| `.esp` `.esm` `.esl` | Plugin 文件（老滚/辐射，含游戏逻辑、对话、任务） |
| `.bsa` `.ba2` | 资源包（打包的模型/贴图/音频） |
| `.pex` | 编译后的 Papyrus 脚本 |
| `.hkx` | 动画文件 |
| `.dds` | 贴图文件（DirectDraw Surface） |
| `.nif` | 模型文件（NetImmerse/NifSkope） |
| `.wav` `.xwm` | 音频文件 |
| `.archive` | 赛博朋克资源包 |
| `.pak` | Unreal / 博德之门3 资源包 |
| `.dll` | 代码注入 Mod |

---

## 五、不同类型 Mod 的技术深度

| 复杂度 | 类型 | 例子 | 需要技能 |
|:------:|:----|:-----|:---------|
| ⭐ | 贴图替换 | 4K皮肤、装备重新上色 | Photoshop / GIMP |
| ⭐⭐ | 模型替换 | 武器换模型、服装改版 | Blender / 3ds Max + NifSkope |
| ⭐⭐⭐ | 配置调整 | 修改游戏参数、平衡性 | 文本编辑器 + 懂游戏机制 |
| ⭐⭐⭐ | 音频替换 | 角色语音、BGM 替换 | 音频编辑软件 |
| ⭐⭐⭐⭐ | 脚本 Mod | 新任务、新对话、新系统 | 游戏专用脚本语言 + 编辑器 |
| ⭐⭐⭐⭐⭐ | DLL / 框架 | 新功能系统、UI 重制、引擎扩展 | C++/C# + 逆向 + 内存操作 |
| ⭐⭐⭐⭐⭐ | 多 Mod 兼容 | 把几个大 Mod 整合到一起 | 深入理解游戏架构 + 冲突解决 |

---

## 六、经典 Mod 框架举例

### Skyrim (老滚5) 生态
```
SKSE (Skyrim Script Extender) — DLL 注入，扩展 Papyrus
SKSE Plugins — Address Library, ConsoleUtil, Scaleform
ENB / Reshade — 图形渲染管线 Hook (DX9/11)
BodySlide — 身形/服装物理
FNIS / Nemesis — 动画行为系统
RaceMenu — 捏脸增强
MCM (Mod Configuration Menu) — Mod 配置菜单
```

### Cyberpunk 2077 生态
```
CET (Cyber Engine Tweaks) — Lua 脚本注入，控制台
Red4Ext / RED4ext — DLL 插件框架
WolvenKit — Archive 编辑工具
ArchiveXL — 资源扩展
TweakXL — 游戏数据扩展
Input Loader — 输入设备支持
```

### 我的世界生态
```
Forge — 字节码注入 + 事件系统
Fabric — 轻量 Mod Loader
NeoForge — Forge 的分叉
Quilt — Fabric 的分叉
Data Pack — 无需 Mod Loader 的数据包（官方支持）
```

---

## 七、核心概念总结

| 概念 | 一句话 |
|:----|:-------|
| **打包文件** | 游戏把资源封在一个大包里，工具解包/封包 |
| **松散文件覆盖** | 引擎按优先级路径加载，Mod 文件优先级更高 |
| **符号链接/硬链接** | 不复制文件，创建"快捷方式"式引用（省空间、易管理） |
| **VFS (虚拟文件系统)** | Hook 文件读取 API，在内存中重定向路径（MO2） |
| **Script Extender** | 给游戏脚本系统开后门，支持更多 API |
| **DLL 注入** | 游戏加载时把 Mod DLL 塞进进程空间 |
| **函数 Hook** | 修改函数开头几个字节/jump 到 Mod 代码 |
| **Harmony Patch** | C# 运行时修改 IL 代码（Mono/.NET 游戏） |
| **冲突解决** | 多个 Mod 改同一文件时，靠加载顺序或规则决定谁赢 |
| **Profile** | 一组 Mod 的启停/排序配置，随时切换 |

---

## 学完了。有啥想深挖的？

我可以针对某个游戏或某种 Mod 类型展开：

- 赛博朋克 2077 的 Mod 体系（CET / RedScript / ArchiveXL）
- 老滚/辐射系列 Mod 全链路
- DLL 注入 / Hook 的底层实现细节
- Mod 冲突排查方法和工具
- 如何制作一个简单的贴图 Mod
- 或者直接动手 —— 需要我帮你做什么？
