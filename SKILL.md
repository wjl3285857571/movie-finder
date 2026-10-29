---
name: movie-finder
version: 1.0.0
description: 找影视资源+抓字幕+转存网盘。Load when 找片、找资源、下字幕。
---

# 影视一条龙：找片 → 验活 → 转存 → 字幕 → 上传

一个开箱即用的影视资源工作流 skill：**找片源 → 逐条验活 → 按画质排序 → 转存网盘 → 找字幕 → 上传字幕**。

不依赖任何私有服务，装上就能用。

---

## 什么时候用

| 你说的话 | 它会做什么 |
|---|---|
| 「我要看《XXX》」/「帮我找 XXX」 | 全站搜 → 验活 → 按画质排序报给你 → 你点头后转存网盘 |
| 「《XXX》更新了吗」 | 查你已转存的分享有没有新集 → 只存新增的正片 → 配新集字幕 |
| 「这个字幕翻译有问题」 | **不重下同一份**，换同站另一个版本（官方简体 / 别的压制组） |
| 「有没有中英双字的」 | 按「双语 > 特效 > 官方简体」优先级挑，并核对与片源的 release 名是否一致 |
| 「这集没字幕」/「字幕时间轴对不上」 | 抓对应集数的字幕，匹配 resolution / 来源 / 编码 / 组名 |
| 「找 4K Remux / 要杜比视界」 | 按画质优先级筛，主动排除 ISO / BDMV 整盘 |

**核心特点**：
- **逐条验活**——不信任资源站标的「已验证」，每条链接自己打开确认
- **不拿低码版凑数**——某集只有 1.5G 的 mp4 时会明说「这个源缺 4K」，而不是拿它顶替
- **字幕跟片源一起交付**——不会让你自己再去搬字幕
- **支持多网盘**——默认夸克，也可用百度 / 115 / 迅雷 / 阿里（见下）

---

## 支持的网盘

**搜索层面全部支持**（会去各资源站抓所有网盘链接），**自动转存只对夸克开箱即用**：

| 网盘 | 找链接 | 自动转存 | 说明 |
|---|---|---|---|
| **夸克网盘** | ✅ | ✅ **开箱即用** | 作者默认使用。靠官方 `quarkclouddrive` skill 自动转存 + 追更 + 上传字幕 |
| 百度网盘 | ✅ | ⚠️ 需自备工具 | 能抓到链接并报给用户，转存要用户自己点，或另装百度网盘相关 skill/CLI |
| 115 网盘 | ✅ | ⚠️ 需自备工具 | 同上 |
| 迅雷网盘 | ✅ | ⚠️ 需自备工具 | 同上 |
| 阿里云盘 | ✅ | ⚠️ 需自备工具 | 同上 |
| UC / 光鸭 / 其他 | ✅ | ⚠️ 需自备工具 | 同上 |
| **磁力 / BT** | ✅ | ✅ 夸克可离线解析 | 夸克网盘能直接把磁力链接变成文件 |

> **为什么默认夸克？** 只是作者个人的使用习惯（夸克对 4K / 杜比视界 / `.sup` 图形字幕的在线播放兼容性好，且磁力可离线）。**你完全可以用别的网盘**——把 `preferred_netdisk` 配置改成 `baidu` / `115` / `xunlei` 即可，skill 会优先筛对应网盘的链接，只是自动转存那一步要你自己完成。

---

## 安装

### 1. 放到 agent 的 skills 目录

```bash
# Hermes Agent
git clone <this-repo> ~/.hermes/skills/media/movie-finder

# Claude Code / 其他兼容 Agent Skills 的客户端
git clone <this-repo> <你的 skills 目录>/movie-finder
```

### 2. （可选，推荐）安装夸克官方 skill，解锁自动转存

只有想让 agent 帮你**直接存进夸克网盘**时才需要：

```bash
# 在 Hermes 里
hermes skills install quarkclouddrive
```

或者让 agent 自己去装。装完首次使用会引导你授权登录（扫码一次即可）。

**没装也能用**：skill 会退化成「找链接 + 报给你 + 你自己点」，只是少了自动转存和自动上传字幕。

### 3. 确认依赖

| 依赖 | 用途 | 没有会怎样 |
|---|---|---|
| `curl` | 抓网页 / 下载 | macOS / Linux 自带 |
| `bsdtar` | 解压字幕 RAR/ZIP | macOS 自带（Linux 装 `libarchive-tools`）；也可以用 `unrar` / `7z` |
| Python 3 + `Pillow` | 读字幕站验证码 | 没装就没法自动过验证码，只能手输 |
| 浏览器工具（`browser_exec` 等） | 抓 SPA 站 / 过验证 | 部分站点抓不到 |

`Pillow` 装法：`pip install pillow`

---

## 配置（改这几项就能适配你自己）

skill 里出现的这几项**都可以按自己习惯改**，改在下方「用户偏好」一节即可：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `preferred_netdisk` | `quark` | 目标网盘。改成 `baidu` / `115` / `xunlei` / `aliyun` 就优先筛那家的链接 |
| `delivery_dir` | `影视/影视资源` | 转存到网盘里的哪个目录（需已存在） |
| `subtitle_dir` | `~/Downloads/` | 字幕下载到本机哪个目录 |
| `quality_priority` | Remux > WEB-DL > WEBRip > HDTV | 画质排序偏好 |

