# 全网盘搜索（PanSou）：这个资源到底在哪个网盘里

影视走 showpaw 那条线。电子书、课程、软件这类拿片名搜不到的东西，走这个。

## 它是什么

PanSou 是开源的网盘资源聚合搜索服务（`fish2018/pansou`，MIT，Go），聚合的是 **Telegram 频道 + 插件站**。它按网盘类型分好类，直接给出夸克 / 百度 / 阿里 / 115 / 磁力 / ed2k 等链接。

默认用公开实例 `https://so.252035.xyz`，不用注册、不用 key。代价：别人的服务器，慢，可能随时挂，你搜过什么它看得见。要长期稳定得自己部署（需要 Docker）。

## 接口

```
POST https://so.252035.xyz/api/search
Content-Type: application/json

{"kw": "<关键词>", "cloud_types": ["quark"], "src": "tg", "res": "merge"}
```

| 参数 | 建议值 | 为什么 |
|---|---|---|
| `kw` | 关键词 | 必填 |
| `cloud_types` | `["quark"]` / `["magnet"]` | 省略会返回全部 13 种网盘，结果很杂 |
| **`src`** | **`tg`** | **必须带。** 默认全来源（含几十个插件站）实测 60 秒超时；只搜 TG 约 65 秒返回 |
| `res` | `merge` | 按网盘类型合并好的结果 |

GET 也行：`?kw=..&src=tg&cloud_types=quark`，中文必须 URL-encode。

## 返回结构

`data.merged_by_type.quark[]`，每条：

| 字段 | 内容 |
|---|---|
| `url` | `https://pan.quark.cn/s/<hash>` |
| `password` | 提取码，多数为空 |
| `note` | 资源标题 |
| `datetime` | 上传时间 |
| `source` | `tg:<频道名>` —— 来源频道，报告时可以带上，让他判断可信度 |

## 三条实测得出的话

1. **超时 ≠ 没有。** 公开实例 60–90 秒是正常耗时，`curl` 一律用 `-m 90`。60 秒没回来先加超时重试，**不要下「搜不到」的结论**——这正是本 skill 铁律里说过的「先怀疑自己的方法」。
2. **必须 `src=tg`。** 不带的话它会把几十个插件站一起并发搜，实测直接拖到超时，看起来像这个站挂了。
3. **结果要人工过一遍再报。** 拿书名去搜，返回里混着「听书解读」「喜马拉雅有声书」，那不是书本身。报之前按 `note` 分一下类：原书 / 解读讲座 / 有声书 / 压缩包。

## 拿到链接之后

跟影视完全一样：验活 → 报给用户 → 用户确认后再转存。验活见 SKILL.md 第 5 步，转存见第三部分。

## 电子书专用源（列着备用，未实测）

- **Anna's Archive**（`annas-archive.gl` 等镜像）：搜书主力
- **LibGen**：同上，另带 `get.php` 直链
- 现成 MCP：`yashimosh/biblio-mcp`（Anna's Archive + LibGen + Z-Library + Sci-Hub 一次搜）、`iosifache/annas-mcp`（★1.1k）

**这几个只查了仓库状态和 README，没有实际跑过一条请求。** 真要用先单独验一条，验通了再写进这里的流程，不要把「看着能用」当成「能用」。
