[简体中文](./README.md) | [English](./README.en.md)

# clone-design

`clone-design` 是一个端到端的网站克隆与 landing page 改写 skill。

它现在支持两条主要链路：

```text
URL -> 1:1 clone.html -> 项目文案替换 -> imagegen 素材替换 -> landing-pages/<slug>/index.html
```

```text
URL / clone.html -> 设计信号提取 -> design-md/<slug>/DESIGN.md
```

核心原则是：**先 1:1 还原，再改写内容**。在没有通过浏览器截图检查之前，不改文案、不换图片、不重新设计。

## 主要能力

- 从 URL 抓取真实浏览器渲染后的 DOM、CSS、字体、图片和视觉状态
- 生成高保真 `clone.html`，作为后续改写或设计提炼的基线
- 按 `frontend-ui-clone` 的思路处理懒加载、CSS 变量、渐变文字、内层滚动容器、遮挡浮层和 Tailwind 样式冲突
- 将外部 landing page 的文案替换为当前项目文件夹中的产品文案
- 调用 `imagegen` skill 生成项目相关的 hero 图、产品图、缩略图、头像或装饰图
- 保持原页面布局、间距、字体节奏、动效感和响应式结构
- 继续支持输出 `DESIGN.md`、亮色/暗色 token 预览和 `evidence.json`

## 输出内容

### Landing remix 输出

```text
landing-pages/<slug>/
  index.html
  source-clone.html
  content-inventory.json
  copy-map.json
  image-plan.json
  assets/
    generated/
  qa/
    original-desktop.png
    clone-desktop.png
    final-desktop.png
```

### 捕获材料

```text
captures/<slug>/
  clone.html
  homepage.png
  live.json
```

多页面或多状态时：

```text
captures/<slug>/<page>/
  clone.html
  homepage.png
  live.json
```

### DESIGN.md 输出

```text
design-md/<slug>/
  DESIGN.md
  README.md
  preview.html
  preview-dark.html
  evidence.json
```

## 仓库结构

```text
clone-design/
  SKILL.md
  README.md
  README.en.md
  references/
    ui_clone_workflow.md
    landing_page_remix_workflow.md
    multi_page_session_workflow.md
  scripts/
    extract_landing_inventory.py
    generate_design_md.py
  captures/
  design-md/
  landing-pages/
```

## 快速开始

### 复刻并改写 landing page

```text
/clone-design 把 https://example.com 这个 landing page 1:1 复刻成本项目的官网
```

推荐流程：

1. 用真实浏览器捕获源网页，生成 `captures/<slug>/clone.html`。
2. 截图对比源网页和本地 clone，修复明显差异。
3. 从当前项目文件夹中读取产品名称、定位、功能、CTA、语气和现有素材。
4. 运行 `scripts/extract_landing_inventory.py` 生成 `content-inventory.json`。
5. 生成 `copy-map.json`，再替换可见文案。
6. 生成 `image-plan.json`，用现有项目素材或 `imagegen` 替换 raster 图片。
7. 输出 `landing-pages/<slug>/index.html`。
8. 做桌面和移动端浏览器 QA。

### 只生成 DESIGN.md

```bash
python3 scripts/generate_design_md.py \
  captures/jimeng/clone.html \
  --name "Jimeng AI" \
  --url "https://jimeng.jianying.com/ai-tool/home?type=image&workspace=undefined" \
  --out-dir design-md/jimeng \
  --json-out design-md/jimeng/evidence.json
```

多页面汇总：

```bash
python3 scripts/generate_design_md.py \
  --capture-dir captures/acme \
  --name "Acme" \
  --url "https://app.example.com" \
  --out-dir design-md/acme \
  --json-out design-md/acme/evidence.json
```

## 作为 Skill 使用

把这个仓库放进本地技能目录，或复制这些核心内容：

- `SKILL.md`
- `references/`
- `scripts/extract_landing_inventory.py`
- `scripts/generate_design_md.py`
- 示例 `captures/` 和 `design-md/`

## 说明

- 复刻阶段默认追求 1:1，不做创意发挥。
- 改写阶段只替换文案、图片和品牌内容，尽量不动布局结构。
- `imagegen` 只用于 raster 图片素材；SVG 图标、CSS 渐变、简单矢量装饰默认保留或用代码方式处理。
- 对登录态产品，推荐保留同一个浏览器 session 后抓取少量关键页面或状态，而不是强行全站爬取。
- `DESIGN.md` 生成仍基于 HTML/CSS 信号；情绪判断、token 命名和组件分类建议人工复核。