---

## ⚠️ 依赖声明（诚实标注来源）

本 skill 的**主体是自写的方法论**，包含两部分：

| 部分 | 归属 | 内容 |
|---|---|---|
| **找片** | ✅ 本 skill | 站点清单、showpaw 抓取流、验活规则、画质排序、报告格式 |
| **抓字幕** | ✅ 本 skill | zimuku 过验证码、三段跳下载、bsdtar 解压、选版规则 |
| **`quarkclouddrive`** | ❌ **夸克官方**（`quarkclouddrive_816db00f`，v1.0.20+） | 转存 / 追更 / 上传 / 搜索 |

**`quarkclouddrive` 不是本 skill 的一部分**，是夸克官方发布的第三方 skill。本 skill 只在「要存进夸克网盘」时调用它的 CLI，**像调用一个外部工具**。它的内部规则（session-id 格式、msg 原样输出、目录参数禁止自动填充等）归它自己管，本 skill 不改它、不复制它的内容，只按接口调用。

**说人话**：找片和字幕是这个 skill 自己攒的本事；夸克那个只是搬东西的手推车。

---

## 用户偏好（默认值，可按上面「配置」一节修改）

- **默认网盘**：`quark`（夸克）。改这一项即可切换。
- **画质优先级**：
  1. **Remux**（蓝光原盘无损压回 mkv，可直接在线看）
  2. **WEB-DL**（DV / HDR10+ 优先，杜比视界 + 杜比全景声）
  3. **WEBRip**
  4. **HDTV / 录制**
  5. 其他
  - 同资源有杜比选杜比（DV + Atmos > 仅 Atmos）。
  - WEB-DL 里 Atmos 是常态，**Dolby Vision（DV）才是真分级关键**。
- **不可直看**：蓝光原盘 ISO / BDMV 目录（网盘解析不了光盘镜像）。碰到只有 ISO 的，主动找 Remux 替代，或回报无 Remux 让用户决定。
- **交付形态**：先在聊天里报链接 + 推荐，**用户点头后才转存**。不要只丢链接就完事。
- **用户说的「要最高画质」是硬要求**——不要拿低码版凑数（原话：「别图省事，我要最高画质的」）。

---

# 第一部分：找片

## 🚨 铁律：说「没有」之前必须过完这四关

**这是被真实使用反复教训出来的规则：不要图省事、不要过早下结论。** 这一节是本 skill 最重要的东西，比任何站点清单都重要。

说「这个资源没有」之前，**四条全部满足才允许开口**：

| # | 关卡 | 具体标准 |
|---|---|---|
| 1 | **层级走完** | 主力站 → 四个备选站 → 外部扒的站（腾讯频道 / linux.do 快照 / kuake5 / suenen / kkpans / BT），**一层都不能跳** |
| 2 | **关键词试过变体** | 中文名、英文名、`S01E05`、`E05`、`第5集`、`05` 都试一遍 |
| 3 | **内容而非标题** | 看过**文件列表**，不是只看标题。标题写「更04集」不代表里面没有 E05；标题写「全8集」也不代表真有 8 集 |
| 4 | **失败原因说清楚** | 区分「站里没有」/「我打不开」/「链接失效」/「要登录」——**这四种完全不是一回事，不能都叫"找不到"** |

**违反这条的实际代价**（2026-10-29 真实发生，三次）：

- 猜搜索参数 `?q=` → 三个站 404 → **误判「辅助站零命中」**，实际是参数全错
- 网页只渲染出第一个文件 → **误判「这个分享只有一集」**，实际有六集
- 没查 kkpans → **误判「E05 的 4K 中文圈确实没有」**，实际完整 S01E01-E06 就在那
- 用户追问「所有的站都拿不到？」才逼出正确答案

**正确姿势**：
- 卡住时先怀疑**自己的方法**（参数对不对？渲染完没有？命令有没有更直接的？），不要先怀疑「资源不存在」
- 有官方 CLI 能用就用 CLI——`share-detail` 读分享内容，比浏览器渲染可靠 10 倍
- 真的找不到时，**报告"我试了哪些、各自怎么失败的"**，而不是给一句「确实没有」

## 检索顺序（维护者实践总结的升级路径）

```
第 1 层  主力站：showpaw
           ↓ 找不到
第 2 层  合集站：kkpans（整季打包，一眼看到 S01E01-Exx / 总体积）
           ↓ 找不到
第 3 层  单集站：qkyunso → time1080 → 4kzn → kuakes
           ↓ 还找不到
第 4 层  外部扒的站：腾讯频道 / linux.do 快照 / kuake5 / suenen / BT 站（torrentdownloads）
```

**不要跳层**：主力站没收录 ≠ 直接跳第 4 层。先在合集站和单集站各搜一遍（覆盖不同上传者，常互补），全都没有才往外走。

> **缺单集时优先找「整季合集」而不是继续找单集。** 单集源容易跳集（某一集只有低码 mp4），但整季打包的分享通常一次到齐——同一个剧的 `S01E01-E06` 一整包往往比逐集找更全。标题里出现 `S01E01 - E06` / `全 N 集` + 总体积（如 34.8GB）的，就是这类。

