[简体中文](./README.md) | [English](./README.en.md)

# clone-design

将任意网站整理成可复用的 `DESIGN.md` 设计文档包。

`clone-design` 适合这条工作流：

```text
URL -> UI clone -> self-contained HTML -> clone-design -> design-md/<slug>/
```

它的重点不是像素级重建，而是把页面里可复用的视觉规则提炼出来，方便后续交给 AI、设计师或前端继续复现和扩展。

案例输出目录遵循接近 `awesome-design-md` 的结构：

```text
design-md/<slug>/
```

## 产出内容

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

1. 先准备一个自包含页面快照。
   最理想的输入是通过 `frontend-ui-clone` 或 Playwright 之类方式拿到的 `clone.html`。
2. 运行生成脚本：

```bash
python3 scripts/generate_design_md.py \
  captures/jimeng/clone.html \
  --name "Jimeng AI" \
  --url "https://jimeng.jianying.com/ai-tool/home?type=image&workspace=undefined" \
  --out-dir design-md/jimeng \
  --json-out design-md/jimeng/evidence.json
```

3. 打开生成后的 `DESIGN.md`，把不够确定的描述明确标注为 inferred，而不是 observed。

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

- 输入的 `clone.html` 质量越高，输出结果越可靠。
- 提取器主要读取 HTML 与 CSS 信号，无法完整恢复仅存在于运行时的动态状态。
- 情绪判断、Token 角色命名和组件分类，仍建议做一次人工复核。
