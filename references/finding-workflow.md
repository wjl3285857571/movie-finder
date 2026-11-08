# 找片全流程（详细版）

> 本文件由 `SKILL.md` v1.0.0 原样拆出（2026-11-09），文字未改，只做归位。

## ⚠️ 依赖声明（必读，别把别人的东西当自己的）

本 skill 的**主体是我们自己写的方法论**，包含两部分：

| 部分 | 是不是我们的 | 内容 |
|---|---|---|
| **找片** | ✅ 我们的 | 站点清单、showpaw 抓取流、验活规则、画质排序、报告格式 |
| **抓字幕** | ✅ 我们的 | zimuku 过验证码、三段跳下载、bsdtar 解压、选版规则 |
| **`quarkclouddrive`** | ❌ **夸克官方**（`quarkclouddrive_816db00f`，v1.0.20+） | 转存 / 追更 / 上传 / 搜索 |

**`quarkclouddrive` 不是本 skill 的一部分**，是夸克官方发的第三方 skill。我们只在"要存进夸克网盘"时调用它的 CLI，**像调用一个外部工具**。它的内部规则（session-id 格式、msg 原样输出、目录参数禁止自动填充等）归它自己管，我们不改它、不复制它的内容，只按它的接口调用。

**说人话**：找片和字幕是我们自己攒的本事；夸克那个只是搬东西的手推车。

## 🚨 铁律：说「没有」之前必须过完这四关

**这条规则来自真实使用的反复教训：不要图省事、不要过早下结论。** 这一节是本 skill 最重要的东西，比任何站点清单都重要。

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
- 一句「所有的站都拿不到？」往往能逼出正确答案

**正确姿势**：
- 卡住时先怀疑**自己的方法**（参数对不对？渲染完没有？命令有没有更直接的？），不要先怀疑「资源不存在」
- 有官方 CLI 能用就用 CLI——`share-detail` 读分享内容，比浏览器渲染可靠 10 倍
- 真的找不到时，**报告"我试了哪些、各自怎么失败的"**，而不是给一句「确实没有」

## 检索顺序（维护者实践总结的升级路径，按这个走）

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

## 第 0 层：不是影视也走这里（PanSou 网盘搜索）

电子书、课程、软件这类**拿片名搜不到的东西**，别在影视站里刨，走 PanSou —— 它聚合 Telegram 频道，直接按网盘类型给你夸克/百度/阿里/磁力链接。拿到的夸克链接，下游验活和转存跟影视那条线完全一样。

```bash
curl -s -m 90 -X POST 'https://so.252035.xyz/api/search' \
  -H 'Content-Type: application/json' \
  -d '{"kw":"<关键词>","cloud_types":["quark"],"src":"tg","res":"merge"}'
```

**两条硬规则**：`src=tg` 必须带（不带的全来源实测 60 秒超时），**超时不等于没有**（公开实例 60–90 秒是正常耗时，先加超时重试再下结论）。完整参数、返回结构和实测踩的坑见 `references/pan-network-search.md`。

## 资源站清单

**搜索 URL 必须用下面这张表里的格式**（`?q=` 一律无效，会 404）：

| 站名 | 搜索 URL 格式 | 登录 | 实测结果 |
|---|---|---|---|
| **showpaw**（主力） | 站内搜索框（SPA，`?s=` 无效） | 不需要 | ⭐ 5 部片命中 4 部 |
| **time1080**（资源量最大） | `https://v.time1080.xyz/s.php?wd=<关键词>` | 不需要 | ⭐ **157 条命中 / 91 个夸克**，但**下载链有 Cloudflare Turnstile**，agent 点不开，要用户自己点 |
| **kkpans**（第 2 层，实测最全） | `https://www.kkpans.com/?search=<关键词>` | 不需要 | ⭐ **整季合集首选**：一眼看到 `S01E01-E06 / 34.8GB` 这种完整包，夸克链接直接可抓。**参数是 `?search=` 不是 `?s=`**——`?s=` 会返回被 CDN 缓存的上一页内容（搜 A 却显示 B 的结果），极易误判成「0 结果」 |
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

搜同名/近名返回 ≤20 个候选，每个是 `<button class="v4-disambig">`，文本按「片名 / 英文名 / 评分 / 年份 / 类型」排列，**后面还跟着整段剧情简介**。

**点击用数组下标，不要用文本精确匹配**：

```js
[...document.querySelectorAll('button.v4-disambig')][1].click()   // 先打印 0..N 的 (片名/年份/类型) 确认下标
```

候选文本里塞着简介，`innerText === '片名'` 永远匹配不上；同一部片还可能同时出现重制版/剧集版两个条目。**先列出 `{i, 片名, 年份, 类型}` 四列，按下标点**，别边猜边点。

## 第 4 步：抠链接（按文档顺序配对）

DOM 是 React 渲染的，标题卡和「打开」按钮可能在不同子树。**用 TreeWalker 按顺序配对最稳**：

```js
document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT)
// 顺序遍历，把 pan.quark.cn/s/<hash> 和对应标题一一配对
// 同名 hash 出现多次（mobile+desktop 双布局）要 Set 去重
```

返回顺序就是 showpaw 列表顺序（画质从高到低）。

**配对抓出 0 条时先改抓法，别怀疑站点没资源**：标题通常在带子元素的容器里，按叶子节点 `innerText` 做正则匹配会全部落空（本 skill 上面的 TreeWalker 写法在某些页面就是 0 命中）。改成：先取全部 `a[href*="pan.quark.cn/s/"]` 去重，再对每个 `<a>` 向上找最多 5 层祖先，取第一个 `innerText` 长度 > 25 且含 `GB` / `REMUX` / `2160` / `1080` 的容器当上下文——标题和链接就配上了。

## 第 6 步：兜底（主力站没有时）

按顺序：

1. `web_search` + `site:panku8.com` / `site:haimian.eu.org`
2. `web_search` + `"<片名>" 夸克网盘 4K`
3. **腾讯频道** `pd.qq.com/g/<id>/post/<pid>` —— **DOM 里有明文夸克链接**，`browser_exec` 直接抓 href
4. **linux.do** 帖子 —— 搜索快照正文里常带 `https://pan.quark.cn/s/<hash>`
5. 酷资源站 / kuake5 / suenen 的**搜索快照**（本站要登录/回帖才给链接）
6. 磁力兜底 → `torrentdownloads.me`

**明文链接照样要验活**——明文 ≠ 存活。

**搜索结果里捡到的裸 `pan.quark.cn/s/<hash>` 经常是别的片**：`web_search` 会把不同页面的链接混排在一起，按搜索片段推断「这条就是《X》」会错得很离谱（实测三个裸 hash 分别指向少林足球、熊家餐馆、和一条已失效链接）。捡到 hash 先 `share-detail` 读一次 `share_info.title`，片名对上了再往下走；不要拿搜索片段当它的标题。

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

**60 Mbps 以上的碟版 Remux 要顺带提醒播放条件**：夸克在线播放会自动转码压缩，这种码率在线看基本是残废（实测只有 5 MB/s 量级）。报规格时带一句「要看真效果得下载到本地用播放器」，别等他看完糊了才解释。

**等用户拍板或选编号。确认后立即执行转存 + 字幕上传闭环，不要把链接丢给用户让他自己点。**