## 资源站清单

**搜索 URL 必须用下面这张表里的格式**（`?q=` 一律无效，会 404）：

| 站名 | 搜索 URL 格式 | 登录 | 实测结果 |
|---|---|---|---|
| **showpaw**（主力） | 站内搜索框（SPA，`?s=` 无效） | 不需要 | ⭐ 5 部片命中 4 部 |
| **time1080**（资源量最大） | `https://v.time1080.xyz/s.php?wd=<关键词>` | 不需要 | ⭐ **157 条命中 / 91 个夸克**，但**下载链有 Cloudflare Turnstile**，agent 点不开，要用户自己点 |
| **kkpans**（第 2 层，实测最全） | `https://www.kkpans.com/?s=<关键词>` | 不需要 | ⭐ **整季合集首选**：一眼看到 `S01E01-E06 / 34.8GB` 这种完整包，夸克链接直接可抓 |
| qkyunso | `https://qkyunso.com/search?keyword=<关键词>` | 不需要 | ✅ 有覆盖但**更新滞后 3-7 天** |
| 4kzn | `https://4kzn.cc/?post_type=book&s=<关键词>` | 不需要 | ⚠️ 有搜索页但**常 0 条具体资源** |
| kuakes | `https://kuakes.com/?s=<关键词>` | 不需要 | ❌ 实测「搜不到相关内容」（冷门剧零覆盖） |
| haimian（补充） | 走 `web_search` + `site:haimian.eu.org` | 不需要 | Cloudflare 严，本体进不去 |
| panku8（补充） | 走 `web_search` + `site:panku8.com` | 不需要 | 聚合搜索，`/res/<hash>` 是详情页，Cloudflare |
| sidhub（补充） | 走 `web_search` + `site:sidhub.cc` | 不需要 | 磁力/BT 兜底 |
| **torrentdownloads.me**（磁力） | `https://www.torrentdownloads.me/search/?search=<关键词>` | 不需要 | ⭐ **唯一能 curl 直出 magnet 的公开 BT 站** |

### time1080 的特殊性（重要）

它是**资源量最大的站**（搜「幻视任务」157 条 / 91 个夸克），但**agent 拿不到最终链接**，机制已挖到底：

1. 每条资源是 `<a class="res-it">`，`href="/go.php?k=<base64>&g=<base64>"` —— **页面里的 href 是完整的**（打印时看到的 `...` / `***` 是脱敏，见下方「通用」第一条，不要误判成页面截断）。
   > **不要把 base64 打印到 stdout**，直接解析到文件再用（`html.unescape` 解 `&amp;`）。
2. `go.php` 的 `g` 参数**跟 cookie 会话绑定**：
   - 无 cookie → `403 资源访问凭证已失效`
   - 带 cookie → `429 请先完成人机验证`
3. 真正卡点是 **Cloudflare Turnstile**（`app2.js` 的 `ensureHuman()`：点击后先过 Turnstile，POST `/turnstile_gate.php`，通过才 fetch `/go.php`）。
4. 通过后返回流式 JSON，`display_mode: "qrcode"` → 弹 `/qr.php?t=...` 二维码，让用户用网盘 App 扫码。

**不要试图绕过 Turnstile**——那正是拦自动化的机制。

**正确用法**：
- 把它当**「有没有」的判定站**：搜得到 → 说明资源存在
- 需要链接时**让用户自己点**（真人能过 Turnstile），他会看到弹窗里的**文字链接**（页面配置 `V_QR_LINK=true`，二维码下面同时显示链接原文）
- 他把链接复制给 agent，agent 再验活 + 转存 + 配字幕

**已提取完整 go.php 链接的脚本**（备用）：
```python
import re, html
s = open('/tmp/t1080.html', encoding='utf-8', errors='ignore').read()
for m in re.finditer(r'<a class="[^"]*res-it[^"]*".*?</a>', s, re.S):
    h = re.search(r'href="([^"]*)"', m.group(0), re.S)
    if h:
        u = html.unescape(h.group(1))
        if u.startswith('/go.php'):
            print('https://v.time1080.xyz' + u)   # 需带同一 cookie 会话才能用
```

### 辅助站实测结论

四个"辅助站"不是"找不到资源"，而是**搜索 URL 全写错**（`?q=` 全部 404）。修正后：
- **time1080 资源最多但被 CF 挡** → 只能当判定站
- **qkyunso 能用但更新滞后** → 比主力源慢 3-7 天
- **4kzn / kuakes 覆盖差** → 冷门剧基本零命中

### 搜索参数的两个技术细节

- **中文关键词一律 URL-encode**（`urllib.parse.quote`）再拼进 URL。raw 中文有时能过但不稳，encode 后 qkyunso / time1080 都吃。
- **qkyunso 搜索结果页偶发返回 `404 Not Found nginx`**（页面本身是好的，重访即恢复）：用 `new_tab` 带 encode 后的完整 URL 重新打开一次，不要因此判定该站无数据。

同片在不同站的结果**往往是互补的**（不同上传者/线路），全搜一轮比反复重搜同一站有效。

## 第 1 步：showpaw 站内搜索

