# HANDOVER — 公开版重构 + 个人版私人覆盖层 + 一键同步

> 本文件是流程交接产物，不是 skill 文档。里面带本机路径，若仓库要公开发布，可先删除本文件或移到私有位置。
> 任务卡：`t_d273ffef`。日期：2026-11-09。

## 1. 在做什么

把 `movie-finder` 拆成「公开骨架 + 私人覆盖层」：

- **公开版** `/Users/a1/Projects/movie-finder`：通用 SKILL.md + 8 篇 references + 3 个脚本，任何人 clone 就能用。
- **个人版** `/Users/a1/.hermes/skills/media/movie-finder`：同一份通用文件（靠 `scripts/sync.sh` 同步）+ 一个 `references/personal.md` 装私人定稿偏好。
- 以后同步 = 跑一次 `sync.sh`：通用文件全覆盖，`personal.md` 永不覆盖。

## 2. 新旧字节数对照

| 文件 | 之前 | 现在 | 说明 |
|---|---|---|---|
| 公开版 `SKILL.md` | 37,446 | **11,210** | -70%，目标 ≤12,000 |
| 公开版 `README.md` | 8,519 | 11,238 | 补脚本用法 + 法律边界 |
| 公开版 `references/` | 无 | 8 篇 / 72,444 | 从个人版搬入并去掉私人称呼 |
| 公开版 `scripts/` | 无 | `mf.py` 20,907 + `test_mf.py` 9,542 + `sync.sh` 4,976 | 原样复制 + 新脚本 |
| 个人版 `SKILL.md` | 8,835 | 9,970 | = 公开版 + 用户偏好指针 |
| 个人版 `references/personal.md` | 无 | 2,750 | 私人定稿偏好，整节原样搬入 |
| 个人版 `references/` 8 篇通用文件 | 71,569 | 72,444 | 与公开版逐字节一致（26 处私人称呼改成通用表述） |

## 3. 两个目录的最终文件树

### 公开版 `/Users/a1/Projects/movie-finder`

```
./LICENSE                          1,070
./README.md                       11,238
./SKILL.md                        11,210
./HANDOVER.md                     （本文件）
./references/finding-workflow.md  13,385
./references/pan-network-search.md 2,899
./references/pitfalls.md          16,415
./references/quark-save.md        10,134
./references/quark-verify.md       4,679
./references/subtitle-quality-picker.md 4,913
./references/subtitle-sources.md   4,297
./references/subtitle-workflow.md  4,723
./scripts/mf.py                   20,907
./scripts/sync.sh                  4,976
./scripts/test_mf.py               9,542
```

### 个人版 `/Users/a1/.hermes/skills/media/movie-finder`

```
./SKILL.md                         9,970   ← 公开版 + 「用户偏好」指针
./references/finding-workflow.md  13,385
./references/pan-network-search.md 2,899
./references/personal.md           2,750   ← 只在个人版存在
./references/pitfalls.md          16,415
./references/quark-save.md        10,134
./references/quark-verify.md       4,679
./references/subtitle-quality-picker.md 4,913
./references/subtitle-sources.md   4,297
./references/subtitle-workflow.md  4,723
./scripts/mf.py                   20,907
./scripts/test_mf.py               9,542
./HANDOVER.md / REVIEW.md / handover-2026-11-09-rank-dolby-fix.md  （旧流程产物，本次未动）
```

## 4. 9 条验收实测输出

