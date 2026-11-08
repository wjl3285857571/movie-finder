#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mf.py 的离线测试：完全不联网，用注入的 fetch_fn / cli_fn 造返回。

    python3 scripts/test_mf.py
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mf  # noqa: E402


SHARE_URL = "https://pan.quark.cn/s/d71b1d5c8bad"


def token_ok(title="测试片"):
    def fetch(url, payload, timeout=20):
        body = {
            "status": 200,
            "code": 0,
            "message": "ok",
            "data": {"stoken": "STOKEN", "share_type": 1, "title": title},
        }
        return 200, json.dumps(body, ensure_ascii=False)

    return fetch


def token_dead(code=41006, message="分享不存在", http=404):
    def fetch(url, payload, timeout=20):
        body = {"status": http, "code": code, "message": message}
        return http, json.dumps(body, ensure_ascii=False)

    return fetch


def share_info(**over):
    info = {
        "title": "测试片",
        "first_fid": "FIRSTFID",
        "size": 11638567,
        "file_num": 1,
        "partial_violation": False,
        "violation_cnt": 0,
        "all_file_num": 4,
        "file_only_num": 3,
        "status": 1,
        "audit_status": 4,
    }
    info.update(over)
    return info


def cli_with(info=None, files=None):
    """顶层返回 share_info；翻目录返回 files（None 表示 CLI 翻不动）。"""
    def cli(hash_, pdir_fid=None):
        if pdir_fid:
            if files is None:
                return None
            return {"code": 0, "msg": "成功", "data": {"files": files}}
        return {"code": 0, "msg": "成功", "data": {"share_info": info or share_info()}}

    return cli


def as_text(results):
    return mf.format_verify_table(results)


class VerifyLayerOne(unittest.TestCase):
    def test_alive_with_real_size(self):
        r = mf.verify_one(SHARE_URL, fetch_fn=token_ok(), cli_fn=cli_with())
        self.assertEqual(r["status"], "alive")
        self.assertEqual(r["hash"], "d71b1d5c8bad")
        self.assertEqual(r["size"], 11638567)
        self.assertEqual(r["size_human"], "11.1 MB")
        self.assertEqual(r["title"], "测试片")

    def test_dead_41006_keeps_code(self):
        r = mf.verify_one("zzzzzzzzzzzz", fetch_fn=token_dead(), cli_fn=cli_with())
        self.assertEqual(r["status"], "dead")
        self.assertEqual(r["code"], 41006)
        self.assertIn("41006", as_text([r]))

    def test_network_error_is_unknown(self):
        def boom(url, payload, timeout=20):
            raise OSError("connection reset")

        r = mf.verify_one(SHARE_URL, fetch_fn=boom, cli_fn=cli_with())
        self.assertEqual(r["status"], "unknown")
        self.assertIn("connection reset", r["note"])

    def test_unrecognised_body_is_unknown(self):
        for fetch in (
            lambda url, payload, timeout=20: (200, "<html>not json</html>"),
            lambda url, payload, timeout=20: (200, json.dumps({"hello": "world"})),
            lambda url, payload, timeout=20: (200, json.dumps({"code": 0, "data": {}})),
            lambda url, payload, timeout=20: (429, json.dumps({"code": 13002, "message": "too many"})),
        ):
            r = mf.verify_one(SHARE_URL, fetch_fn=fetch, cli_fn=cli_with())
            self.assertEqual(r["status"], "unknown", r)
            self.assertNotEqual(r["status"], "alive")


class VerifyLayerTwo(unittest.TestCase):
    def test_partial_violation_is_half_dead(self):
        info = share_info(partial_violation=True, violation_cnt=2)
        r = mf.verify_one(SHARE_URL, fetch_fn=token_ok(), cli_fn=cli_with(info=info, files=None))
        self.assertEqual(r["status"], "half_dead")
        self.assertIn("违规", r["note"])

    def test_only_subtitles_left_is_half_dead(self):
        info = share_info(partial_violation=True, violation_cnt=2)
        files = [
            {"filename": "Movie.2020.2160p.ass"},
            {"filename": "Movie.2020.2160p.srt"},
            {"filename": "poster.jpg"},
        ]
        r = mf.verify_one(SHARE_URL, fetch_fn=token_ok(), cli_fn=cli_with(info=info, files=files))
        self.assertEqual(r["status"], "half_dead")
        self.assertIn("仅剩字幕", r["note"])

    def test_video_still_present_is_alive(self):
        info = share_info(partial_violation=True, violation_cnt=1)
        files = [{"filename": "Movie.2020.2160p.mkv"}, {"filename": "Movie.ass"}]
        r = mf.verify_one(SHARE_URL, fetch_fn=token_ok(), cli_fn=cli_with(info=info, files=files))
        self.assertEqual(r["status"], "alive")
        self.assertIn("视频", r["note"])

    def test_counts_differ_alone_is_not_half_dead(self):
        """防回归：all_file_num=4 / file_only_num=3 但 violation_cnt=0，实测正常。"""
        info = share_info(all_file_num=4, file_only_num=3, violation_cnt=0, partial_violation=False)
        r = mf.verify_one(SHARE_URL, fetch_fn=token_ok(), cli_fn=cli_with(info=info))
        self.assertEqual(r["status"], "alive")
        self.assertNotEqual(r["status"], "half_dead")
        self.assertIn("数字不等", r["note"])

    def test_missing_fields_is_unknown(self):
        for info in (
            {k: v for k, v in share_info().items() if k != "size"},
            {k: v for k, v in share_info().items() if k != "partial_violation"},
        ):
            r = mf.verify_one(SHARE_URL, fetch_fn=token_ok(), cli_fn=cli_with(info=info))
            self.assertEqual(r["status"], "unknown", r)
            self.assertIn("缺少字段", r["note"])

    def test_cli_unavailable_is_unknown(self):
        r = mf.verify_one(SHARE_URL, fetch_fn=token_ok(), cli_fn=lambda h, pdir_fid=None: None)
        self.assertEqual(r["status"], "unknown")
        self.assertNotEqual(r["status"], "alive")
        self.assertIn("未判 alive", r["note"])


