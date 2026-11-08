#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""movie-finder 的机械活：夸克分享验活 + 候选资源排序。

只用标准库（urllib / json / argparse / re / subprocess）。

    python3 scripts/mf.py verify <链接或hash> [更多…] [--json]
    python3 scripts/mf.py rank [候选.json] [--json]      # 不给文件就读 stdin

验活判定：alive / dead / half_dead / unknown。
硬红线：拿不到 share_info 关键字段时只输出 unknown 并写原因，绝不猜成 alive / dead。
"""

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

TOKEN_URL = "https://drive-h.quark.cn/1/clouddrive/share/sharepage/token?pr=ucpro&fr=pc"
QUARK_CLI = os.environ.get(
    "MF_QUARK_CLI",
    os.path.expanduser("~/.hermes/skills/quarkclouddrive/scripts/quark-drive.cjs"),
)
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# 41006 分享不存在；41031 分享者已被封禁（这个人的所有分享都死了）
DEAD_CODES = {41006: "分享不存在", 41031: "分享者已被封禁"}

VIDEO_EXT = (".mkv", ".mp4", ".avi", ".ts", ".m2ts", ".mov", ".wmv", ".flv", ".rmvb")
SIDE_EXT = (".ass", ".srt", ".ssa", ".vtt", ".sup", ".jpg", ".jpeg", ".png", ".webp", ".nfo", ".txt")


# ---------------------------------------------------------------- 通用小工具

def parse_hash(target):
    """从链接或裸 hash 里取 pwd_id；取不到返回 None。"""
    t = (target or "").strip()
    if not t:
        return None
    m = re.search(r"/s/([0-9A-Za-z]+)", t)
    if m:
        return m.group(1)
    if re.fullmatch(r"[0-9A-Za-z]{4,}", t):
        return t
    return None


def parse_passcode(target):
    """链接带 ?pwd=xxxx 时取提取码，没有就返回空串。"""
    m = re.search(r"[?&]pwd=([0-9A-Za-z]+)", target or "")
    return m.group(1) if m else ""


def human_size(n):
    if n is None:
        return "-"
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "-"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return ("%d %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1024.0
    return "-"


def display_width(s):
    import unicodedata

    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, width):
    s = str(s)
    return s + " " * max(0, width - display_width(s))


def cut(s, width):
    s = str(s)
    if display_width(s) <= width:
        return s
    out = ""
    for c in s:
        if display_width(out + c) > width - 1:
            break
        out += c
    return out + "…"


# ---------------------------------------------------------------- 第一层：token

def _http_post_json(url, payload, timeout=20):
    """返回 (http_status, body_text)。网络异常向上抛，由调用方转 unknown。"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": UA},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


# ---------------------------------------------------------------- 第二层：官方 CLI