```
## 1) 公开版 SKILL.md 字节数
11210 字节（上限 12000）→ PASS

## 2) 公开版 SKILL.md 私人表述 grep -c
命中 0 行 → PASS

## 3) references 篇数 + scripts 三件
references: 8 篇
finding-workflow.md
pan-network-search.md
pitfalls.md
quark-save.md
quark-verify.md
subtitle-quality-picker.md
subtitle-sources.md
subtitle-workflow.md
scripts:
  mf.py (20907 字节)
  sync.sh (4976 字节)
  test_mf.py (9542 字节)

## 4) 公开版单测
OK
17 passed

## 5) 个人版 personal.md 存在 + 规则齐全
2750 字节  /Users/a1/.hermes/skills/media/movie-finder/references/personal.md
  夸克优先 命中 1
  画质优先级 命中 1
  诺兰   命中 1
  不可直看 命中 1
  闭环交付 命中 1
  别图省事 命中 1
  中英特效 命中 1

## 6) 个人版 SKILL.md 不含私人规则
命中 0 行 → PASS
84:**以 `references/personal.md` 为准**（那是<用户名>的定稿，与本文件任何默认值冲突时，personal.md 赢）。动任何交付动作前先读它。
   （上面一行是脱敏后的引用：原文写的是用户名，本文件用 `<用户名>` 占位）

## 7) sync.sh --dry-run 清单
将覆盖以下 11 个文件（references/personal.md 不在其中）：
  覆盖  SKILL.md
  覆盖  references/finding-workflow.md
  覆盖  references/pan-network-search.md
  覆盖  references/pitfalls.md
  覆盖  references/quark-save.md
  覆盖  references/quark-verify.md
  覆盖  references/subtitle-quality-picker.md
  覆盖  references/subtitle-sources.md
  覆盖  references/subtitle-workflow.md
  覆盖  scripts/mf.py
  覆盖  scripts/test_mf.py
  保留  references/personal.md
  SKILL.md 复制后套用个人覆盖层：「用户偏好」→ 指向 references/personal.md

dry-run：未写入任何文件。
清单里「覆盖/新增」条目含 personal.md 的行数：0

## 8) 同步后个人版单测
OK
17 passed

## 9) 公开版 git 状态
（commit 后 git status --short 输出为空）
```

## 5. commit

- `29dfe69` `refactor: 公开版拆成骨架 + references/scripts，加一键同步脚本`（重构主体）
- `0ba9cfe` `docs: 公开版 HANDOVER（…）`（本文件初版）
- 最新一笔是收尾修复（`sync.sh --help` 少打一行 + 本节更新），hash 见 `git log` 第一条。
- **未 push**（按约束，push 由主 agent 决定）。

## 6. sync.sh 用法示例

```bash
# 只看会覆盖什么
bash ~/Projects/movie-finder/scripts/sync.sh --dry-run

# 真同步：逐文件 md5 校验 + 跑单测
bash ~/Projects/movie-finder/scripts/sync.sh

# 换路径（例如同步到别的机器上的 skill 目录）
SRC=~/Projects/movie-finder DST=~/.hermes/skills/media/movie-finder bash scripts/sync.sh
```

真实输出（结尾部分）：

```text
复制完成，逐文件校验 md5（SKILL.md 比对的是套用覆盖层后的预期内容）：
  一致    8b726f5fd0491d8d5b571632021fd955  SKILL.md
  一致    43f16c640dd724c0b94cb33d7ff15321  references/finding-workflow.md
  ...
personal.md 未被改动（md5 d73cc504deb87df8063ba43dc60c3204）

跑一次单测：python3 /Users/a1/.hermes/skills/media/movie-finder/scripts/test_mf.py
------------------------------------------------------------
Ran 17 tests in 0.001s

OK
17 passed
------------------------------------------------------------
同步完成：11 个文件一致，单测通过，personal.md 未动。
```

行为约定：

- `personal.md` 不存在 → 直接报错退出（退出码 1），一个文件都不写。已实测：指向一个没有 `personal.md` 的临时目录时，该目录里文件数仍为 0。
- 只复制清单内文件，**不做镜像删除**：个人版多出来的私有 references 不会被删。
- **SKILL.md 会套用个人覆盖层**：复制后把「用户偏好（默认值）」那节换成指向 `personal.md` 的指针。不加这一步，同步会把个人版 SKILL.md 冲成公开默认值，指针丢失（这是实现过程中实际踩到的坑，已修）。
- 二次执行幂等：连续跑两次，个人版 `SKILL.md` md5 都是 `8b726f5f…`。

## 7. 本次 diff 范围

