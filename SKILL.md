---
name: movie-finder
version: 2.0.0
description: 找影视资源+抓字幕+转存网盘。Load when 找片、找资源、下字幕。
---

# 影视一条龙：找片 → 验活 → 转存 → 字幕 → 上传

一个开箱即用的影视资源工作流：**找片源 → 逐条验活 → 按画质排序 → 转存网盘 → 找字幕 → 上传字幕**。不依赖任何私有服务，装上就能用。

## 什么时候用

| 用户说的话 | 走哪条线 |
|---|---|
| 「我要看《XXX》」/「帮我找 XXX」 | 找片全流程 → 报推荐 → 用户确认后转存 |
| 「《XXX》更新了吗」 | 查 `get-share-update-files` → 只存新增正片 → 配新集字幕 |
| 「这个字幕翻译有问题」 | **只走字幕线**，不重下同一份，换同站另一个版本 |
| 「有没有中英双字的」/「这集没字」 | 只走字幕线，按「双语 > 特效 > 官方简体」选 |
| 「字幕时间轴对不上」 | 只走字幕线，按 release 名重新匹配 |
| 「找 4K Remux / 要杜比视界」 | 按画质优先级筛，主动排除 ISO / BDMV 整盘 |

**关键区分**：用户已经有片源、只是字不对时，**不要重新找片**，直接进第二部分。

## 支持的网盘

**搜索层面全部支持**（各站抓到的网盘链接都会报），**自动转存只对夸克开箱即用**：

| 网盘 | 找链接 | 自动转存 |
|---|---|---|
| **夸克网盘** | ✅ | ✅ 靠官方 `quarkclouddrive` skill 转存 / 追更 / 上传字幕 |
| 百度 / 115 / 迅雷 / 阿里 / UC / 光鸭 | ✅ | ⚠️ 需自备工具，只能报链接 |
| **磁力 / BT** | ✅ | ✅ 夸克可离线解析 |

默认夸克只是因为 `preferred_netdisk=quark`；改成 `baidu` / `115` / `xunlei` / `aliyun` 就优先筛那家的链接，只是自动转存那一步要自己完成。

## 安装

```bash
# Hermes Agent
git clone https://github.com/wjl3285857571/movie-finder.git ~/.hermes/skills/media/movie-finder

# Claude Code / 其他兼容 Agent Skills 的客户端
git clone <repo> <你的 skills 目录>/movie-finder
```

想让 agent 直接把片存进夸克网盘，再装夸克官方 skill（可选；不装也能用，只是退化成「给链接 + 自己点」）：

```bash
hermes skills install quarkclouddrive   # 首次使用扫码授权一次
```

| 依赖 | 用途 | 没有会怎样 |
|---|---|---|
| `curl` | 抓网页 / 下载 | macOS / Linux 自带 |
| `bsdtar` | 解压字幕 RAR/ZIP | macOS 自带；Linux 装 `libarchive-tools`，或改用 `unrar` / `7z` |
| Python 3 + `Pillow` | 读字幕站验证码 | 只能手输验证码（`pip install pillow`） |
| 浏览器工具（`browser_exec` 等） | 抓 SPA 站 / 过验证 | 部分站点抓不到 |

## 配置（改这几项就能适配自己）

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `preferred_netdisk` | `quark` | 目标网盘。改成 `baidu` / `115` / `xunlei` / `aliyun` 就优先筛那家 |
| `delivery_dir` | `影视/影视资源` | 转存到网盘里的哪个目录（需已存在） |
| `subtitle_dir` | `~/Downloads/` | 字幕下载到本机哪个目录 |
| `quality_priority` | Remux > WEB-DL > WEBRip > HDTV | 画质排序偏好 |

改法：直接改下面「用户偏好」一节里对应的值。

## 依赖声明（诚实标注来源）

| 部分 | 归属 | 内容 |
|---|---|---|
| **找片** | ✅ 本 skill | 站点清单、showpaw 抓取流、验活规则、画质排序、报告格式 |
| **抓字幕** | ✅ 本 skill | zimuku 过验证码、三段跳下载、bsdtar 解压、选版规则 |
| **`quarkclouddrive`** | ❌ **夸克官方**（`quarkclouddrive_816db00f`，v1.0.20+） | 转存 / 追更 / 上传 / 搜索 |