```python
goto_url("https://www.showpaw.xyz/")
wait_for_load()
fill_input("input[placeholder='搜索影视剧名称…']", "<片名>")
# 点 innerText === '搜索' 的 button
# URL 跳 /movie/<id> 或 /tv/<id>（直接命中）
#   或停在根路径的「找到 N 个相近作品」消歧页
```

**关键**：showpaw 是 SPA，`?s=` 不参与搜索，**必须走站内搜索框**。

## 第 2 步：等渲染完成

详情页 body 会先出现「正在为你查询资源」占位文案，**轮询 `document.body.innerText` 直到这句消失**（首次常需 5–30 秒）。没消失就抓，只会拿到骨架。

## 第 3 步：消歧（同名多版本）

搜同名/近名返回 ≤20 个候选，每个是 `<button class="v4-disambig">`，文本按「片名 / 英文名 / 评分 / 年份 / 类型」排列。
**按年份 + 类型选**（同名剧/动漫/重制靠年份和「剧集」标签识别）。

## 第 4 步：抠链接（按文档顺序配对）

DOM 是 React 渲染的，标题卡和「打开」按钮可能在不同子树。**用 TreeWalker 按顺序配对最稳**：

```js
document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT)
// 顺序遍历，把 pan.quark.cn/s/<hash> 和对应标题一一配对
// 同名 hash 出现多次（mobile+desktop 双布局）要 Set 去重
```

返回顺序就是 showpaw 列表顺序（画质从高到低）。

## 第 5 步：逐条验活 ⭐ 必做

```python
for h in hashes:
    goto_url(f"https://pan.quark.cn/s/{h}")
    wait_for_load(); time.sleep(4)
    body = js("document.body.innerText")
```

| bodyText 含 | 判定 |
|---|---|
| 「共 N 个文件」「永久有效」+ 文件名 | ✅ 活链 |
| 「该分享已失效」/「分享已被取消」/「文件已被删除」 | ❌ 死链，剔除 |
| 只有登录墙 | ⚠️ **不算失效**（用户已登录时会自动转存） |

**showpaw 标的「已验证有效」不可信**——那只是它上次抓取的快照。**必须自己打开验。**

**文件夹型分享要点进去看**：bodyText 只给一个文件夹名（可能乱码化，如 `xxx灭xxx`），要点开才看到真实文件名（`Annihilation.2018.2160p.ass`）。文件名的分辨率/编码/音轨标签是判断档位的唯一依据。

**数量策略**：≤6 条全验；>8 条只验前 3（top picks）+ 后 1（兜底），中间注明「未验活」。

## 第 6 步：兜底（主力站没有时）

按顺序：

1. `web_search` + `site:panku8.com` / `site:haimian.eu.org`
2. `web_search` + `"<片名>" 夸克网盘 4K`
3. **腾讯频道** `pd.qq.com/g/<id>/post/<pid>` —— **DOM 里有明文夸克链接**，`browser_exec` 直接抓 href
4. **linux.do** 帖子 —— 搜索快照正文里常带 `https://pan.quark.cn/s/<hash>`
5. 酷资源站 / kuake5 / suenen 的**搜索快照**（本站要登录/回帖才给链接）
6. 磁力兜底 → `torrentdownloads.me`

**明文链接照样要验活**——明文 ≠ 存活。

**兜底拿到的要在报告里说明来源**（「主力站未收录，从外部搜到」）。

## 第 7 步：报告给用户

按画质排序，标明：**规格 / 体积 / 字幕 / 是否验活**，给出推荐项 + 一句话理由。

```
## 首选：4K Remux 58GB
https://pan.quark.cn/s/xxx
- 1080p BluRay / x265 HEVC 10bit / 58.02G / 18 seed
- 理由：无 REMUX 时这是质量上限

## 次选：2.79GB（种子最健康）
...
```

**等用户拍板，不要自动转存。**

---

# 第二部分：抓字幕

**这一部分和找片源同样重要**——很多情况下用户已经有片源了，只是**字幕不满意**（翻译腔太重 / 没有双语 / 缺集 / 时间轴对不上 / 只有硬字幕）。

## 什么时候单独用这部分

用户说下面这些话时，**跳过找片，直接走字幕流程**：

- 「这个字幕翻译有问题」
- 「有没有中英双字的」
- 「帮我找个字幕」
- 「这集没字幕」
- 「字幕时间轴对不上」
- 「只有硬字幕，想要外挂的」

**关键：不要重下同一份。** 同一部片在同一站通常有多个版本，见 2.4「换版本」一节。

目标目录：`$subtitle_dir`（默认 `~/Downloads/`，scratch 24h 自动清，不要放那）。

备用域名（zimuku）：`srtku.com` / `zmk.pw`（同一站）。

## 2.1 打开站点，遇验证码

```python
new_tab("https://zimuku.org/")
wait_for_load(); time.sleep(4)
# body 含「验证」→ 进 2.2
```

## 2.2 读验证码（自己读，不发用户）

5 位数字的图片验证码（BMP base64）：

```python
from PIL import Image
import base64, io, os
src = js("document.querySelector('img.verifyimg').src")
im = Image.open(io.BytesIO(base64.b64decode(src.split(',',1)[1])))
im = im.resize((400, 108), Image.LANCZOS)   # 必须放大
p = "/tmp/zimuku_captcha.png"   # 任意可写临时路径
im.save(p)
```

