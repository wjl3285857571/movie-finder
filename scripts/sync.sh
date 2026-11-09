#!/usr/bin/env bash
# 把公开版的通用文件同步到本机 Hermes 的个人 skill，保留 references/personal.md。
#
#   bash scripts/sync.sh --dry-run             # 只看会覆盖哪些文件，不写盘、不备份
#   bash scripts/sync.sh                       # 备份 + 同步 + 逐文件 md5 校验 + 跑单测
#   bash scripts/sync.sh --no-backup           # 跳过备份（清楚后果时用）
#   bash scripts/sync.sh --restore <归档>      # 从备份恢复（绝对路径或备份目录下的文件名）
#
# 每次真同步前会把整个 DST 备份到 ~/.hermes/backups/movie-finder-sync/<YYYYmmdd-HHMMSS>.tar.gz，
# 只保留最近 10 个。SKILL.md 复制后会自动套一层「个人覆盖层」：把「用户偏好」那节换成
# 指向 references/personal.md 的指针，避免个人偏好被通用默认值冲掉。
#
# 可用环境变量覆盖路径：
#   SRC=~/Projects/movie-finder DST=~/.hermes/skills/media/movie-finder \
#   BACKUP_DIR=~/.hermes/backups/movie-finder-sync bash scripts/sync.sh
set -euo pipefail

SRC="${SRC:-$HOME/Projects/movie-finder}"
DST="${DST:-$HOME/.hermes/skills/media/movie-finder}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/.hermes/backups/movie-finder-sync}"
KEEP_BACKUPS=10

# 去掉结尾斜杠，保证 dirname/basename 拆得对
SRC="${SRC%/}"
DST="${DST%/}"
BACKUP_DIR="${BACKUP_DIR%/}"

DRY_RUN=0
DO_BACKUP=1
RESTORE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --no-backup) DO_BACKUP=0; shift ;;
    --restore)
      [ $# -ge 2 ] || { echo "错误：--restore 需要一个归档路径或文件名" >&2; exit 2; }
      RESTORE="$2"; shift 2
      ;;
    -h|--help)
      sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "未知参数：$1（支持 --dry-run / --no-backup / --restore <归档> / --help）" >&2
      exit 2
      ;;
  esac
done

die() { echo "错误：$*" >&2; exit 1; }

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

