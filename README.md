[简体中文](./README.md) | [English](./README.en.md)

# clone-design

将任意网站整理成可复用的 `DESIGN.md` 设计文档包。

`clone-design` 现在内置完整链路，适合这条工作流：

```text
URL -> clone-design 内建克隆流程 -> captures/<slug>/<page>/clone.html -> design-md/<slug>/
```

它的重点不是像素级重建，而是先复用 `frontend-ui-clone` 的克隆方法拿到高质量 `clone.html`，再把页面里可复用的视觉规则提炼出来，方便后续交给 AI、设计师或前端继续复现和扩展。

现在它不只支持单页，也支持：

- 登录后保留同一个浏览器会话
- 由你选择多个关键页面或界面状态
- 将多个 `clone.html` 一起汇总成一个站点级 `DESIGN.md`

案例输出目录遵循接近 `awesome-design-md` 的结构：

```text
design-md/<slug>/
```

## 产出内容

- `captures/<slug>/clone.html`：单页模式下的自包含网页快照
- `captures/<slug>/<page>/clone.html`：多页面模式下，每个页面或状态各自的快照
- `captures/<slug>/<page>/homepage.png`：抓取时的页面截图
- `captures/<slug>/<page>/live.json`：可选的页面实时样式证据
- `captures/<slug>/capture-plan.json`：可选的页面采集计划
- `DESIGN.md`：整理后的设计系统说明
- `README.md`：案例目录说明
- `preview.html`：亮色设计 Token 预览
- `preview-dark.html`：暗色设计 Token 预览
- `evidence.json`：可选的原始提取证据

## 仓库结构

```text
clone-design/
  SKILL.md
  README.md
  README.en.md
  references/
    ui_clone_workflow.md
    multi_page_session_workflow.md
  scripts/
    generate_design_md.py
  design-md/
    jimeng/
      DESIGN.md
      README.md
      preview.html
      preview-dark.html
      evidence.json
  captures/
    jimeng/
      clone.html
      live.json
      homepage.png
```

## 快速开始

1. 直接把网址交给 skill。

```text
/clone-design https://example.com
```

这一步会在 skill 内部直接复用 `frontend-ui-clone` 的克隆流程，不需要用户再安装另一个 skill。

2. 如果目标站点需要登录，或者你想抓多个页面，可以走同一个浏览器会话：

- 先登录
- 再选择你要的几个页面或状态
- 每个页面会保存到 `captures/<slug>/<page>/`
- 最后统一汇总成一个 `design-md/<slug>/`

3. 如果你已经有现成的 `clone.html`，也可以只运行生成脚本：

```bash
python3 scripts/generate_design_md.py \
  captures/jimeng/clone.html \
  --name "Jimeng AI" \
  --url "https://jimeng.jianying.com/ai-tool/home?type=image&workspace=undefined" \
  --out-dir design-md/jimeng \
  --json-out design-md/jimeng/evidence.json
```

4. 多页面汇总时，可以直接传多个 HTML，或者整个 capture 目录：

```bash
python3 scripts/generate_design_md.py \
  captures/acme/home/clone.html \
  captures/acme/workspace/clone.html \
  captures/acme/settings-modal-open/clone.html \
  --name "Acme" \
  --url "https://app.example.com" \
  --out-dir design-md/acme \
  --json-out design-md/acme/evidence.json
```

```bash
python3 scripts/generate_design_md.py \
  --capture-dir captures/acme \
  --name "Acme" \
  --url "https://app.example.com" \
  --out-dir design-md/acme \
  --json-out design-md/acme/evidence.json
```

5. 打开生成后的 `DESIGN.md`，把不够确定的描述明确标注为 inferred，而不是 observed。

## 作为 Skill 使用

你可以直接把这个仓库放进本地技能目录，或者按需复制下面这些核心文件：

- `SKILL.md`
- `scripts/generate_design_md.py`
- `design-md/` 和 `captures/` 下的示例内容

## 已包含案例

当前仓库已内置一套完整案例：

- [jimeng 设计产物](./design-md/jimeng/)
- [jimeng 抓取材料](./captures/jimeng/)

这套案例同时保留了两部分内容：

- `captures/jimeng/`：浏览器抓取得到的源材料
- `design-md/jimeng/`：最终整理出的设计文档包

## 说明

- 现在不需要单独安装 `frontend-ui-clone`；`clone-design` 会在 skill 内部直接复用那套克隆流程。
- 对登录态产品，推荐保留同一个浏览器 session 后抓多个关键页面，而不是强行全站爬取。
- 输入的 `clone.html` 质量越高，输出结果越可靠。
- 提取器主要读取 HTML 与 CSS 信号，能汇总多个页面，但无法完整恢复未被捕获的运行时动态状态。
- 情绪判断、Token 角色命名和组件分类，仍建议做一次人工复核。