| 文件 | 动作 | 为什么在范围内 |
|---|---|---|
| 公开版 `SKILL.md` | 重写 | 交付一（瘦身到 11,210 字节，保留安装 / 配置 / 依赖声明 / 默认偏好，补三块通用知识） |
| 公开版 `README.md` | 增补 | 交付一 1.4（脚本用法 + 法律边界） |
| 公开版 `references/*.md` | 新增 8 篇 | 交付一 1.1（从个人版搬入，私人称呼替换） |
| 公开版 `scripts/mf.py`、`test_mf.py` | 新增 | 交付一 1.2（原样复制） |
| 公开版 `scripts/sync.sh` | 新增 | 交付三 |
| 个人版 `references/personal.md` | 新增 | 交付二 1 |
| 个人版 `SKILL.md` | 替换偏好节 + 其余对齐公开版 | 交付二 2、3 |
| 个人版 `references/` 8 篇、`scripts/mf.py` | 被 sync 覆盖 | 同步的必然结果（见下） |

范围外的顺手改动：无。`LICENSE`、个人版 `HANDOVER.md` / `REVIEW.md` / `handover-2026-11-09-rank-dolby-fix.md` 均未动。

**需要审查员注意的一处既定冲突**：任务要求「个人版那 8 篇 references 内容不许改（只新增 personal.md）」，但同一份任务又要求把它们搬进公开版前「有私人痕迹就去掉那一句」。8 篇里有 6 篇共 26 处写着私人称呼/私人经历（「<用户名>」「他点头」「原话」等），公开仓库不能带这些。处理方式：在**公开版**做替换，再由 `sync.sh` 把替换后的同一份同步回个人版——这样两边仍然是「共用同一份」。替换只涉及人称和个别叙述句，没有删改知识内容。逐条替换清单见下：

- `finding-workflow.md`（6 处）：标题里的「（<用户名> 2026-10-29 明确要求）」→「（维护者实践总结的升级路径）」；「<用户名> 2026-10-29 明确批评过」→「这条规则来自真实使用的反复教训」；「<用户名>一句…才逼出正确答案」→「一句…往往能逼出正确答案」；「让<用户名>自己点」→「让用户自己点」；「报告给<用户名>」→「报告给用户」；「等<用户名>拍板…点头后」→「等用户拍板…确认后」。
- `pitfalls.md`（8 处）：「<用户名>会明确拒绝，原话…」→「用户要的是最高画质」；「<用户名>会把…当成偷懒」→「只查了一处就说没有，等同于偷懒」；「<用户名>说的「夸克」」→「用户说的「夸克」」；「不要把验证码截图发给<用户名>」→「…发给用户」；「<用户名>说「翻译有问题」」→「用户说…」；「他点头 → 转存」→「用户确认 → 转存」；「<用户名>不会下」→「用户不会下」；「必须等他点头」→「必须等用户确认」。
- `quark-save.md`（7 处）：「（<用户名> 2026-10-22 指定）」→「（默认交付目录）」；`<<用户名>原话逐字>` → `<用户原话逐字>`（3 处）；「必须是<用户名>原话逐字」→「必须是用户原话逐字」；「<用户名>点头 → 转存」→「用户确认 → 转存」；「让<用户名>自己搬字幕」→「让用户自己搬字幕」。
- `pan-network-search.md`（1 处）：「报给<用户名> → 他点头再转存」→「报给用户 → 用户确认后再转存」。
- `quark-verify.md`（1 处）：「（<用户名>侧已登录会自动转存）」→「（调用方已登录会自动转存）」。
- `subtitle-workflow.md`（3 处）：「不发<用户名>核对」→「不发用户核对」；「<用户名>说「这份字幕翻译有问题」」→「用户说…」；「列全让他挑」→「列全让用户挑」。
- `scripts/mf.py`（1 处，注释）：`# BluRay 不在<用户名>的五档里` → `# BluRay 不在默认五档里`。代码逻辑零改动。
- `subtitle-quality-picker.md`、`subtitle-sources.md`：无私人痕迹，未改。

## 8. 已知未覆盖的风险点