# ---------------------------------------------------------------- 恢复模式
if [ -n "$RESTORE" ]; then
  case "$RESTORE" in
    */*) ARCH="$RESTORE" ;;
    *)   ARCH="$BACKUP_DIR/$RESTORE" ;;
  esac
  [ -f "$ARCH" ] || die "找不到备份归档：${RESTORE}（按文件名找的目录是 ${BACKUP_DIR}）"
  [ -d "$DST" ] || die "DST 不存在：$DST"
  tar -tzf "$ARCH" >/dev/null 2>&1 || die "不是可读的 tar.gz 归档：$ARCH"

  mkdir -p "$WORK/x"
  tar -xzf "$ARCH" -C "$WORK/x" || die "解压失败：$ARCH"

  # 归档若只有一个顶层目录（备份时是 tar -C 父目录 basename DST），剥掉它
  ROOT="$WORK/x"
  TOP_N="$(find "$WORK/x" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ')"
  TOP_ONE="$(find "$WORK/x" -mindepth 1 -maxdepth 1 | head -1)"
  if [ "$TOP_N" = "1" ] && [ -d "$TOP_ONE" ]; then ROOT="$TOP_ONE"; fi

  TOTAL=0
  OVERWRITE=0
  while IFS= read -r f; do
    rel="${f#"$ROOT"/}"
    TOTAL=$((TOTAL + 1))
    if [ -e "$DST/$rel" ]; then OVERWRITE=$((OVERWRITE + 1)); fi
  done < <(find "$ROOT" -type f | sort)
  [ "$TOTAL" -gt 0 ] || die "归档里没有文件：$ARCH"

  echo "归档：$ARCH"
  echo "恢复目标：$DST"
  echo "归档含 ${TOTAL} 个文件：其中 ${OVERWRITE} 个将覆盖现有文件，$((TOTAL - OVERWRITE)) 个为新增（归档里没有的文件不删除）。"
  echo

  if [ "$DRY_RUN" = "1" ]; then
    echo "dry-run：未写盘、未改动任何文件。"
    exit 0
  fi

  (cd "$ROOT" && tar -cf - .) | (cd "$DST" && tar -xf -) || die "写入 $DST 失败"

  echo "逐文件 md5 比对（归档 vs 恢复后）："
  OK=0
  BAD=0
  while IFS= read -r f; do
    rel="${f#"$ROOT"/}"
    a="$(md5of "$f")"
    b="$(md5of "$DST/$rel")"
    if [ "$a" = "$b" ]; then
      OK=$((OK + 1)); printf '  一致    %s  %s\n' "$a" "$rel"
    else
      BAD=$((BAD + 1)); printf '  不一致  %s != %s  %s\n' "$a" "$b" "$rel"
    fi
  done < <(find "$ROOT" -type f | sort)
  echo
  if [ "$BAD" -ne 0 ]; then
    echo "恢复校验失败：${BAD} 个文件与归档不一致。" >&2
    exit 1
  fi
  echo "恢复完成：${OK} 个文件全部与归档一致。"
  exit 0
fi

# ---------------------------------------------------------------- 同步模式
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

# 生成「公开版 SKILL.md + 个人覆盖层」的预期内容。
# 定位不依赖标题措辞：起点是第一个 ^## 用户偏好 行（前缀匹配），终点是其后第一个一级标题 ^# 行，
# 找不到一级标题就取到文件末尾。围栏代码块里的 # 行不算标题。
python3 - "$SRC/SKILL.md" "$WORK/SKILL.md" <<'PY' || die "生成个人覆盖层失败"
import io
import sys

src, dst = sys.argv[1], sys.argv[2]
START_PREFIX = "## 用户偏好"
POINTER = (
    "## 用户偏好\n\n"
    "**以 `references/personal.md` 为准**（那是本机维护者的定稿，与本文件任何默认值冲突时，personal.md 赢）。"
    "动任何交付动作前先读它。\n\n"
)
lines = io.open(src, encoding="utf-8").read().splitlines(keepends=True)

start = None
for i, line in enumerate(lines):
    if line.startswith(START_PREFIX):
        start = i
        break
if start is None:
    sys.exit("SKILL.md 里找不到「## 用户偏好」小节（前缀匹配），无法套用个人覆盖层")

end = len(lines)
in_fence = False
for j in range(start + 1, len(lines)):
    line = lines[j]
    if line.lstrip().startswith("```"):
        in_fence = not in_fence
        continue
    if not in_fence and line.startswith("# "):
        end = j
        break

out = "".join(lines[:start]) + POINTER + "".join(lines[end:])
io.open(dst, "w", encoding="utf-8").write(out)
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
if [ "$DO_BACKUP" = "1" ]; then
  echo "备份：$BACKUP_DIR/<YYYYmmdd-HHMMSS>.tar.gz（保留最近 ${KEEP_BACKUPS} 个）"
else
  echo "备份：已跳过（--no-backup）"
fi
echo

if [ "$DRY_RUN" = "1" ]; then
  echo "dry-run：未备份、未写入任何文件。"
  exit 0
fi

# ---------------------------------------------------------------- 备份
BACKUP_PATH=""
if [ "$DO_BACKUP" = "1" ]; then
  mkdir -p "$BACKUP_DIR" || die "无法创建备份目录：$BACKUP_DIR"
  TS="$(date +%Y%m%d-%H%M%S)"
  BACKUP_PATH="$BACKUP_DIR/$TS.tar.gz"
  n=2
  while [ -e "$BACKUP_PATH" ]; do
    BACKUP_PATH="$BACKUP_DIR/$TS-$n.tar.gz"
    n=$((n + 1))
  done
  COPYFILE_DISABLE=1 tar -czf "$BACKUP_PATH" -C "$(dirname "$DST")" "$(basename "$DST")" \
    || die "备份失败：$BACKUP_PATH"
  echo "备份完成：${BACKUP_PATH}（$(du -h "$BACKUP_PATH" | awk '{print $1}')）"

  # 按文件名时间戳排序，只留最近 KEEP_BACKUPS 个
  OLD=()
  while IFS= read -r f; do OLD+=("$f"); done \
    < <(find "$BACKUP_DIR" -maxdepth 1 -type f -name '*.tar.gz' | sort)
  EXCESS=$(( ${#OLD[@]} - KEEP_BACKUPS ))
  if [ "$EXCESS" -gt 0 ]; then
    i=0
    while [ "$i" -lt "$EXCESS" ]; do
      rm -f -- "${OLD[$i]}"
      echo "  删除旧备份  $(basename "${OLD[$i]}")"
      i=$((i + 1))
    done
  fi
  echo
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
  [ -n "$BACKUP_PATH" ] && echo "可用备份回退：bash scripts/sync.sh --restore $BACKUP_PATH" >&2
  exit 1
fi
if [ "$TEST_OK" -ne 1 ]; then
  echo "同步后单测未通过，请检查。" >&2
  [ -n "$BACKUP_PATH" ] && echo "可用备份回退：bash scripts/sync.sh --restore $BACKUP_PATH" >&2
  exit 1
fi
echo "同步完成：${#FILES[@]} 个文件一致，单测通过，personal.md 未动。"
if [ -n "$BACKUP_PATH" ]; then
  echo "本次备份：$BACKUP_PATH"
  echo "回退方式：bash scripts/sync.sh --restore $BACKUP_PATH"
fi