def _run_cli(args, timeout=60):
    """跑 quark-drive.cjs，返回 (payload, error)。"""
    node = shutil.which("node")
    if not node:
        return None, "node 未安装"
    if not os.path.isfile(QUARK_CLI):
        return None, "找不到 quark-drive.cjs: %s" % QUARK_CLI
    session_id = "%d-%06d" % (int(time.time()), random.randint(0, 999999))
    cmd = [node, QUARK_CLI] + list(args) + [
        "--session-input", "验活",
        "--session-id", session_id,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "CLI 超时（%ss）" % timeout
    except OSError as exc:
        return None, "CLI 启动失败: %s" % exc
    raw = (proc.stdout or "").strip()
    if not raw:
        return None, "CLI 无输出: %s" % ((proc.stderr or "").strip()[:200] or "empty")
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return None, "CLI 输出不是 JSON: %s" % raw[:200]
    try:
        return json.loads(raw[start:end + 1]), None
    except ValueError as exc:
        return None, "CLI 输出 JSON 解析失败: %s" % exc


def _cli_share_detail(hash_, pdir_fid=None):
    """官方 CLI 读分享信息；pdir_fid 给了就翻该目录。返回 (payload, error)。"""
    args = ["share-detail", "--url", "https://pan.quark.cn/s/%s" % hash_]
    if pdir_fid:
        args += ["--pdir-fid", str(pdir_fid), "--size", "50"]
    return _run_cli(args)


def _invoke_cli(cli_fn, hash_, pdir_fid=None):
    """调注入的 cli_fn，统一成 (payload, error) 二元组。

    允许 cli_fn 直接返回 payload（此时 error 一律记成「CLI 不可用」）。
    """
    out = cli_fn(hash_, pdir_fid)
    if isinstance(out, tuple) and len(out) == 2:
        return out
    return out, (None if out is not None else "CLI 不可用")



# ---------------------------------------------------------------- 验活

def _entry_name(entry):
    return entry.get("filename") or entry.get("file_name") or ""


def _entry_is_dir(entry):
    if entry.get("dir") is True:
        return True
    return str(entry.get("file_type", "")) == "0"


def _ext(name):
    name = name.lower()
    for ext in VIDEO_EXT + SIDE_EXT:
        if name.endswith(ext):
            return ext
    return os.path.splitext(name)[1].lower()


def _list_share_files(hash_, first_fid, cli_fn, depth=1):
    """翻分享目录，返回 (files, error)；files 里每项是 dict。"""
    payload, err = _invoke_cli(cli_fn, hash_, first_fid)
    if payload is None:
        return None, err or "CLI 不可用"
    if payload.get("code") not in (0, None):
        return None, "share-detail code=%s %s" % (payload.get("code"), payload.get("msg") or "")
    data = payload.get("data") or {}
    files = data.get("files")
    if files is None:
        files = data.get("list")
    if not isinstance(files, list):
        return None, "share-detail 没有返回文件列表"
    out = list(files)
    if depth > 0:
        dirs = [f for f in files if _entry_is_dir(f)][:5]
        for d in dirs:
            sub, _ = _list_share_files(hash_, d.get("fid"), cli_fn, depth - 1)
            if sub:
                out.extend(sub)
    return out, None


def verify_one(target, fetch_fn=None, cli_fn=None):
    """验一条分享，返回结构化 dict。"""
    fetch_fn = fetch_fn or _http_post_json
    cli_fn = cli_fn or _cli_share_detail

    result = {
        "target": target,
        "hash": None,
        "status": "unknown",
        "title": None,
        "size": None,
        "size_human": "-",
        "file_num": None,
        "all_file_num": None,
        "file_only_num": None,
        "partial_violation": None,
        "violation_cnt": None,
        "code": None,
        "message": None,
        "note": "",
    }

    hash_ = parse_hash(target)
    if not hash_:
        result["note"] = "无法从输入里解析出夸克 hash"
        return result
    result["hash"] = hash_

    # ---- 第一层：token（免登录） ----
    try:
        http_status, body_text = fetch_fn(
            TOKEN_URL, {"pwd_id": hash_, "passcode": parse_passcode(target)}
        )
    except Exception as exc:  # 网络异常一律 unknown
        result["note"] = "token 接口请求失败：%s" % exc
        return result

    try:
        body = json.loads(body_text)
    except (TypeError, ValueError):
        result["note"] = "token 接口返回不是 JSON（HTTP %s）" % http_status
        return result
    if not isinstance(body, dict):
        result["note"] = "token 接口返回结构不认识（HTTP %s）" % http_status
        return result

    code = body.get("code")
    data = body.get("data")
    has_stoken = isinstance(data, dict) and bool(data.get("stoken"))

    if code in DEAD_CODES:
        result.update(status="dead", code=code, message=body.get("message"))
        result["note"] = "token 层 code=%s %s" % (code, DEAD_CODES[code])
        return result
    if not (http_status == 200 and code == 0 and has_stoken):
        # 不认识的返回：可能限流、接口改版、要验证码 —— 都不许猜
        result.update(code=code, message=body.get("message"))
        result["note"] = "token 层返回不认识的结果（HTTP %s, code %s, message %s）" % (
            http_status, code, body.get("message"),
        )
        return result

    # token 层活着
    result["title"] = data.get("title")
    result["code"] = code
    result["message"] = body.get("message")

    # ---- 第二层：官方 CLI 读 share_info ----
    payload, err = _invoke_cli(cli_fn, hash_)
    if payload is None:
        result["note"] = "token 层 code=0 但无法确认内容：%s（未判 alive）" % (err or "CLI 不可用")
        return result

    if payload.get("code") not in (0, None):
        pcode = payload.get("code")
        if pcode in DEAD_CODES:
            result.update(status="dead", code=pcode, message=payload.get("msg"))
            result["note"] = "share-detail code=%s %s" % (pcode, DEAD_CODES[pcode])
            return result
        result["note"] = "share-detail 返回 code=%s %s" % (pcode, payload.get("msg") or "")
        return result

    info = (payload.get("data") or {}).get("share_info")
    if not isinstance(info, dict):
        result["note"] = "share-detail 里没有 data.share_info"
        return result

    missing = [k for k in ("size", "partial_violation", "violation_cnt") if k not in info]
    if missing:
        result["note"] = "share_info 缺少字段：%s" % ", ".join(missing)
        return result

    result.update(
        title=info.get("title") or result["title"],
        size=info.get("size"),
        size_human=human_size(info.get("size")),
        file_num=info.get("file_num"),
        all_file_num=info.get("all_file_num"),
        file_only_num=info.get("file_only_num"),
        partial_violation=bool(info.get("partial_violation")),
        violation_cnt=info.get("violation_cnt"),
    )

    violation = bool(info.get("partial_violation")) or int(info.get("violation_cnt") or 0) >= 1
    all_num, only_num = info.get("all_file_num"), info.get("file_only_num")
    counts_differ = (
        isinstance(all_num, int) and isinstance(only_num, int) and all_num != only_num
    )

    if not violation:
        result["status"] = "alive"
        if counts_differ:
            # 实测反例：4 vs 3 但分享完全正常。数字不等只提示复查，绝不据此判半死。
            result["note"] = "文件数 %s→%s，无违规记录（数字不等 ≠ 被清理）" % (
                all_num, only_num,
            )
        else:
            result["note"] = "无违规记录"
        return result

    # 有违规记录：必须翻文件列表核实才能叫 half_dead
    files, list_err = _list_share_files(hash_, info.get("first_fid"), cli_fn)
    if files is None:
        result["status"] = "half_dead"
        result["note"] = "有违规记录（violation_cnt=%s），翻目录失败：%s" % (
            info.get("violation_cnt"), list_err,
        )
        return result

    names = [_entry_name(f) for f in files if not _entry_is_dir(f)]
    videos = [n for n in names if _ext(n) in VIDEO_EXT]
    side = [n for n in names if _ext(n) in SIDE_EXT]

    if videos:
        result["status"] = "alive"
        result["note"] = "有违规记录，但目录里仍有 %d 个视频文件" % len(videos)
    elif side:
        result["status"] = "half_dead"
        result["note"] = "仅剩字幕/图片（%d 个），没有任何视频文件" % len(side)
    else:
        result["status"] = "unknown"
        result["note"] = "有违规记录，但目录为空/只有子目录，无法确认"

    return result


def verify_many(targets, fetch_fn=None, cli_fn=None):
    return [verify_one(t, fetch_fn=fetch_fn, cli_fn=cli_fn) for t in targets]


def format_verify_table(results):
    head = "%-14s %-10s %-9s %-26s %s" % ("HASH", "STATUS", "SIZE", "TITLE", "NOTE")
    lines = [head]
    for r in results:
        note = r.get("note") or ""
        if r.get("code") not in (None, 0) and str(r["code"]) not in note:
            note = ("code %s %s" % (r["code"], note)).strip()
        lines.append(
            "%s %s %s %s %s"
            % (
                pad(r.get("hash") or "-", 14),
                pad(r.get("status") or "-", 10),
                pad(r.get("size_human") or "-", 9),
                pad(cut(r.get("title") or "-", 26), 26),
                note,
            )
        )
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    lines.append("")
    lines.append(
        "共 %d 条：%s"
        % (
            len(results),
            "，".join("%s %d" % (k, counts[k]) for k in ("alive", "dead", "half_dead", "unknown") if k in counts)
            or "无",
        )
    )
    return "\n".join(lines)


# ---------------------------------------------------------------- 排序

TAG_RULES = {
    "dv": re.compile(r"(?<![A-Za-z])(DV|DoVi)(?![A-Za-z])|dolby[.\s\-_]?vision", re.I),
    "atmos": re.compile(r"(?<![A-Za-z])atmos(?![A-Za-z])", re.I),
    "hdr": re.compile(r"(?<![A-Za-z])HDR10\+?|(?<![A-Za-z])HDR(?![A-Za-z])", re.I),
}

TIER_RULES = [
    ("Remux", re.compile(r"(?<![A-Za-z])remux(?![A-Za-z])", re.I)),
    ("BluRay", re.compile(r"blu-?ray", re.I)),
    ("WEB-DL", re.compile(r"(?<![A-Za-z])web[.\s\-_]?dl(?![A-Za-z])", re.I)),
    ("WEBRip", re.compile(r"(?<![A-Za-z])web[.\s\-_]?rip(?![A-Za-z])", re.I)),
    ("HDTV", re.compile(r"(?<![A-Za-z])hdtv(?![A-Za-z])|录制|电视录制", re.I)),
]

# BluRay 不在默认五档里，按「碟源优于流媒体」放在 Remux 之后、WEB-DL 之前
TIER_ORDER = {"Remux": 0, "BluRay": 1, "WEB-DL": 2, "WEBRip": 3, "HDTV": 4, "其他": 5}

UNPLAYABLE_RE = re.compile(
    r"(?<![A-Za-z])ISO(?![A-Za-z])|(?<![A-Za-z])BDMV(?![A-Za-z])|蓝光原盘", re.I
)


def parse_tier(title):
    """从标题解析档位，返回 (tier, quality_guess)。解析不出就是「其他」+ False。"""
    for tier, pattern in TIER_RULES:
        if pattern.search(title):
            return tier, True
    return "其他", False


def parse_size(value):
    """把 12345 / '58.02G' / '2.79 GB' 统一成字节数（解析不了就 None）。"""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([KMGTP]?)(?:i?B)?", str(value), re.I)
    if not m:
        return None
    num = float(m.group(1))
    unit = m.group(2).upper()
    factor = {"": 1, "K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4, "P": 1024 ** 5}
    return int(num * factor.get(unit, 1))


def rank_items(items):
    """返回 (ranked, unplayable)。items 里每项至少要有 title。"""
    ranked, unplayable = [], []
    for raw in items:
        if isinstance(raw, str):
            raw = {"title": raw}
        if not isinstance(raw, dict):
            raise ValueError("候选条目必须是对象或字符串：%r" % (raw,))
        title = (raw.get("title") or "").strip()
        if not title:
            raise ValueError("候选条目缺 title：%r" % (raw,))

        size_bytes = parse_size(raw.get("size"))
        entry = {
            "title": title,
            "tier": None,
            "quality_guess": False,
            "dv": bool(TAG_RULES["dv"].search(title)),
            "atmos": bool(TAG_RULES["atmos"].search(title)),
            "hdr": bool(TAG_RULES["hdr"].search(title)),
            "size": size_bytes,
            "size_human": human_size(size_bytes),
            "rank": None,
        }

        if UNPLAYABLE_RE.search(title):
            entry["tier"] = "ISO/BDMV"
            entry["quality_guess"] = True
            unplayable.append(entry)
            continue

        entry["tier"], entry["quality_guess"] = parse_tier(title)
        ranked.append(entry)

    def sort_key(e):
        return (
            TIER_ORDER.get(e["tier"], 9),
            0 if e["dv"] else 1,
            0 if e["atmos"] else 1,
            -1 if e["hdr"] else 0,
            -(e["size"] or 0),
        )

    ranked.sort(key=sort_key)
    for i, e in enumerate(ranked, 1):
        e["rank"] = i
    return ranked, unplayable


def format_rank_table(ranked, unplayable):
    lines = [
        "%s %s %s %s %s" % (pad("#", 4), pad("TIER", 8), pad("SIZE", 10), pad("TAGS", 12), "TITLE"),
    ]
    for e in ranked:
        tags = "/".join(
            t for t in (
                "DV" if e["dv"] else "",
                "Atmos" if e["atmos"] else "",
                "HDR" if e["hdr"] else "",
            ) if t
        ) or "-"
        tier_label = e["tier"] + ("" if e["quality_guess"] else "?")
        lines.append(
            "%s %s %s %s %s"
            % (
                pad(e["rank"], 4),
                pad(tier_label, 8),
                pad(e["size_human"], 10),
                pad(tags, 12),
                e["title"],
            )
        )
    if unplayable:
        lines.append("")
        lines.append("不可直看（ISO / BDMV / 蓝光原盘，夸克解析不了）：")
        for e in unplayable:
            lines.append("  - %s" % e["title"])
    lines.append("")
    lines.append("可排 %d 条，不可直看 %d 条" % (len(ranked), len(unplayable)))
    return "\n".join(lines)


def load_items(path):
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        text = sys.stdin.read()
        if not text.strip():
            raise ValueError("stdin 没有内容，也没有给 JSON 文件")
        data = json.loads(text)
    if isinstance(data, dict):
        for key in ("items", "candidates", "results", "data"):
            if isinstance(data.get(key), list):
                return data[key]
        raise ValueError("JSON 对象里找不到 items / candidates / results / data 列表")
    if isinstance(data, list):
        return data
    raise ValueError("候选清单必须是 JSON 数组或含数组的对象")


# ---------------------------------------------------------------- CLI

def cmd_verify(args):
    results = verify_many(args.targets)
    if args.json:
        counts = {}
        for r in results:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        payload = {"results": results, "counts": counts}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_verify_table(results))
    return 0


def cmd_rank(args):
    try:
        items = load_items(args.file)
    except (OSError, ValueError) as exc:
        print("读取候选清单失败：%s" % exc, file=sys.stderr)
        return 2
    try:
        ranked, unplayable = rank_items(items)
    except ValueError as exc:
        print("候选清单不合法：%s" % exc, file=sys.stderr)
        return 2
    if args.json:
        payload = {
            "items": ranked,
            "unplayable": unplayable,
            "counts": {"total": len(items), "ranked": len(ranked), "unplayable": len(unplayable)},
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_rank_table(ranked, unplayable))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="mf.py", description="movie-finder：夸克验活 + 候选资源排序"
    )
    sub = parser.add_subparsers(dest="command")

    p_verify = sub.add_parser("verify", help="验夸克分享是活/死/半死")
    p_verify.add_argument("targets", nargs="+", help="分享链接或 hash，可以传多个")
    p_verify.add_argument("--json", action="store_true", help="输出结构化 JSON")
    p_verify.set_defaults(func=cmd_verify)

    p_rank = sub.add_parser("rank", help="按画质给候选资源排序")
    p_rank.add_argument("file", nargs="?", help="候选清单 JSON；不给就读 stdin")
    p_rank.add_argument("--json", action="store_true", help="输出结构化 JSON")
    p_rank.set_defaults(func=cmd_rank)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
