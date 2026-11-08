# 夸克分享验活（详细版）

> 本文件由 `SKILL.md` v1.0.0 原样拆出（2026-11-09），文字未改，只做归位。

## 第 5 步：逐条验活 ⭐ 必做

```python
for h in hashes:
    goto_url(f"https://pan.quark.cn/s/{h}")
    wait_for_load(); time.sleep(4)
    body = js("document.body.innerText")
```

**批量筛先用官方接口过一遍，别一上来开浏览器**（每条 `time.sleep(4)`，八条就是半分钟）：

```bash
curl -s -m 20 -X POST 'https://drive-h.quark.cn/1/clouddrive/share/sharepage/token?pr=ucpro&fr=pc' \
  -H 'Content-Type: application/json' -d '{"pwd_id":"<hash>","passcode":"<提取码或空>"}'
```

返回 `{"status":200,"code":0,"data":{"stoken":"...","share_type":1,...}}` = 存活。

**注意口径**：这条只实测过「活链返回 200 + stoken」，**死链返回什么没验过**，所以它只能当**廉价的预筛**——200 的再走下面的浏览器/`share-detail` 确认，非 200 的不要据此直接判定失效（真正确认请用 `share-detail`，见第三部分 3.3）。

| bodyText 含 | 判定 |
|---|---|
| 「共 N 个文件」「永久有效」+ 文件名 | ✅ 活链 |
| 「该分享已失效」/「分享已被取消」/「文件已被删除」 | ❌ 死链，剔除 |
| 只有登录墙 | ⚠️ **不算失效**（调用方已登录会自动转存） |

**showpaw 标的「已验证有效」不可信**——那只是它上次抓取的快照。**必须自己打开验。**

### 版权清理留下的「半死链」：链接活着，视频没了 ⭐

`share-detail` 返回 `code:0`、标题完整、第三方站还写着 82GB，**不代表内容还在**。夸克会把侵权文件从分享里摘掉、只留字幕和海报，链接本身依然合法可访问——这是最容易被当成好资源报给用户的形态。

判据全在 `share_info` 里，三个字段一起看：

| 字段 | 含义 |
|---|---|
| `partial_violation: true` + `violation_cnt ≥ 1` | 这份分享有内容被清理过 |
| `all_file_num`（含违规项）/ `file_only_num`（实际可见） | 两个数差得多 = 少的那部分被摘了 |
| `size` | **真实剩余体积**；和第三方站标注的体积对不上就是被清过（实测 82GB 的条目真实只剩 393KB） |

命中任一迹象，再翻一层文件列表确认：只剩 `.ass` / `.srt` / `.jpg` 而没有 mkv，就是视频已经被摘走，**不能存、不能报**。

**三种「不能存」要分开报，别都说成「链接失效」**：

| 现象 | 真实含义 |
|---|---|
| `{"code":41031,"msg":"该链接分享者已被封禁"}` | 这人的所有分享都死了，换他其它链接也没用 |
| `该分享已失效` / `分享已被取消` | 只是这一条没了 |
| `partial_violation` 版权清理 | **链接还在、标题还在、平台标「有效」，但正片没了**——最需要主动查出来的一种 |

**文件夹型分享要点进去看**：bodyText 只给一个文件夹名（可能乱码化，如 `xxx灭xxx`），要点开才看到真实文件名（`Annihilation.2018.2160p.ass`）。文件名的分辨率/编码/音轨标签是判断档位的唯一依据。

**数量策略**：≤6 条全验；>8 条只验前 3（top picks）+ 后 1（兜底），中间注明「未验活」。

## mf.py verify 接口与判定顺序（脚本版）

```bash
python3 scripts/mf.py verify <链接或hash> [更多…] [--json]
```

- **第一层**：`POST https://drive-h.quark.cn/1/clouddrive/share/sharepage/token?pr=ucpro&fr=pc`，body `{"pwd_id": "<hash>", "passcode": "<可空>"}`。HTTP 200 + `code:0` + `data.stoken` → 进第二层；`code:41006`（分享不存在）/ `41031`（分享者已被封禁）→ `dead`；其它返回（限流、改版、要验证码）→ `unknown`，不猜。
- **第二层**：`node ~/.hermes/skills/quarkclouddrive/scripts/quark-drive.cjs share-detail --url ...`，读 `data.share_info`。必需字段 `size` / `partial_violation` / `violation_cnt`，缺任一 → `unknown`。
- **判定顺序**：
  1. `partial_violation == true` 或 `violation_cnt >= 1` → 翻文件列表（`--pdir-fid <first_fid> --size 50`）：只剩 `.ass/.srt/.jpg/.png` → `half_dead`；仍有 `.mkv/.mp4` → `alive`；翻不动 → `half_dead`（有违规记录）。
  2. 无违规记录 → `alive`。`all_file_num != file_only_num` 只写进 note，**不降级**（实测反例 4 vs 3）。
  3. CLI 不可用（node / 脚本缺失、无登录态）→ `unknown`，note 写明原因，**不判 alive**。
- `--json` 稳定字段：`results[].{target,hash,status,title,size,size_human,file_num,all_file_num,file_only_num,partial_violation,violation_cnt,code,message,note}`，外加 `counts`。

