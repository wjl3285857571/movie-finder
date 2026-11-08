# 字幕来源与补位方案

zimuku 是首选，但它不一定有你要的那一档。这份文件记：怎么一次看全 zimuku 的候选、特效组什么时候发、没有该档时去哪儿顶替。

## 1. zimuku：一次看全整部剧的字幕

搜索页 `/search?q=<片名>` **只渲染前 5 条**，「还有 N 个字幕，点击查看」点了也不展开。想要全量，从任意一条的详情页找面包屑里那个「剧名 (年份)」链接，指向：

```
https://zimuku.org/subs/<剧集id>.html
```

那页按时间倒序列出整部剧的全部字幕，格式是「字幕名 / 制作 / 校订 / 来源 / 下载次数 / 上传者 / 时间」。**从发布节奏一眼就能看出哪个组是成对发的**，比在搜索结果里翻得快。

## 2. 特效组按两集一包发，单集不存在

以 LEN-X 的中英特效为例，标题固定长这样：

```
幻视任务VisionQuest.S01E1-2.2160p...-LEN-X中英特效字幕.rar   SUP
幻视任务VisionQuest.S01E3-4.2160p...-LEN-X中英特效字幕.rar   SUP
幻视任务VisionQuest.S01E5-6.2160p...-LEN-X中英特效字幕.rar   SUP
```

规律：**1-2 / 3-4 / 5-6 成对发布，最后一集播完才出 E7-8 那包**。所以新一集刚上线时，没有同档 .sup 是正常的发布节奏，不是资源缺失——先说清这一点，再给顶替方案，不要含糊地说「这个字幕没有」。

解出来的文件名带的是**匹配的片源组名**（`-RAWR` / `-FLUX`），不是 `-LEN-X`。看到 `[zmk` 里是 `-RAWR.sup` 而来源是 LEN-X 包，不要以为是两套东西。

## 3. 备用源：assrt.net（射手网伪）

zimuku 没有同档时的第一顺位。它的 E2E 是**官方译本 + 双语 ASS**，不是图形特效，但比机翻强得多。

```bash
# 1) 搜（用英文 release 名）
https://assrt.net/sub/?searchword=VisionQuest

# 2) 详情（XML 渲染的 HTML，能列出所有变体 + 下载直链）
https://assrt.net/xml/sub/<803>/<803132>.xml

# 3) 下载（要带 referer，会 302 到 file0.assrt.net）
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
curl -sL -A "$UA" --max-time 120 -e "https://assrt.net/xml/sub/<803>/<803132>.xml" \
  'https://assrt.net/download/<id>/<文件名URL编码>.zip' -o /tmp/vq.zip
```

一个 zip 里通常有 9 份，按字形 × 语言 × 格式铺开：

```
.chs.ass  .cht.ass  .chs&eng.ass  .cht&eng.ass
.chs.srt  .cht.srt  .chs&eng.srt  .cht&eng.srt  .eng.srt
```

**要双语拿 `.chs&eng.ass`**（ASS 带样式，比 SRT 好看）。

### 陷阱一：assrt 的 `chs` 内容可能是繁体

文件名标 chs，正文却是「給你的 / 謝謝 / 什麽」。**先读一条再信文件名**，是繁体就转：

```bash
python3 -m pip install --quiet zhconv
```

```python
import zhconv
# 只处理 Dialogue 的文本字段（第 10 个逗号之后），不要整文件过度改写
parts = ln.split(',', 9)
parts[9] = zhconv.convert(parts[9], 'zh-cn')
ln = ','.join(parts)
```

双语 ASS 的中英是用硬换行 `\N{\rJap}` 拼在一行里的，所以对整段文本做 `zhconv.convert` 正好：它只换 CJK 字形，ASCII 英文原样不动。转完抽查：`哈囉 幻視` → `哈啰 幻视`。

### 陷阱二：assrt 条目更短，不是时间轴错

assrt 那份可能 659 条、末条 57:29，而 zimuku 那份 676 条、末条 1:02:14。**条数少常只是没有片尾歌词、合并了同屏双行**，不代表不同片源。必须按时间点抽样验证，方法见 `references/subtitle-quality-picker.md` 第 3 步。

## 4. 降级次序

1. 同档特效 `.sup`（LEN-X 包）——有就用，别拿别的凑
2. assrt 双语 `.ass`（转简中）——**最佳顶替**，中英双行
3. zimuku 官方译本中文 SRT——单语，最后手段
4. 机翻——不要往网盘里传

不论用哪个，都告诉用户这是哪一档、为什么不是他常用的那档、什么时候能换成同档。

## 5. 上传前固定动作

- 文件名对齐正片：正片文件名去掉 `.mkv` 加 `.ass` / `.src`，播放器才自动挂
- 落 `~/Downloads/`，不要留 scratch（24h 清）
- `upload --parent-fid <[zmk fid>` 后 `browse` 回读确认
- 旧的错版本挪进 `[zmk/旧版-<说明>`（CLI 没有 delete，用 `create-folder` + `move`）