1. **sync.sh 依赖两个固定标题**：公开版 `SKILL.md` 的 `## 用户偏好（默认值，可按「配置」一节改）` 和 `# 第一部分：找片`。以后改这两个标题，sync 会直接报错停下（有意 fail-fast，不会静默生成错的个人版）。要一起改 `sync.sh` 里的 `HEAD` / `END` 常量。
2. **sync.sh 不做备份**：覆盖前不存副本，个人版不是 git 仓库。误覆盖只能靠公开版 git 历史 + 手工重建。后续可加 `--backup`。
3. **个人版 references 从此不能单独手改**：下次 sync 会覆盖。要改就改公开版再 sync。
4. **`verify` 只在真接口上验过 `dead` 分支**（`41006`）。`alive` / `half_dead` / `unknown` 由 17 个离线用例注入覆盖，没有真实活链样本。
5. **`sync.sh` 只在 macOS bash 3.2 上跑过**，Linux（md5sum 分支）写了但未实测。
6. **README 的 verify 示例是 dead 样本**，没有 alive 的真实输出片段（不想编）。
7. **公开版 `HANDOVER.md` 会随仓库走**：里面带本机绝对路径。若公开发布，建议先删。

## 9. 自证材料（实际跑过的命令）

```bash
cd ~/.hermes/skills/media/movie-finder && python3 scripts/test_mf.py   # 17 passed（改前基线）
cd ~/Projects/movie-finder && python3 scripts/test_mf.py               # 17 passed
python3 scripts/mf.py verify 0123456789abcdef0123456789abcdef          # 真接口，返回 dead / code=41006
python3 scripts/mf.py rank <candidates.json>                            # README 里那段真实输出
bash scripts/sync.sh --dry-run                                          # 11 个文件，0 个 personal.md
DST=<无 personal.md 的临时目录> bash scripts/sync.sh                     # 退出码 1，未写入任何文件
bash scripts/sync.sh                                                    # 11 个一致 + 17 passed + personal.md md5 未变
bash scripts/sync.sh                                                    # 第二次：SKILL.md md5 仍为 8b726f5f…（幂等）
diff -u ~/Projects/movie-finder/SKILL.md ~/.hermes/skills/media/movie-finder/SKILL.md  # 只差「用户偏好」一节
```

## 10. 复现与验证命令（给审查员）

```bash
PUB=~/Projects/movie-finder
PER=~/.hermes/skills/media/movie-finder

wc -c "$PUB/SKILL.md"                                   # 期望 11210（≤12000）
grep -c '亮子\|他点头\|原话' "$PUB/SKILL.md"             # 期望 0（grep 退出码 1）
ls "$PUB"/references/*.md | wc -l                       # 期望 8
ls "$PUB"/scripts                                       # mf.py sync.sh test_mf.py
cd "$PUB" && python3 scripts/test_mf.py                 # 期望 17 passed
grep -c '夸克优先\|别图省事' "$PER/SKILL.md"            # 期望 0
grep -c '夸克优先\|别图省事' "$PER/references/personal.md"  # 期望 ≥1
bash "$PUB/scripts/sync.sh" --dry-run | grep 'personal.md'  # 只应出现在「保留」和说明行
python3 "$PER/scripts/test_mf.py"                       # 期望 17 passed
cd "$PUB" && git status --short                          # 期望空
```

## 11. 回滚办法

- 公开版：`cd ~/Projects/movie-finder && git reset --hard 33d7a8a`（回到重构前那一版），或 `git revert 29dfe69`。
- 个人版：没有版本控制。目标态本身就是这次要的形态；若要退回旧形态，把公开版 `SKILL.md` 的「用户偏好」节换回 `references/personal.md` 里的整节内容即可（那一节是原样保存的），其余通用文件本来就和公开版同源。
- 旧个人版 `SKILL.md` 的临时备份在 `~/.hermes/profiles/agents-md-code/cache/scratch/personal-SKILL.before.md`（scratch 24 小时清理，不要依赖它长期存在）。

## 12. 遗留问题

1. `sync.sh` 无备份能力（见风险 2）。
2. 未 push：`origin` 仍是 `https://github.com/wjl3285857571/movie-finder.git`，本地领先 2 个提交。
3. 个人版旧流程产物（`HANDOVER.md` / `REVIEW.md` / `handover-2026-11-09-rank-dolby-fix.md`）按约束保留原样，是否清理由后续决定。
4. 公开版 `SKILL.md` 里的安装命令写死了仓库地址，如果以后 fork 给别人用，那段可以改成占位符。
