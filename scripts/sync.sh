#!/usr/bin/env bash
# 把公开版的通用文件同步到本机 Hermes 的个人 skill，保留 references/personal.md。
#
#   bash scripts/sync.sh --dry-run   # 只看会覆盖哪些文件，不写
#   bash scripts/sync.sh             # 真同步 + 逐文件 md5 校验 + 跑单测
#
# 可用环境变量覆盖路径：
#   SRC=~/Projects/movie-finder DST=~/.hermes/skills/media/movie-finder bash scripts/sync.sh
#
# SKILL.md 复制后会自动套一层「个人覆盖层」：把「用户偏好（默认值）」那节换成
# 指向 references/personal.md 的指针，避免个人偏好被通用默认值冲掉。
set -euo pipefail

SRC="${SRC:-$HOME/Projects/movie-finder}"
DST="${DST:-$HOME/.hermes/skills/media/movie-finder}"
DRY_RUN=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "未知参数：${arg}（只支持 --dry-run / --help）" >&2
      exit 2
      ;;
  esac
done

die() { echo "错误：$*" >&2; exit 1; }

[ -d "$SRC" ] || die "SRC 不存在：$SRC"
[ -d "$DST" ] || die "DST 不存在：$DST"
[ -f "$SRC/SKILL.md" ] || die "SRC 里没有 SKILL.md：$SRC"
[ -f "$DST/references/personal.md" ] || die "$DST/references/personal.md 不存在——这不是个人 skill 目录（个人偏好文件必须已存在，本脚本不负责创建它）"

# 通用文件清单（相对路径）。personal.md 永远不在清单里。
FILES=("SKILL.md")
for f in "$SRC"/references/*.md; do
  [ -e "$f" ] || continue
  name="$(basename "$f")"
  [ "$name" = "personal.md" ] && continue
  FILES+=("references/$name")
done
FILES+=("scripts/mf.py" "scripts/test_mf.py")

for rel in "${FILES[@]}"; do
  [ -f "$SRC/$rel" ] || die "源文件缺失：$SRC/$rel"
done

# macOS 是 md5 -q，Linux 是 md5sum
if command -v md5 >/dev/null 2>&1; then
  md5of() { md5 -q "$1"; }
elif command -v md5sum >/dev/null 2>&1; then
  md5of() { md5sum "$1" | awk '{print $1}'; }
else
  die "找不到 md5 / md5sum，无法做校验"
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# 生成「公开版 SKILL.md + 个人覆盖层」的预期内容
python3 - "$SRC/SKILL.md" "$WORK/SKILL.md" <<'PY' || die "生成个人覆盖层失败"
import io
import sys

src, dst = sys.argv[1], sys.argv[2]
HEAD = "## 用户偏好（默认值，可按「配置」一节改）"
END = "\n# 第一部分：找片"
POINTER = (
    "## 用户偏好\n\n"
    "**以 `references/personal.md` 为准**（那是亮子的定稿，与本文件任何默认值冲突时，personal.md 赢）。"
    "动任何交付动作前先读它。\n"
)
text = io.open(src, encoding="utf-8").read()
if HEAD not in text or END not in text:
    sys.exit("SKILL.md 里找不到「用户偏好（默认值）」小节标记，无法套用个人覆盖层")
a = text.index(HEAD)
b = text.index(END, a)
io.open(dst, "w", encoding="utf-8").write(text[:a] + POINTER + text[b:])
PY

PERSONAL_BEFORE="$(md5of "$DST/references/personal.md")"

echo "SRC: $SRC"
echo "DST: $DST"
echo
echo "将覆盖以下 ${#FILES[@]} 个文件（references/personal.md 不在其中）："
for rel in "${FILES[@]}"; do
  if [ -f "$DST/$rel" ]; then
    printf '  覆盖  %s\n' "$rel"
  else
    printf '  新增  %s\n' "$rel"
  fi
done
echo "  保留  references/personal.md"
echo "  SKILL.md 复制后套用个人覆盖层：「用户偏好」→ 指向 references/personal.md"
echo

if [ "$DRY_RUN" = "1" ]; then
  echo "dry-run：未写入任何文件。"
  exit 0
fi

src_of() {
  if [ "$1" = "SKILL.md" ]; then echo "$WORK/SKILL.md"; else echo "$SRC/$1"; fi
}

for rel in "${FILES[@]}"; do
  mkdir -p "$DST/$(dirname "$rel")"
  cp "$(src_of "$rel")" "$DST/$rel"
done

echo "复制完成，逐文件校验 md5（SKILL.md 比对的是套用覆盖层后的预期内容）："
MISMATCH=0
for rel in "${FILES[@]}"; do
  a="$(md5of "$(src_of "$rel")")"
  b="$(md5of "$DST/$rel")"
  if [ "$a" = "$b" ]; then
    printf '  一致    %s  %s\n' "$a" "$rel"
  else
    MISMATCH=$((MISMATCH + 1))
    printf '  不一致  %s != %s  %s\n' "$a" "$b" "$rel"
  fi
done
echo

PERSONAL_AFTER="$(md5of "$DST/references/personal.md")"
if [ "$PERSONAL_BEFORE" = "$PERSONAL_AFTER" ]; then
  echo "personal.md 未被改动（md5 ${PERSONAL_AFTER}）"
else
  echo "警告：personal.md 的 md5 变了（${PERSONAL_BEFORE} -> ${PERSONAL_AFTER}）" >&2
  MISMATCH=$((MISMATCH + 1))
fi
echo

echo "跑一次单测：python3 $DST/scripts/test_mf.py"
echo "------------------------------------------------------------"
TEST_OK=0
if python3 "$DST/scripts/test_mf.py"; then TEST_OK=1; fi
echo "------------------------------------------------------------"

if [ "$MISMATCH" -ne 0 ]; then
  echo "同步失败：有 ${MISMATCH} 个文件校验不一致。" >&2
  exit 1
fi
if [ "$TEST_OK" -ne 1 ]; then
  echo "同步后单测未通过，请检查。" >&2
  exit 1
fi
echo "同步完成：${#FILES[@]} 个文件一致，单测通过，personal.md 未动。"
