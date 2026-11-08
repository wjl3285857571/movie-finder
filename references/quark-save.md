# 转存夸克全流程（详细版）

> 本文件由 `SKILL.md` v1.0.0 原样拆出（2026-11-09），文字未改，只做归位。

# 第三部分：存进夸克（调用官方 skill）

> 这一段是**调用 `quarkclouddrive`（夸克官方 skill）的接口**，不是我们自己的实现。
> 它的约束（session-id 格式、msg 原样输出、目录参数禁止自动填充等）以它自己的 SKILL.md 为准。

## 3.1 前置（每次调 CLI 前必跑）

```bash
cd ~/.hermes/skills/quarkclouddrive
bash scripts/install.sh          # 环境检查 / 更新
```

## 3.2 固定交付目录

**`文件/影视/影视资源`**（默认交付目录；按剧集/电影名建立子文件夹，字幕放剧集内的 `[zmk…` 子目录）。

**定位这个目录用 `browse` 逐层走下去，不要用 `search --search-type dir`**——后者实测返回 3000 条 `zh` / `ui` 之类的无关条目，翻不出真目录，照它做会得出「找不到影视资源目录」的错误结论。

```bash
# 1. 根目录找「影视」
node scripts/quark-drive.cjs browse --parent-fid 0 --all --page-size 100 ...
# 2. 进「影视」找「影视资源」，拿它的 fid
node scripts/quark-drive.cjs browse --parent-fid "<影视 fid>" --all --page-size 100 ...
```

拿到「影视资源」fid 后，**建子文件夹一律带 `--parent-fid`**：

```bash
node scripts/quark-drive.cjs create-folder --dir-path '<剧名>' --parent-fid "<影视资源 fid>" ...
```

⚠️ **不要用 `create-folder --dir-path '影视/影视资源/<剧名>'` 一步到位**：它不从网盘根解析相对路径，会在 `来自：Hermes/` 底下另建一套 `影视/影视资源/<剧名>` 空目录——文件没存到该去的地方，还留下一串空文件夹（CLI 没有 delete，只能请用户手删）。

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

### 多层目录要递归，一层不够

合集分享往往是 **分享根 → 系列文件夹 → 集数区间文件夹 → 具体文件** 三层。只翻第一层会看到 `101-170` `001-100` 这种**集数区间文件夹**（`dir: true`、size 0），不是文件——**必须拿它的 fid 再 `share-detail` 一次**，才能看到里面的 `164.zip`。

判读规律：
- 区间文件夹名（`001-100` / `101-170`）里的集数范围就是内容范围，但**要进一层核实**，别直接拿名字当结论
- 区间之上常常还有**散装单集**（`171.zip` … `176.mkv`）摆在系列文件夹里，和区间文件夹平级
- 所以「164 集往后」= **区间文件夹里的 164–170** + **系列层里的 171–176**，两处拼起来才是完整区间

递归脚本写法：拿上一层 `share-detail` 返回的 `dir: true` 条目 fid，逐个当 `--pdir-fid` 再调一次，把 `filename` 和 `fid` 累积到同一个列表，最后用正则 `re.search(r'(\d{3})', filename)` 算集数并排序。

```bash
# 3. 只存需要的文件（--fid-list 用上一步拿到的分享内 fid）
#    目标目录优先用 --to-pdir-path：CLI 自己解析路径，少一次 fid 查询
node scripts/quark-drive.cjs saveas \
  --url "https://pan.quark.cn/s/<hash>" \
  --fid-list "<分享内 fid>" \
  --to-pdir-path "影视/影视资源/<剧集或电影文件夹名>" \
  --session-input "<用户原话逐字>" --session-id "<同一个 id>"
```

**`--to-pdir-path` 和 `--to-pdir-fid` 二选一，优先 path**（官方 help 明确推荐）。`search` / `browse` 返回的 fid 常见形态是 `~1xxxx…|yyyy` 这种带竖线的长串——**它就是可用 fid，原样传给 `browse --parent-fid` / `--to-pdir-fid` 就行**，不要因为「看着不像网盘 fid」去截断或改用其它 id。

**转存完必须回读验证**：`saveas` 返回 success ≠ 文件已到位。用 `browse --parent-fid <目标目录>` 再看一遍文件名和体积，确认那一集真在。`saveas` 的返回里 `save_as.min_save_file_size` 是实际写入的字节数，可用来和分享里的大小对账。

### 整季 / 多季合集：别直接 `--save-all`

`saveas --save-all` 会把分享**自带的包装目录**整串搬进网盘。一个「全两季」分享的真实结构常是：

