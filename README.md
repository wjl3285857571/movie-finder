# movie-finder

> 给 AI Agent 的影视资源 + 字幕工作流 skill：**找片源 → 逐条验活 → 按画质排序 → 转存网盘 → 找字幕 → 上传字幕**

一个装上就能用的 Agent Skill。不依赖私有服务，不需要自己写脚本。

[English summary ↓](#english)

---

## 它解决什么问题

你想看一部片，通常是这样一个流程：

1. 去好几个资源站搜 → 每个站结果不一样、有的只有标清、有的链接已经死了
2. 挑一个下载 → 发现只有机翻字幕 / 没有中英双字 / 这集缺字幕
3. 再去字幕站找 → 被验证码拦住、下载下来是加密 RAR、格式不对还要转
4. 字幕和片源的版本对不上 → 时间轴错位

这个 skill 把上面 4 步串成一条自动流水线，并且内置了一堆踩过的坑。

---

## 核心特点

| 特点 | 说明 |
|---|---|
| **逐条验活** | 不信任资源站标的「已验证有效」——每条链接都实际打开确认，死链剔除并在报告里说明 |
| **不拿低码版凑数** | 某集只有 1.5G 的 mp4 时会明说「这个源缺 4K」，而不是拿它顶替。宁可等，也不糊弄 |
| **字幕一起交付** | 找到片源后主动找对应集数的字幕，匹配 release 名（分辨率/来源/编码/组名）后才上传，不让你自己去搬 |
| **字幕不满意可换版本** | 特效字幕翻译常带润色腔、官方字幕准确但没特效——两类互补，会列全让你挑，不重下同一份 |
| **多网盘支持** | 默认夸克，也支持百度 / 115 / 迅雷 / 阿里 / UC / 光鸭 / 磁力 |
| **整季合集优先** | 单集源跳集时自动去找 `S01E01-Exx` 一整包的分享 |
| **不过早下结论** | 说「没有」之前必须走完全部检索层级 + 看过文件列表 + 说清失败原因（见 SKILL.md 的「铁律」一节） |

---

## 支持的网盘

**搜索层面全部支持，自动转存只对夸克开箱即用：**

| 网盘 | 找链接 | 自动转存 | 说明 |
|---|---|---|---|
| **夸克网盘** | ✅ | ✅ **开箱即用** | 作者默认。靠官方 [`quarkclouddrive`](#依赖与归属) skill 自动转存 / 追更 / 上传字幕 |
| 百度网盘 | ✅ | ⚠️ 需自备工具 | 抓到链接报给你，转存自己点 |
| 115 网盘 | ✅ | ⚠️ 需自备工具 | 同上 |
| 迅雷网盘 | ✅ | ⚠️ 需自备工具 | 同上 |
| 阿里云盘 | ✅ | ⚠️ 需自备工具 | 同上 |
| UC / 光鸭 / 其他 | ✅ | ⚠️ 需自备工具 | 同上 |
| **磁力 / BT** | ✅ | ✅ 夸克可离线解析 | 夸克网盘能直接把磁力变成文件 |

> **为什么默认夸克？** 只是作者个人的使用习惯——夸克对 4K / 杜比视界 / `.sup` 图形字幕的在线播放兼容性好，而且磁力可以离线解析。
> **你完全可以用别的网盘**：把 SKILL.md 里的 `preferred_netdisk` 改成 `baidu` / `115` / `xunlei` / `aliyun` 就行，skill 会优先筛对应网盘的链接，只是自动转存那一步要你自己完成。

---

## 安装

### 方式 1：Hermes Agent

```bash
git clone https://github.com/wjl3285857571/movie-finder.git \
  ~/.hermes/skills/media/movie-finder
```

### 方式 2：Claude Code / 其他兼容 Agent Skills 的客户端

把本仓库整个目录放到你的 skills 目录下即可（目录名保持 `movie-finder`）。

### 方式 3：手动

把 `SKILL.md` 复制到你 agent 的 skills 目录，命名为 `movie-finder/SKILL.md`。

### 可选：装夸克官方 skill 解锁自动转存

```bash
# Hermes
hermes skills install quarkclouddrive
```

首次使用会引导你扫码授权（一次即可）。

**不装也能用**：skill 会退化成「找链接 + 报给你 + 你自己点」，只是少了自动转存和自动上传字幕。

---

## 依赖

| 依赖 | 用途 | 必需 |
|---|---|---|
| `curl` | 抓网页 / 下载字幕 | ✅（macOS / Linux 自带） |
| `bsdtar` 或 `unrar` / `7z` | 解压字幕 RAR / ZIP | ✅（macOS 自带 `bsdtar`；Linux 装 `libarchive-tools`） |
| Python 3 + `Pillow` | 读字幕站图片验证码 | 推荐（没有就只能手输验证码） |
| 浏览器工具 | 抓 SPA 站点 / 过部分验证 | 推荐（没有则部分站点抓不到） |

```bash
pip install pillow
```

---

## 用法示例

```text
你：我要看《盗火线》
它：找到 5 条，去掉 1 条死链。首选 4K Remux 58GB（18 seed），次选 2.79GB（67 seed 最健康）。
    要哪个？
你：a
它：已存到「影视/影视资源/盗火线 4K原盘REMUX 国英双音 内封字幕」。要不要配字幕？
```

```text
你：《幻视任务》更新了吗
它：更新了 3 个文件，但其中 2 个是低码 mp4。只存了 4K 那集，并把 E05/E06 字幕一起传上去了。
```

```text
你：这个字幕翻译有问题
它：同站还有 2 个版本——官方简体（准确、无特效、分集单文件）和另一个组的双语特效。
    你要哪个？
```

---

## 它是怎么工作的

```
找片源
  ├─ 主力站（showpaw）→ 四个备选站 → 外部渠道 → BT 兜底
  ├─ 消歧（同名多版本按年份+类型选）
  ├─ 抠链接（按 DOM 文档顺序配对标题与链接）
  └─ 逐条验活（活链=「共 N 个文件」+「永久有效」；死链剔除并说明）

转存
  ├─ 夸克：调 quarkclouddrive CLI（saveas / saveas-update / upload）
  └─ 其他网盘：给链接，用户手动

抓字幕
  ├─ 过图片验证码（放大 400×108 后识别）
  ├─ 选版本（双语 > 特效 > 官方简体；核对 release 名）
  ├─ 三段跳下载（详情页 → 下载页 → 真实文件）
  └─ bsdtar 解压 → 落到 $subtitle_dir

交付
  └─ 正片 + 字幕一起进网盘同一个目录
```

---

## 配置

改 SKILL.md 里这几个字段就能适配自己：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `preferred_netdisk` | `quark` | 目标网盘，可改 `baidu` / `115` / `xunlei` / `aliyun` |
| `delivery_dir` | `影视/影视资源` | 转存到网盘哪个目录（需已存在） |
| `subtitle_dir` | `~/Downloads/` | 字幕下载到本机哪个目录 |
| `quality_priority` | Remux > WEB-DL > WEBRip > HDTV | 画质排序偏好 |

---

## 依赖与归属

本 skill 的**主体是自写的方法论**：

| 部分 | 归属 |
|---|---|
| 找片（站点清单、抓取流、验活规则、画质排序、报告格式） | ✅ 本仓库 |
| 抓字幕（验证码、三段跳下载、解压、选版规则） | ✅ 本仓库 |
| `quarkclouddrive`（转存 / 追更 / 上传） | ❌ **夸克官方**，第三方 skill，仅调用其 CLI |

`quarkclouddrive` 是夸克官方发布的 skill，**不是本仓库的一部分**。本仓库只在「要存进夸克网盘」时调用它，像调用一个外部工具。

---

## 已知限制

- **部分资源站有 Cloudflare Turnstile 人机验证**（如 time1080），自动化过不去——这种站只能当「有没有」的判定站，最终链接需要用户自己点开
- **需要注册/回复才能看链接的站**（kuake5 / suenen / linux.do 等），agent 拿不到明文链接
- **蓝光原盘 ISO / BDMV** 支持差，会主动引导找 Remux 替代
- **非夸克网盘**只能给链接，不能自动转存
- **院线新片**（上映 3-4 周内）网盘通常还没有资源，skill 会如实说明而不是塞枪版

---

## 免责声明

本 skill **只做公开分享链接的检索与整理，不存储、不上传任何文件**。

所有资源均来自第三方公开分享。使用者应自行确认内容的合法性与版权状态，并仅用于个人学习研究。作者不对第三方链接的可用性、合法性或内容负责。

---

## License

MIT

---

<a id="english"></a>
## English

**movie-finder** is an agent skill for finding movies/TV resources and matching subtitles.

Pipeline: **search → verify every link → rank by quality → save to netdisk → fetch subtitles → upload subtitles**.

- Verifies every link instead of trusting "verified" badges
- Never substitutes a low-bitrate file for a missing 4K episode
- Delivers subtitle + video together, matched by release name
- Multi-netdisk: Quark (default, full automation), plus Baidu / 115 / Xunlei / Aliyun / magnet (link finding only)
- Built-in rules against premature "not found" conclusions

Install: clone into your agent's skills directory. Optionally install the official `quarkclouddrive` skill for automatic transfer to Quark.

MIT licensed. Searches public shares only; hosts nothing.