**规则**：
- 必须放大到 400×108（原图 100×27，斜纹干扰读不准）
- **自己识别直接填，不发给用户核对**
- 读错就刷新重读，别硬填试错
- 实在看不清才说「这码我读不准，帮我看一眼」

## 2.3 过码 + 搜索（必须同一次 browser_exec）

⚠️ **最大坑**：`browser_exec` 守护进程超时/断连 → 验证码 cookie 失效 → 白过。
**「填码 → 提交 → 搜索」必须一口气跑完。**

```python
fill_input("#intext", "<验证码>")
time.sleep(0.3)
js("document.querySelector('input[type=submit]').click()")
time.sleep(5)
assert "验证" not in js("document.body.innerText")

# 用站内搜索框，不要 goto /search?q=...（会重新触发验证）
fill_input("input[name=q]", "<片名英文>")
time.sleep(0.3)
js("document.querySelector('form').submit()")
time.sleep(4)
```

守护进程断了就重开会话重来，别在旧会话里反复试。

## 2.4 选字幕

| 优先级 | 维度 |
|---|---|
| 1 | **双语** > 纯中文 |
| 2 | **特效字幕**（压制组带样式）> 官方简体 |
| 3 | **release 名与资源完全匹配**（时间轴才准） |

**匹配检查**：字幕文件名和影视资源文件名并排比，分辨率/来源/编码/组名一致才稳。

**周更剧**：字幕常打包成 `E5-6` 合集，比追单个文件省事。

**用户说「这份字幕翻译有问题」时**：不要重下同一份。特效组为了视觉常润色台词；官方字幕逐字准确但没特效。**两类互补不替代**——换另一版本，或列全让他挑。

## 2.5 抠下载链接

`curl` 直连详情页会触发验证，但**下载链接本身可以 curl**（带 referer 就行）。先从浏览器拿路径：

```python
goto_url("https://zimuku.org/detail/<id>.html")
d = js("document.querySelector('#down1')?.getAttribute('href')")   # → /dld/<id>.html
goto_url(f"https://zimuku.org{d}")
# 从页面抢 /download/<b64>/svr/d0
```

## 2.6 三段跳下载

```
详情页 /detail/<id>.html
  → 下载页 /dld/<id>.html        （5 个线路：d0/d1/l0/l1/y0，base64 路径）
  → /download/<b64>/svr/d0
  → RAR / ZIP
```

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
curl -sL -A "$UA" --max-time 120 -e "https://zimuku.org/dld/<id>.html" \
  "https://zimuku.org/download/<b64>/svr/d0" -o /tmp/sub.rar -D /tmp/hdr.txt
```

校验：`content-length` vs 页面标注大小、`file` 确认 RAR/ZIP。

## 2.7 解压落盘

```bash
bsdtar -tf /tmp/sub.rar            # 先看内容，防路径穿越
bsdtar -xf /tmp/sub.rar -C "$subtitle_dir"        # 默认 ~/Downloads/
md5 -q "$subtitle_dir"/<每个文件>
```

**macOS 没有 unrar / unar / 7z 时用 `bsdtar`**（自带 libarchive，支持 RAR5）。

## 2.8 报告

文件名、大小、MD5、语言、格式、制作/校订组、上传时间、详情页链接，以及**是否与资源 release 匹配**。

---

# 第三部分：转存到网盘

> **夸克 = 自动**（调用 `quarkclouddrive` 官方 skill）；**其他网盘 = 交给用户手动**。
> `quarkclouddrive` 的约束（session-id 格式、msg 原样输出、目录参数禁止自动填充等）以它自己的 SKILL.md 为准，本 skill 只按接口调用。

## 3.0 非夸克网盘怎么处理

如果 `preferred_netdisk` 不是 `quark`（或资源只有百度/115/迅雷/阿里/UC/光鸭链接）：

1. **照常找、照常验活**（能打开就说明链接有效）
2. **报告时把链接按网盘分组列出来**，标明每个链接的网盘类型、画质、大小
3. **明确告诉用户**：「这些网盘的自动转存本 skill 做不到，需要你自己点开保存」
4. 如果用户装了对应网盘的 CLI / skill，按那套来；没有就停在「给链接」这一步

**不要**因为「不是夸克」就直接说没有资源——**找链接和转存是两件事**。

## 3.1 前置（每次调 CLI 前必跑）

```bash
cd ~/.hermes/skills/quarkclouddrive
bash scripts/install.sh          # 环境检查 / 更新
```

## 3.2 固定交付目录

**目标目录由配置项 `delivery_dir` 决定**（默认 `影视/影视资源`）。

```bash
# 定位目录 fid
node scripts/quark-drive.cjs search --keyword "<目标目录名>" --search-type dir \
  --session-input "<用户原话逐字>" --session-id "<时间戳-6位随机>"