```
分享根 🔥🔥🔥剧名 第二季(2025)…_kkpan  /  剧名  /  S01 / 4K HDR / *.mkv
                                              └ S02 / 4KHDR / *.mkv
```

`--save-all` 落到 `影视/影视资源/剧名/` 之后变成三层空壳嵌套，最外层还挂着上传者写的带 emoji 标题（名字里说「第二季」，里面两季都有），用户点进去完全找不到集数。

**正确做法**：`share-detail` 递归到能看见 `S01` / `S02` 那一层，拿这两个文件夹的 fid 用 `--fid-list` 存——落下来就是干净的 `剧名/S01`、`剧名/S02`。

已经 `--save-all` 存进去了别重存，用 `move` 把季文件夹提上来：

```bash
node scripts/quark-drive.cjs move "<S01 fid>" "<S02 fid>" --target-fid "<剧名 目录 fid>" ...
```

提完剩下的那串包装空目录**删不掉**（CLI 无 delete 命令）。汇报时明说「有个空文件夹是原分享的包装目录，需要你在 App 里手删」，不要假装目录是干净的。

**合集存完要按季报数**：分别 browse `S01` / `S02`，从 `data.total` 和 artifact JSONL 里数出「几个 mkv + 有没有字幕夹」，再和分享里对账。只报总体积等于没验证。

## 3.4 追更（周更剧核心）

**第一步永远是 `get-share-update-list`**——不记得某部剧的分享链接时，它一次性列出所有「转存过且有更新」的分享（含标题、`share_url`、更新时间），按标题匹配到目标剧。**不要靠回忆或重新搜索去找那条链接**：同一条分享是这部剧的历史载体，换链接会丢掉「上次存到哪」的目录绑定。

```bash
# 1. 列出所有有更新的分享，按标题匹配目标剧，取 share_url
node scripts/quark-drive.cjs get-share-update-list \
  --session-input "<用户原话逐字>" --session-id "<同一个 id>"

# 2. 查这条分享新增了哪些文件（files[] 含 title / size / fid）
node scripts/quark-drive.cjs get-share-update-files --url "https://pan.quark.cn/s/<hash>"

# 3. 只存挑中的文件（按下方「凑数文件」规则筛选，不要直接 saveas-update）
node scripts/quark-drive.cjs saveas --url "https://pan.quark.cn/s/<hash>" \
  --fid-list "<挑中的 fid>" \
  --to-pdir-path "影视/影视资源/<剧集文件夹名>"
```

**「最新两集」不等于「本次新增」**：`get-share-update-files` 只报新增，用户要的是最后 N 集的完整状态。先 `browse` 看剧集文件夹已经有哪些集，把「已有」和「本次新增」拼起来核对，汇报时逐集写明状态（如「E06 已有 / E07 本次新增」），别让用户自己数。

**「已导入」不等于「已看过」**：他描述进度（「我看过第六集，你导入了第七集，就差第八集」）时按字面理解——已存进网盘 ≠ 已经看完。不要替他推断看过哪几集，汇报只用「网盘里有哪些 / 这次新增哪一集」的客观口径。

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

**字幕也要进网盘，不能只落 `~/Downloads`。** 上传后同样用 `browse` 回读确认。

**字幕文件名对齐正片**：把正片的完整文件名去掉扩展名再加 `.srt` / `.sup`，播放器才会自动挂上。压制组名不一致（正片 `-SmartWeb`、字幕 `-RAWR`）时手动选也能用，但对齐后体验更好。

**空间余额要转达**：`saveas` / `upload` 成功时若 `notice.kind == "member_hint"` 且文案含「存储空间已不足」，在汇报里带一句——每部 4K Remux 吃 50–90G，连着存几部就会顶。

## 3.6 硬约束（来自官方 skill，遵守）

- `--session-id` 格式 `{Unix时间戳}-{6位随机}`，**同一次对话全程复用同一个**
- `--session-input` 必须是**用户原话逐字**，不得改写/摘要
- **`--to-pdir-fid` 禁止自动填 `0`**——他指定了目录就用他指定的；没指定就省略走默认
- 搜索结果**只能以 Markdown 表格输出、只展示前 5 条**，且要展示 `check_all_link` 完整 URL 和 `browse_hint` 原文
- `get-share-update-files` / `saveas-update` 成功后**必须原样完整输出 `msg`**，禁止改写/扩写/加前后缀

# 完整交付链

```
找片 → 验活 → 报推荐 → 用户确认 → 转存正片 → 抓字幕 → 上传字幕
```

**停在转存正片 = 让用户自己搬字幕。** 这不是完整交付。
