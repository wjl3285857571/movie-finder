# 抓字幕全流程（详细版）

> 本文件由 `SKILL.md` v1.0.0 原样拆出（2026-11-09），文字未改，只做归位。

# 第二部分：抓字幕

目标：从 `zimuku.org` 抓到 `~/Downloads/`（scratch 24h 自动清，不要放那）。

备用域名：`srtku.com` / `zmk.pw`（同一站）。

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
p = os.path.expanduser("~/.hermes/cache/scratch/cap.png")
im.save(p)
```

**规则**：
- 必须放大到 400×108（原图 100×27，斜纹干扰读不准）
- **自己识别直接填，不发用户核对**
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

守护进程超时先 `ensure_real_tab()` 再 `goto_url`——这一步能把 `Page.navigate timed out ... waiting for the daemon` 当场救回来，同一个会话接着跑。**连续两次都超时才重开会话**：一超时就换会话，验证码 cookie 会跟着丢，白过一遍。

## 2.4 选字幕

| 优先级 | 维度 |
|---|---|
| 1 | **双语** > 纯中文 |
| 2 | **特效字幕**（压制组带样式）> 官方简体 |
| 3 | **release 名与资源完全匹配**（时间轴才准） |

**匹配检查**：字幕文件名和影视资源文件名并排比，分辨率/来源/编码/组名一致才稳。

**周更剧的特效字幕按两集一包发**：LEN-X 那套中英特效的节奏是 E1-2 / E3-4 / E5-6 一包一包出，**所以「E07 没有 E01-E06 那种 .sup」通常不是缺，而是 E7-8 那包还没发**——单集播出后要等下一集一起打包。要确认全场有哪些字幕、是不是成对发布，看剧集主页 `https://zimuku.org/subs/<id>.html`（全量列表，见 `references/subtitle-sources.md`）。拿不到同档时去备用源找双语版顶替，并在汇报里说清「这是临时版本，等 E7-8 包出来再换同档特效」。

**用户说「这份字幕翻译有问题」时**：不要重下同一份。特效组为了视觉常润色台词；官方字幕逐字准确但没特效。**两类互补不替代**——换另一版本，或列全让用户挑。

**同集有多个「简体中文」候选、拿不准选哪个时**：两份都下，按 `references/subtitle-quality-picker.md` 做逐条比对（条数+时间戳判同源，diff 判用语），再决定。

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
bsdtar -xf /tmp/sub.rar -C ~/Downloads/
md5 -q ~/Downloads/<每个文件>
```

**macOS 没有 unrar / unar / 7z 时用 `bsdtar`**（自带 libarchive，支持 RAR5）。

## 2.8 报告

文件名、大小、MD5、语言、格式、制作/校订组、上传时间、详情页链接，以及**是否与资源 release 匹配**。