```

## 3.3 转存正片

**⭐ 先列清楚分享里到底有什么，再决定存哪些**——用 `share-detail` 直接读分享的子目录，**不要靠浏览器滚动**（React 列表分页，网页上通常只渲染出第一个文件，会误判"只有一集"）：

```bash
# 1. 拿顶层（返回 share_info.first_fid = 顶层文件夹 fid）
node scripts/quark-drive.cjs share-detail --url "https://pan.quark.cn/s/<hash>" ...

# 2. 用 first_fid 翻子目录，列出真实文件名 + 大小
node scripts/quark-drive.cjs share-detail --url "https://pan.quark.cn/s/<hash>" \
  --pdir-fid "<first_fid>" --size 50 ...
```

**这一步是判断「分享里有没有那一集」的唯一可靠办法**，比打开网页看快，也不受渲染分页干扰。

```bash
# 3. 只存需要的文件（--fid-list 用上一步拿到的分享内 fid）
node scripts/quark-drive.cjs saveas \
  --url "https://pan.quark.cn/s/<hash>" \
  --fid-list "<分享内 fid>" \
  --to-pdir-fid "<目标目录 fid>" \
  --session-input "<用户原话逐字>" --session-id "<同一个 id>"
```

## 3.4 追更（周更剧核心）

```bash
# 1. 查新增
node scripts/quark-drive.cjs get-share-update-files --url "https://pan.quark.cn/s/<hash>"
# 2. 只存新增（自动进上次的目录）
node scripts/quark-drive.cjs saveas-update --url "https://pan.quark.cn/s/<hash>"
```

**周更剧出新集，先查更新，不要重新找片源**——同一条链接是同一部剧的历史载体。

**⚠️ 更新列表里常混凑数文件**：上传者会把同一集同时放一份 4K mkv（5–7G）和一份低码 mp4（1.5–2G，常命名 `05.mp4` / `06.mp4`），还夹带预告花絮。
**先看 `files[]` 的 `size` 和 `title`，只挑体积达标的 4K 正片**：

```bash
node scripts/quark-drive.cjs saveas --url "<原链接>" \
  --fid-list "<只挑中的 fid>" --to-pdir-fid "<剧集文件夹 fid>" ...
