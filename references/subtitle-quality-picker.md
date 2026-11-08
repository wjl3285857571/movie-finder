# 同集多版本字幕：怎么选

一集常常有 2–4 份中文字幕候选，标题看着都像「简体中文」，实际差别是**时间轴来源**和**用语体系**。别凭下载量猜，把候选都下下来逐条比对——两分钟成本，能避免「看到一半发现是台湾腔」。

## 什么时候用

- 同一集在 zimuku 上有两个以上「简体中文」条目
- 一个写「官方译本 / 官方简体」，另一个写「繁转简 / 见字幕文件」
- 两个条目的下载量差很多，但标题说不清差别
- 用户说过「这个字幕翻译有问题」

## 步骤

### 1. 候选都走完三段跳

按 SKILL.md 2.5–2.6 分别下到 `/tmp/<dir>/sub_<id>.bin`。**不要只下第一个**——下载量和译文质量没有强相关：一份繁转简可能因为上线早而下载量高好几倍。

### 2. 判编码并统一转 UTF-8

```python
for tag in tags:
    raw = open(f'/tmp/vqsub/sub_{tag}.bin', 'rb').read()
    enc = None
    for e in ['utf-8-sig', 'utf-8', 'gb18030', 'big5']:
        try:
            txt = raw.decode(e); enc = e; break
        except Exception:
            continue
    print(tag, enc, len(txt))
    open(f'/tmp/vqsub/sub_{tag}.utf8.srt', 'w', encoding='utf-8').write(txt)
```

`file` 报 `ISO-8859 text` 基本就是 GB18030（简中 Windows 环境导出）。`Unicode text, UTF-8` 是另一份。顺序上先试 utf-8 再试 gb18030：UTF-8 中文几乎不可能被误判成 GB18030 解读成功，反过来则容易出乱码。

### 3. 比时间轴：按时间点抽样，不要按序号

先说清楚：**条数不同不等于来自不同片源**。同一条官方字幕轨，不同人导出时会合并同屏双行、拆开长句、丢掉片尾歌词，条数就能差十几条。

```python
import re
ts = re.findall(r'(\d{2}:\d{2}:\d{2})[,.]\d{3}\s*-->', txt)
print(len(ts), ts[0], ts[-1])
```

这个只能看个大概范围。**判定是否同一剪：拿 A 的固定时间点去 B 里找起始时间最近的那条，看时间差是不是 0**：

```python
import bisect
def near(t, B, bt):
    i = bisect.bisect_left(bt, t)
    c = [j for j in (i-1, i, i+1, i+2) if 0 <= j < len(B)]
    return min(c, key=lambda j: abs(bt[j] - t))

for t in [120, 300, 600, 900, 1200, 1800, 2400, 3000, 3400]:
    ia = min(range(len(A)), key=lambda i: abs(A[i][0] - t))
    jb = near(A[ia][0], B, bt)
    print(f'{t//60}:{t%60:02d}  A={A[ia][0]}  B={B[jb][0]}  差 {bt[jb]-A[ia][0]:+.1f}s')
```

- **每个抽样点都是 0.0s** = 同一剪，条数差异只是断句策略，可以直接用
- **偏差随时间单调变大**（0s → 30s → 90s）= 不同剪或不同帧率，换版本
- **大小相等但反向偏移** = 片头 logo/黑场长度不同，整份要加固定偏移

> 真实踩过的坑：两份字幕按序号对到第 600 条，算出「差了 97 秒」并差点弃用，实际上按时间点抽样每个点都是 0.0s——纯粹是条数不同导致序号错位。**永远不要用序号对齐两份字幕。**

### 4. 逐条 diff，看用语不看措辞

**只有两份条数一致时**才能用下面的 `zip` 按序号对齐：

```python
def texts(p):
    blocks = re.split(r'\n\s*\n', open(p, encoding='utf-8').read().strip())
    out = []
    for b in blocks:
        ls = [x for x in b.splitlines() if x.strip()]
        if len(ls) >= 3:
            out.append(' '.join(ls[2:]))
    return out

a, b = texts('sub_A.utf8.srt'), texts('sub_B.utf8.srt')
diff = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
print(len(a), len(b), '不同条数:', len(diff))
for i, x, y in diff[:12]:
    print(f'#{i+1}\n  A: {x[:70]}\n  B: {y[:70]}')
```

行数相同（`zip` 不漏）说明结构对得上，diff 出来的就是纯译文差异。

判读对照表：

| 大陆用语 | 台湾用语繁转简 |
|---|---|
| 什么 | 什麽 |
| 计划 | 计画 |
| 源代码 | 原始码 |
| 里 | 裡 |
| 治愈 | 治癒 |
| 设定（语境可见） | 設定（语境可见） |

**选大陆用语那版**。繁转简只换字形不换词，整片会一直是台湾腔；官方译本通常会注明「修正部分翻译为大陆风格 + 中文标点格式化」。

### 5. 落盘、命名、上传

```bash
# 命名对齐正片：正片完整文件名去掉扩展名 + .srt
OUT="$HOME/Downloads/<正片文件名去掉.mkv>.srt"
cp sub_<胜出>.utf8.srt "$OUT"
md5 -q "$OUT"
```

先落 `~/Downloads/`（scratch 24h 会清），再 `upload --parent-fid <[zmk 子目录 fid>` 进网盘，最后 `browse` 回读确认确实在。

## 汇报怎么说

三个数字就够，不用贴全文：

- 候选各自的条数与末时间戳（一致 = 同源，时间轴没问题）
- 不同条数（如「676 条里 151 条不同」）
- 一句话说清差异性质（「另一版是繁转简，还留着 什麽/计画/原始码」）

这样用户一眼知道你为什么选这一版，也不会怀疑你随手抓了一份就交差。