`quarkclouddrive` **不是本 skill 的一部分**，是夸克官方发布的第三方 skill。本 skill 只在「要存进夸克网盘」时按接口调它的 CLI，**像调用一个外部工具**；它的内部规则（session-id 格式、msg 原样输出、目录参数禁止自动填充等）归它自己管，本 skill 不改它、不复制它的内容。

**说人话**：找片和字幕是这个 skill 自己攒的本事；夸克那个只是搬东西的手推车。

## 用户偏好（默认值，可按「配置」一节改）

- **默认网盘**：`quark`。改这一项即可切换。
- **画质优先级**：
  1. **Remux**（蓝光原盘无损压回 mkv，可直接在线看）
  2. **WEB-DL**（DV / HDR10+ 优先，杜比视界 + 杜比全景声）
  3. **WEBRip**
  4. **HDTV / 录制**
  5. 其他
  - 同资源有杜比选杜比（DV + Atmos > 仅 Atmos）。WEB-DL 里 Atmos 是常态，**Dolby Vision（DV）才是真分级关键**。
  - DV 标签必须先对实碟规格，见下文「画质判断：DV 标签陷阱」。
- **不可直看**：蓝光原盘 ISO / BDMV 目录（网盘解析不了光盘镜像）。碰到只有 ISO 的，主动找 Remux 替代，或回报无 Remux 由用户决定。
- **交付形态**：先在聊天里报链接 / 规格 + 推荐理由，**用户确认后再转存**。装了 `quarkclouddrive` 就代转存并同步上传字幕；没装则停在「给链接」并说明原因。不要只丢链接就完事。
- **「要最高画质」是硬要求**——不要拿低码版凑数。目标是 4K Remux / DV 却只有 720p、WEBRip 时，如实说没有最高档，并给两个清晰选项：「等几天等新压制出源」或「去 BT 站拿磁力直挂夸克」。
- **周更剧字幕要「中英特效」档**，不是随便一份中文 SRT。换字幕前先确认有没有同档新包；只有纯中文 SRT 时说明这是临时顶替。

# 第一部分：找片

## 铁律：说「没有」前必须过完四关

1. **层级走完**：主力 → 备选 → 外部，一层不跳
2. **关键词变体**：中/英文名、`S01E05`、`E05`、`第5集`、`05`
3. **内容而非标题**：看**文件列表**，「更04集」不代表没有 E05
4. **失败原因分开**：没有 / 打不开 / 失效 / 要登录 是四件事

卡住先怀疑方法（参数、渲染、更直接的命令），不先怀疑资源不存在。

## 资源站（按顺序搜，`?q=` 一律 404）

1. **showpaw**（主力）：站内搜索框，`?s=` 无效
2. **kkpans**（整季合集）：`www.kkpans.com/?search=<kw>`（`?s=` 返回缓存旧页）
3. **qkyunso**：`qkyunso.com/search?keyword=<kw>`（滞后 3–7 天）
4. **time1080**：`v.time1080.xyz/s.php?wd=<kw>`（CF 挡，只当判定站）
5. **4kzn / kuakes**：`4kzn.cc/?post_type=book&s=` / `kuakes.com/?s=`（覆盖差）
6. **外部**：腾讯频道 / linux.do 快照 / kuake5 / suenen / BT
7. **磁力**：`torrentdownloads.me/search/?search=<kw>`
8. **以上都没有 → 自己去找**：允许自行到清单外的其他资源站、搜索引擎、社群（TG 频道、论坛、网盘分享页等）扒资源，**不受这份清单限制**。找到后一样要验活、按画质排序、照实报规格。某个新站反复好用，就在报告里提一句「建议加进清单」，由用户决定收不收。

不跳层；**缺单集先找整季包**。中文先 `quote`。书/课/软件走 PanSou（`so.252035.xyz/api/search`，`src=tg` 必带，超时≠没有）。

## 第 1–4 步：showpaw

1. 站内搜索框（`?s=` 不参与）→ 详情或消歧页；等「正在为你查询资源」消失（5–30s）再抓
2. 消歧按 `button.v4-disambig` 下标点，先打印 0..N 确认
3. TreeWalker 把 `pan.quark.cn/s/<hash>` 与标题配对去重；0 命中改为先取全部链接、再向上找含 `GB`/`REMUX`/`2160` 的容器