class Rank(unittest.TestCase):
    FIXTURE = [
        {"title": "Dune.2021.1080p.WEBRip.x264", "size": "3.2G"},
        {"title": "Dune.2021.2160p.UHD.BluRay.REMUX.HDR.HEVC.DTS-HD.MA", "size": "58.02G"},
        {"title": "Dune.2021.2160p.WEB-DL.DDP5.1.Atmos.DV.HDR.HEVC", "size": "17.5G"},
        {"title": "Dune.2021.HDTV.x264", "size": "1.4G"},
        {"title": "Dune.2021.2160p.UHD.BluRay.BDMV", "size": "90G"},
    ]

    def test_exact_order_and_unplayable(self):
        ranked, unplayable = mf.rank_items(self.FIXTURE)
        self.assertEqual(
            [e["tier"] for e in ranked],
            ["Remux", "WEB-DL", "WEBRip", "HDTV"],
        )
        self.assertEqual([e["rank"] for e in ranked], [1, 2, 3, 4])
        self.assertTrue(ranked[0]["title"].endswith("DTS-HD.MA"))
        self.assertEqual(len(unplayable), 1)
        self.assertIn("BDMV", unplayable[0]["title"])
        # 不可直看的条目不进主排序
        self.assertFalse(any("BDMV" in e["title"] for e in ranked))

    def test_dolby_vision_beats_atmos_only(self):
        items = [
            {"title": "X.2160p.WEB-DL.DDP5.1.Atmos.HEVC", "size": "12G"},
            {"title": "X.2160p.WEB-DL.DDP5.1.Atmos.DV.HDR.HEVC", "size": "12G"},
        ]
        ranked, _ = mf.rank_items(items)
        self.assertTrue(ranked[0]["dv"])
        self.assertIn("DV", ranked[0]["title"])

    def test_atmos_beats_plain_webdl(self):
        items = [
            {"title": "X.2160p.WEB-DL.H264", "size": "12G"},
            {"title": "X.2160p.WEB-DL.DDP5.1.Atmos.HEVC", "size": "12G"},
        ]
        ranked, _ = mf.rank_items(items)
        self.assertTrue(ranked[0]["atmos"])
        self.assertFalse(ranked[1]["atmos"])
        self.assertIn("Atmos", ranked[0]["title"])

    def test_unknown_quality_is_other_and_flagged(self):
        ranked, unplayable = mf.rank_items([{"title": "某某电影 高清版 国语中字", "size": "2G"}])
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["tier"], "其他")
        self.assertFalse(ranked[0]["quality_guess"])
        self.assertEqual(unplayable, [])

    def test_webdl_spellings(self):
        for title, tier in (
            ("A.2020.WEBDL.1080p", "WEB-DL"),
            ("A.2020.WEB.DL.1080p", "WEB-DL"),
            ("A.2020.WEB-RIP.1080p", "WEBRip"),
            ("A.2020.BluRay.1080p", "BluRay"),
            ("A.2020.remux.1080p", "Remux"),
        ):
            got, guess = mf.parse_tier(title)
            self.assertEqual(got, tier, title)
            self.assertTrue(guess)


class Helpers(unittest.TestCase):
    def test_parse_hash_accepts_url_hash_and_pwd(self):
        self.assertEqual(mf.parse_hash("https://pan.quark.cn/s/abc123"), "abc123")
        self.assertEqual(mf.parse_hash("abc123"), "abc123")
        self.assertEqual(mf.parse_hash("https://pan.quark.cn/s/abc123?pwd=xyz"), "abc123")
        self.assertEqual(mf.parse_passcode("https://pan.quark.cn/s/abc123?pwd=xyz"), "xyz")
        self.assertIsNone(mf.parse_hash(""))

    def test_parse_size(self):
        self.assertEqual(mf.parse_size(11638567), 11638567)
        self.assertEqual(mf.parse_size("58.02G"), int(58.02 * 1024 ** 3))
        self.assertIsNone(mf.parse_size(None))


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    if result.wasSuccessful():
        print("%d passed" % result.testsRun)
    else:
        print("%d passed, %d failed" % (passed, len(result.failures) + len(result.errors)))
    sys.exit(0 if result.wasSuccessful() else 1)