```

`saveas-update` 只在「新增内容全是正片」时才用。

## 3.5 上传字幕

周更剧的正片文件夹里通常有字幕子目录（常见名 `[zmk...`）。先 `browse --parent-fid <剧集文件夹 fid>` 找它的 fid：

```bash
node scripts/quark-drive.cjs upload <字幕1> [<字幕2>] \
  --parent-fid "<字幕子文件夹 fid>" \
  --session-input "<用户原话逐字>" --session-id "<同一个 id>"
```

**字幕也要进网盘，不能只落本地的 `$subtitle_dir`。**

## 3.6 硬约束（来自官方 skill，遵守）

- `--session-id` 格式 `{Unix时间戳}-{6位随机}`，**同一次对话全程复用同一个**
- `--session-input` 必须是**用户原话逐字**，不得改写/摘要
- **`--to-pdir-fid` 禁止自动填 `0`**——他指定了目录就用他指定的；没指定就省略走默认
- 搜索结果**只能以 Markdown 表格输出、只展示前 5 条**，且要展示 `check_all_link` 完整 URL 和 `browse_hint` 原文
- `get-share-update-files` / `saveas-update` 成功后**必须原样完整输出 `msg`**，禁止改写/扩写/加前后缀

---

# 完整交付链

```
找片 → 验活 → 报推荐 → 用户点头 → 转存正片 → 抓字幕 → 上传字幕
```

**停在转存正片 = 让用户自己搬字幕。** 这不是完整交付。

---

# 踩过的坑（不要再踩）

## 找片

- **同片多版本**：同名≠同部。《三体》有腾讯剧/动画/电影，《大话西游》有重映加长版。排序前先看年份/UHD/Remux/DV。
- **剧集/动漫**：要带季号/集数范围。蓝光原盘常整季一包，WEB-DL 单集常见。
- **showpaw「已验证有效」不可信** —— 标笶是它上次抓取的快照，分享被删/取消后不实时同步。**报告前逐条打开验。**
- **showpaw 两种「没资源」提示意思不同**：
  - 「**还在院线**，网盘资源还没出」+「新片一般首映 3-4 周后」= **真没有**。如实说没有 + 给首映日期 + 提议到时间再查。**不要在磁力圈翻枪版硬凑**（HC 枪版 1-2G，画质糊，分享几天就死）。
  - 「**刚开播**，网盘资源还没跟上」+「新剧一般首播 3-7 天后更新」= **已开播，只是慢几集**。**照常走补充站**，通常能拿到已播集数的 4K DV/HDR。看到「刚开播」就报「没有」是错的。
- **周更剧在中文网盘常「跳集缺 4K」**：某个源里其他集都是 5–7G mkv，某一集只有个 1.5G 的 `NN.mp4`。**这只说明这一个源缺，不等于全网没有。**
  - ❌ 不要拿低码版凑数（用户会明确拒绝（「别图省事，我要最高画质的」））
  - ❌ **不要只查一个源就报「没有」**——先把资源站清单里能出结果的那几家（showpaw / kkpans / time1080 / qkyunso）和兜底渠道跑完，再下结论。用户会把「只查了一处就说没有」当成偷懒。
  - ✅ **换思路：找整季合集**。单集源跳集时，去 kkpans 找 `S01E01-Exx` 一整包的分享——经常一次到齐，且能用 `share-detail --pdir-fid` 列全确认。
  - ✅ 穷尽之后仍没有，才如实报「中文网盘圈目前只有低码版，4K 在 BT 圈有但需注册拿磁链」，并说明已查过哪几家
  - ✅ 给两个选项：「等几天等中文源补齐」/「你自己去 BT 站拿磁力」
- **冷门 cult / 老片在中文网盘圈可能完全不存在**：主力站全没收录 ≠ 资源没流通。必须走 BT 兜底，并老实说「中文网盘圈无收录，从 BT 圈找到」。
- **Cloudflare 反爬的站（haimian / panku8 / 1lou / linux.do）**：`web_extract` 报 `Blocked: URL targets a private or internal network address`，`browser_exec` 弹「请稍候…」/「Sorry, you have been blocked」。**走 `web_search` 快照**。
- **PT/BT 站（ext.to / rutracker / 波兰站 ex-torrenty）走 browser_exec 也是死路**：Cloudflare Turnstile / hCaptcha 过不了，而且 magnet 按钮跳 `/login.php`。要磁链得用户自己注册。
- **公开磁力搜索引擎默认都会死**：btsow.bar 跳中转页、btsow.bz/.com `ERR_CONNECTION_CLOSED`、magnetdl 同、btdig 弹 recaptcha、cilixiong POST 后「没有搜索到」、1337x / thepiratebay 被挡、limetorrents 结果不全。
  **真实可用的只有 `torrentdownloads.me`**（server-rendered，curl 直出 magnet）：
  ```bash
  UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
  curl -sL -A "$UA" --max-time 15 "https://www.torrentdownloads.me/search/?search=<片名+组名>" -o /tmp/cur.html
  grep -oE 'href="/torrent/[0-9]+/[^"]*<关键词>[^"]*"' /tmp/cur.html | sort -u
  curl -sL -A "$UA" "https://www.torrentdownloads.me/torrent/<id>/" | grep -oE 'magnet:\?xt=urn:btih:[0-9A-Fa-f]{40}'
  curl -sL -A "$UA" "https://www.torrentdownloads.me/torrent/<id>/" | grep -oE 'Total Size:</span>[^<]+'
  ```
- **不要从搜索引擎快照里复制「磁链」字段**——快照里基本没有 magnet，写一个就是编的。
- **web_search 后端默认可能是坏的**：`web.search_backend: auto` 会先选 `web-openai-native`，那条路在客户端模式必失败。在 `config.yaml` 加 `web: { search_backend: firecrawl, extract_backend: firecrawl }`。改完看日志出现 `Web search via firecrawl` 就生效。
- **用户说的「夸克」可能是夸克浏览器，不是夸克网盘**：夸克浏览器（UC 内核，带视频解析/AI 总结）和夸克网盘（`pan.quark.cn`）是两个产品。他说「用夸克看」「我夸克登录了」时先分清。**网盘登录态 ≠ 浏览器登录态。**
- **不要直接猜默认网盘**：资源站页面可能混着阿里/磁力/迅雷，必须从链接域名筛。
- **杜比不是只有 Atmos**：Atmos 是音轨，DV/Dolby Vision 才是画质。要的是「DV + Atmos」双料。
- **⭐ 判定「分享里有没有那一集」必须用 `share-detail`，不要靠网页滚动**（2026-10-29 血的教训）：
  夸克分享页是 React 虚拟列表，滚动半天**只渲染出第一个文件**（E01），很容易误判「这个分享只有一集」。
  ```bash
  # 拿顶层 first_fid
  node scripts/quark-drive.cjs share-detail --url "https://pan.quark.cn/s/<hash>" ...
  # 列子目录全部文件
  node scripts/quark-drive.cjs share-detail --url "https://pan.quark.cn/s/<hash>" \
    --pdir-fid "<first_fid>" --size 50 ...
  ```
  同理 **`browse --all` 也可能只返回一页**（实测只回 5 条，实际 6 条）——要确认总数用 `search --keyword <片名> --stdout-only` 读 artifact JSONL 数一遍。
- **⭐ 服务器返回的 base64 参数看着像被截断，其实是 Hermes 的密钥脱敏**（2026-10-29 踩过）：
  time1080 的 `href="/go.php?k=...&g=eyJyIj...e500"`，我以为是站点把参数截断了，实际**文件里是完整的**——
  Hermes 的 secret redaction 把 base64 片段替换成 `...` / `***` 后才输出到 stdout。
  **解法：不要把 base64 打印到 stdout**，解析到文件/变量里直接用，只打印长度和 hash。
- **搜索参数绝对不能猜**：`?q=` 在 qkyunso/4kzn/kuakes/time1080 **全部 404**。正确做法是先打开首页，读表单：
  ```js
  [...document.querySelectorAll('form')].map(f => ({
    action: f.action, inputs: [...f.querySelectorAll('input')].map(i => i.name || i.placeholder)
  }))
  ```
  各家参数：qkyunso `?keyword=` / 4kzn `?post_type=book&s=` / kuakes `?s=` / time1080 `s.php?wd=` / kkpans `?s=`。
- **标题 ≠ 内容**：标题写「更新至04集」不代表里面没有 E05；标题写「全8集」也不代表真有 8 集（实测那条「全8集」的 4K 文件夹里只有一个 `01.mp4`）。**必须点进去看文件列表。**

## 字幕

- **不要把验证码截图发给用户**——他自己不用看，我读就行
- **不放大到 400×108 就不要读验证码**（100×27 读不准）
- **`goto /search?q=` 会重新触发验证**——必须用站内搜索框
- **「过码」和「搜索」不能拆成两次 browser_exec**
- **看到「请先登录」不要断言下载要登录**——zimuku 下载不需要登录，那提示是别的模块的
- **不要断言「.sup 夸克加载不了」**——**错。夸克全都能挂，.sup 特效字幕直接用。**
- **不要在守护进程断连后于旧会话里继续试**——重开
- **不要把字幕留在 scratch 目录**（24h 清）
- **不要只抓搜索结果第一条**——同片常有双语特效 + 官方简中多份
- **用户说「翻译有问题」时不要重下同一份**
- **不要编造文件名/大小/下载量**——全部实际抓到

## 通用

- **不要把「找链接」当成交付终点**。完整交付 = 找到 → 验活 → 报推荐 → 他点头 → 转存 → 字幕 → 上传。
- **不要把「这轮没用到」汇报成「这个渠道零命中」**。没实际按正确 URL 搜过就断言某站无效，会把可用渠道误判成废站，也会让他以为资源真的不存在。有两种场景必区分：①「我搜了，确实没有」——给实测结果；②「我这轮还没去那几个站搜」——直说未测，不要包装成结论。断言「某站没有」之前必须先实搜一次。
- **报告「没有」之前，先怀疑自己的搜索方式**。URL 格式写错、参数名写错、关键词没 encode，都会返回一个看起来像「没数据」的空白页——那是 404 或空结果，不是「站里没有」。先确认搜索入口真的生效（页面标题里带关键词、结果计数 > 0），再下结论。
  **新增站点或参数不确定时，先读表单再拼 URL**（5 秒，比猜错重试快）：
  ```js
  [...document.querySelectorAll('form')].map(f => ({action: f.action, method: f.method,
    inputs: [...f.querySelectorAll('input')].map(i => i.name || i.placeholder || i.type)}))
  ```
  拿到真实 `action` + `input.name` 再拼；各站参数名互不通（`keyword` / `s` / `wd` 都有）。
- **工具输出里的 `...` / `***` 可能是自己的脱敏器遮的，不是页面截断**。长 base64（签名、token、`go.php?k=..&g=..` 的 guard）打印到 stdout 时会被 Hermes 的密钥脱敏替换成省略号。
  **判断方法**：不看打印结果，直接用 `python3` 解析存到文件，再报 `len()`：
  ```python
  # 只打印长度和首尾，不打印内容 → 不会被遮
  print(f"href len={len(v)}")
  ```
  长度对得上（带 `=` 补齐的 base64 应有对应长度）就说明数据完整，只是显示被遮。
  **不要因为打印结果带省略号就断言「服务器截断了参数」并放弃**——这会让你把一个能用的站误判成死的。
- **撞到人机验证（Turnstile/reCAPTCHA）不是「做不到」，要说清墙在哪并给一步交接**。正确话术是三段：①我挖到了什么（链接在哪一层、卡在哪一个接口）②我卡在哪（哪个验证码，它本来就是拦自动化的）③你帮我做哪一下（复制弹窗里的文字链接 / 扫码）。**不要把「我拿不到」说成「转存不了」**——这是两件事，前者是获取环节，后者是写入环节。
- **同一部周更剧各集可能来自不同压制组**（E01–E04 是 A 组、E06 是 B 组），分辨率/音轨/字幕组会跟着变。**存之前在报告里说明组别不一致**，别让他以为是一整套。
- **删凭据类操作要问过再删**——本 skill 只做只读检索 + saveas/upload 写操作。

---

# 反面模式（不要做）

- ❌ **不要发豆瓣链接**（那是影评站，不是资源）
- ❌ **不要只发「非首选网盘」就当成没找到**——默认网盘是夸克，但用户要百度/115/迅雷/阿里时，照常找、照常报，只是转存交给用户手动
- ❌ 不要把磁力丢在前面凑数——它是兜底
- ❌ 不要被标题里的「4K」「高清」骗了——看标签是 WEB-DL / WEBRip / Remux
- ❌ **看到「4K原盘」「BD-100/BD-66」「BDMV」「ISO」要警惕**——大概率是 ISO 整盘，用户不会下
- ✅ **「Remux」是安全词**——文件名带 Remux 的 mkv 才可以推
- ❌ **「蓝光原盘」≠ Remux**：Remux 是抽流无损封装成 mkv（体积小、可直接在线看）；ISO/BDMV 是光盘镜像
- ❌ 不要拿到一份 DV 就停——有 DV + HDR10 双版本都要列
- ❌ **不要自动转存**——必须等用户点头
- ❌ **不要把 `quarkclouddrive` 的内容当成本 skill 的实现**——它是官方第三方，只调用
- ❌ **不要在只查了一两个站之后就宣布「全网没有」**——见开头「铁律」一节