## 第 5 步：验活（跑脚本，不手搓）

`python3 scripts/mf.py verify <链接或hash> [更多…] [--json]`

`alive` / `dead` / `half_dead` / `unknown`；`dead` 带错误码（`41006` 分享不存在）。≤6 全验，>8 只验前 3 + 后 1（注明未验活）。

**红线**：字段拿不到只出 `unknown`，不猜；`all_file_num != file_only_num` 单独出现不算被清理（实测 4 vs 3 正常）；判 `half_dead` 必须翻过文件列表、只剩字幕图片。

## 画质判断：DV 标签陷阱

有些片子的影碟本身就没有 DV（诺兰的碟一贯只有 HDR10 + DTS-HD MA，无 Atmos）。这种片网上标 `TrueHD.Atmos.7.1.DV` 的「Remux」多是流媒体转的，码率往往不到碟版三分之一——**别为了「DV」两个字把碟版 Remux 换掉**。判断看 blu-ray.com / r/SceneReleases 的实碟规格，不看盗版站标题。

## 第 6 步：兜底

`site:panku8.com` / `site:haimian.eu.org` → `"<片名>" 夸克网盘 4K` → 腾讯频道 `pd.qq.com` → linux.do 快照 → kuake5 / suenen → `torrentdownloads.me`。**明文 ≠ 存活**；裸 hash 先对 `title`。

## 第 7 步：报告

按画质排序，标 **规格 / 体积 / 字幕 / 是否验活** + 理由；>60 Mbps 碟版 Remux 提醒在线会被转码。**等用户确认再转存**。

---

# 第二部分：抓字幕

目标：`zimuku.org`（备用 `srtku.com` / `zmk.pw`）→ `~/Downloads/`，不留 scratch。

1. 5 位数字验证码放大 400×108 自己读，读错刷新，不发用户
2. **填码 → 提交 → 搜索同一次 `browser_exec`**（断连丢 cookie）；用站内框，`/search?q=` 会重新验证
3. 双语 > 特效 > 官方简体，release 名匹配；周更特效两集一包，E07 没有多半是包没发
4. 三段跳 `/detail` → `/dld` → `/download/<b64>/svr/d0`，带 UA + referer；先 `file` 判类型，压缩包 `bsdtar -tf` 看再解
5. 报文件名/大小/MD5/语言/格式/组/时间/详情页 + 是否匹配

---

# 第三部分：存进夸克

**3.1 前置**：`cd ~/.hermes/skills/quarkclouddrive && bash scripts/install.sh`

**3.2 固定目录 `影视/影视资源`**（按剧名建子文件夹，字幕放 `[zmk…` 子目录）。`browse --parent-fid` 逐层定位，不用 `search --search-type dir`；建子目录必须带 `--parent-fid`，别用 `create-folder --dir-path` 全路径（会另建空壳）。

**3.3 转存**：先 `share-detail` 列内容（`first_fid` → `--pdir-fid <fid> --size 50`），别靠网页滚动，`dir: true` 继续翻。`saveas --fid-list <fid> --to-pdir-path "影视/影视资源/<名>"`，**完成后 browse 回读**。整季别 `--save-all`，已存用 `move` 提季。

**3.4 追更**：`get-share-update-list` 找 share_url → `get-share-update-files` → 只挑 4K 正片 `saveas --fid-list`；「新增」≠「最新两集」；`saveas-update` 只用于全是正片。

**3.5 字幕**：`upload <字幕> --parent-fid <[zmk fid>`，回读确认；文件名对齐正片；空间不足要转达。

**3.6 硬约束**：`--session-id` `{unix秒}-{6位随机}` 全程复用；`--session-input` 用户请求逐字传入（不改写、不摘要）；`--to-pdir-fid` 不填 `0`；搜索结果只前 5 条表格；`msg` 原样输出。

---

# 详细资料

坑与平台特殊性 `references/pitfalls.md`、找片 `references/finding-workflow.md`、验活 `references/quark-verify.md`、转存与交付链 `references/quark-save.md`、字幕 `references/subtitle-workflow.md`、PanSou `references/pan-network-search.md`、字幕源 `references/subtitle-sources.md`、选版 `references/subtitle-quality-picker.md`。脚本 `scripts/mf.py`（verify / rank），单测 `scripts/test_mf.py`。
