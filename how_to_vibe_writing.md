# How to Vibe Writing

本文档记录在本仓库下用 Claude Code 辅助完成"毕业论文写作 + 图表制作 + Overleaf 同步"的完整流程，方便后续使用者复现。

适用场景：
- 本地修改 LaTeX 章节文件后，同步到 Overleaf 云端项目
- 用 draw.io（Python 程序化生成 + puppeteer 渲染）制作论文图表
- 通过 Claude Code skill 系统让 AI 直接完成上述链路

---

## 0. 目录结构约定

```
CodeAgentCostOptimization/
├── overleaf/                       # Overleaf 项目本地副本
│   ├── .olauth                     # Overleaf 登录凭证（pickle，本地，不入 git）
│   ├── make_olauth.py              # 凭证生成脚本
│   └── paper/
│       ├── main.tex
│       ├── data/                   # 各章节 .tex 文件
│       │   ├── chap01.tex ~ chap07.tex
│       │   └── ...
│       ├── figures/                # 图片（PDF/PNG）
│       └── ref/refs.bib
├── tools/drawio/                   # draw.io 图表生成工具
│   ├── drawio_generator.py         # Python 程序化生成 .drawio XML
│   ├── render.js                   # puppeteer 渲染 .drawio → PNG/SVG
│   ├── mxClient.min.js             # mxGraph 客户端库（被 render.js 使用）
│   ├── node_modules/               # puppeteer-core 等依赖
│   └── output/                     # 渲染产物
├── skills/                         # Claude Code skill 目录
│   ├── overleaf-sync/              # Overleaf 同步 skill
│   └── thesis-writing-guide/       # 论文写作 skill
└── how_to_vibe_writing.md          # 本文档
```

---

## 1. 获取 Overleaf 凭证

Overleaf 云端项目没有官方 CLI，只能通过浏览器 Cookie 模拟登录。流程如下：

### 1.1 从浏览器复制三个值

1. 在浏览器打开 https://www.overleaf.com 并登录
2. `F12` 打开 DevTools → `Application` 选项卡 → `Cookies` → `https://www.overleaf.com`
3. 找到并复制这两个 cookie 的值：
   - `overleaf_session2`
   - `GCLB`
4. 切到 `Console` 选项卡，在 https://www.overleaf.com/project 页面执行：
   ```js
   document.getElementsByName('ol-csrfToken')[0].content
   ```
   复制输出的 token

### 1.2 生成 .olauth 文件

编辑 `overleaf/make_olauth.py`，把刚才复制的三个值填进去：

```python
OVERLEAF_SESSION2 = "s%3A..."   # 第一步 cookie 值
GCLB              = "CM..."      # 第二步 cookie 值
CSRF_TOKEN        = "G...."      # 第三步 console 输出
```

运行：
```bash
cd /home/azureuser/jrh/CodeAgentCostOptimization/overleaf
python3 make_olauth.py
```

会在 `overleaf/.olauth` 生成一个 pickle 文件。所有后续同步操作都读取这个文件。

### 1.3 记住项目 ID

从浏览器地址栏 `overleaf.com/project/69b27599cb82593435d69eb7` 取出最后一段，就是 project ID。本项目 ID：

```
69b27599cb82593435d69eb7
```

---

## 2. Overleaf ↔ 本地同步

### 2.1 基于 `ols` CLI（文本 .tex 文件）

安装过的 `overleaf-sync` 包已经打上兼容补丁（详见 `skills/overleaf-sync/references/olclient-patch.md`）。

```bash
cd /home/azureuser/jrh/CodeAgentCostOptimization/overleaf/paper

# 双向同步
ols --store-path ../.olauth -n "毕业论文___江润汉"

# 只推本地 → Overleaf
ols --store-path ../.olauth -n "毕业论文___江润汉" -l

# 只拉 Overleaf → 本地
ols --store-path ../.olauth -n "毕业论文___江润汉" -r

# 列出可用项目
ols list --store-path ../.olauth
```

### 2.2 单文件 OT 上传（推荐用于单章节覆盖）

当 `ols` 整体同步过慢或冲突时，用 OT 协议直接覆盖某个远端文档：

```bash
cd /home/azureuser/jrh/CodeAgentCostOptimization
python3 skills/overleaf-sync/references/ot-upload.py \
    overleaf/paper/data/chap05.tex \
    69b27599cb82593435d69f24
```

第二个参数是远端的 `doc_id`（每个 `.tex` 文件一个）。获取方式：Overleaf Web UI 打开该文件 → 查看浏览器 Network → `joinDoc` 事件里有 doc id，或从 `joinProjectResponse` 里找 folder tree。

**几个关键协议细节（都已在 `ot-upload.py` 里处理了）：**
- Socket.IO v1 URL 里必须带 `?projectId=` 才能让服务器进入 project 上下文
- 消息格式必须用 `5:N+::`（sequence 后面的 `+` 不能省），否则服务器只回 bare ack
- `applyOtUpdate` 里的 `d`（删除）字段必须等于服务端当前文档的真实 Unicode 字符串；而 `joinDoc` 返回来的字符串是 mojibake（UTF-8 字节被当成 Latin-1 解码），所以要先 `.encode('latin-1').decode('utf-8')` 还原
- 发完 `applyOtUpdate` 后必须保持连接 ≥35s 让服务器 flush 到持久化存储，再 `leaveDoc` 关闭；提前断连会导致更新被丢弃

### 2.3 图片/二进制文件上传

**Overleaf 的 REST 上传接口对我们的脚本不开放**（`/project/{id}/upload` 一律返回 `invalid_filename`，即使 MIME 和 CSRF 都正确）。

目前唯一可靠方案：**在 Overleaf Web UI 手动拖拽上传**。

流程：
1. 本地生成好 PDF（见第 3 节）到 `overleaf/paper/figures/xxx.pdf`
2. 浏览器打开 Overleaf 项目
3. 左侧 `figures/` 文件夹右键 → `Upload` → 选择本地文件
4. 如果是覆盖，先在 Web UI 删掉旧文件再传

---

## 3. 用 draw.io 画图

### 3.1 两种方式

| 方式 | 用途 | 工具 |
|---|---|---|
| 手画 → 导出 | 自由度高、不规则图表 | draw.io Web 或 Desktop |
| Python 程序化生成 | 结构化架构图、方法对比图，可复现、可重构 | `tools/drawio/drawio_generator.py` |

**本项目所有图表都用"Python 程序化 + puppeteer 渲染"的组合**，因为可以版本化、可以在对话中迭代修改。

### 3.2 用 `drawio_generator.py` 写图

最小例子：

```python
import sys
sys.path.insert(0, 'tools/drawio')
from drawio_generator import DrawioDiagram, Style

d = DrawioDiagram("我的图", width=1200, height=600)

# 三个方框横向排列，自动连线
ids = d.add_flowchart_row(
    ["输入", "处理", "输出"],
    y=200, x_start=100, gap=80,
    box_w=160, box_h=60,
    style=Style.BOX,   # 浅蓝 / BOX_GREEN / BOX_YELLOW / BOX_RED ...
)

# 带副标题的盒子
d.add_box(
    "<b>核心模块</b><br/><font style='font-size:11px'>副标题</font>",
    x=500, y=400, w=200, h=80, style=Style.BOX_DARK,
)

# 手动连线
d.add_arrow(ids[0], ids[2], label="跳过中间", style=Style.ARROW_DASHED)

d.save("tools/drawio/output/demo.drawio")
```

运行（必须在项目根目录）：
```bash
cd /home/azureuser/jrh/CodeAgentCostOptimization
python3 your_script.py
```

### 3.3 关键样式常量

（定义在 `drawio_generator.py`）

| 常量 | 效果 |
|---|---|
| `Style.BOX` | 浅蓝矩形（默认） |
| `Style.BOX_GREEN` / `BOX_YELLOW` / `BOX_RED` | 浅色系矩形 |
| `Style.BOX_DARK` | 深灰底白字（突出核心组件） |
| `Style.BOX_GRAY` | 中性灰（输入、度量、标签） |
| `Style.DIAMOND` | 判断节点 |
| `Style.TERMINAL` | 流程图起止端（大圆角） |
| `Style.DATABASE` | 数据库圆柱 |
| `Style.ARROW` | 正交折线（默认箭头） |
| `Style.ARROW_DASHED` | 虚线箭头 |

**配色建议**：论文图表选浅色系（fillColor `#dae8fc` / `#d5e8d4` / `#ffe6cc` / `#e1d5e7` / `#f5f5f5`），描边用同色系深一档。深色只留给需要突出的 1-2 个核心组件。

### 3.4 渲染为 PNG

```bash
cd /home/azureuser/jrh/CodeAgentCostOptimization/tools/drawio
node render.js output/demo.drawio output/demo.png 2.0
```

第三个参数是缩放倍数（默认 1.5，论文用 2.0 左右清晰度够用）。

**依赖**：`puppeteer-core` + 系统 `/usr/bin/chromium-browser`（render.js 里硬编码路径）。已通过 `npm install` 装好在 `tools/drawio/node_modules/`。

### 3.5 转成真正的 PDF

`render.js` 的 `.pdf` 输出其实是伪装成 `.pdf` 后缀的 PNG（内容还是 PNG 格式，Acrobat 打不开）。**务必用 `img2pdf` 转一遍**：

```bash
pip install img2pdf
```

```python
import img2pdf
from PIL import Image
import numpy as np

png = 'tools/drawio/output/demo.png'
pdf = 'overleaf/paper/figures/demo.pdf'

# 自动裁白边（draw.io 默认画布常有大片空白）
img = Image.open(png).convert('RGB')
arr = np.array(img)
nw = np.any(arr < 240, axis=2)
rows = np.any(nw, axis=1); cols = np.any(nw, axis=0)
rmin, rmax = np.where(rows)[0][[0, -1]]
cmin, cmax = np.where(cols)[0][[0, -1]]
pad = 20
img.crop((max(0,cmin-pad), max(0,rmin-pad),
          min(arr.shape[1], cmax+1+pad), min(arr.shape[0], rmax+1+pad))
        ).save('_cropped.png')

with open('_cropped.png', 'rb') as f:
    pdf_bytes = img2pdf.convert(f)
with open(pdf, 'wb') as f:
    f.write(pdf_bytes)
```

**为什么必须裁白边**：`render.js` 渲染出来的 PNG 四周常有大片空白（画布尺寸 > 内容 bounding box），直接塞进 PDF 后 LaTeX 的 `\includegraphics` 会把白边一起算进去，图片看起来只占 PDF 的一角。

### 3.6 在 LaTeX 里引用

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.95\linewidth]{figures/method_deps.pdf}
  \caption{方法模块依赖关系}
  \label{fig:method-deps}
\end{figure}
```

然后**手动在 Overleaf Web UI 把 `method_deps.pdf` 拖进 `figures/`**（见 2.3 节）。

---

## 4. GitHub 同步

本项目 GitHub 远端主要用于：代码、实验脚本、论文源码（含 `overleaf/paper/`）三者版本化。

### 4.1 忽略规则（`.gitignore`）

必须排除的：
- `overleaf/.olauth`（含 session cookie，敏感）
- `overleaf/.codex` / `overleaf/.git`（Overleaf 自己的元数据）
- `tools/drawio/node_modules/`
- `**/__pycache__/`、`*.pyc`
- 实验产物目录 `experiments/subset_*/`（体积大）

### 4.2 常规流程

```bash
cd /home/azureuser/jrh/CodeAgentCostOptimization
git status
git add -A  # 或只 add 具体文件
git commit -m "update chap05 and method_deps figure"
git push
```

**注意**：Claude Code 的默认策略是不主动提交，需要用户显式说"提交 / commit / 推送"才会执行。推送前会列出改动清单给你确认。

### 4.3 写作 → 同步三端

完整一次迭代：

```
本地编辑 chap05.tex
        │
        ├─► git commit + push      (备份到 GitHub)
        └─► ols / ot-upload.py     (发布到 Overleaf)
                │
                └─► Overleaf 编译、预览
                        │
                        └─► 如需改图：
                              本地改 .py → 渲染 PNG → 转 PDF → Web UI 上传
```

---

## 5. 让 Claude Code 把上述链路自动化

### 5.1 已有的 skill

目录 `skills/` 下：

- `overleaf-sync/SKILL.md`：告诉 Claude 何时调用 `ols` / `ot-upload.py`，附带所有协议细节（cookie 刷新、mojibake fix、flush window 等）
- `thesis-writing-guide/SKILL.md`：论文写作风格约束（术语、citations 风格等）

Claude Code 启动时会读取这些 `SKILL.md`。当你说"把 chap05 上传到 Overleaf"时，它会自动调 `ot-upload.py` 并传正确的 `doc_id`。

### 5.2 推荐对话模式

- **写内容**："帮我写/改 chap0X.tex 的第 X 节，参考 progress.md 里的实验结论"
- **画图**："给方法对比画一张 draw.io 图，用浅色系，右侧加一列评估指标"
- **同步**："把 chap05 上传到 Overleaf" / "把今天的改动 commit 了"
- **调图**："图太挤了，把第二行拉开" / "颜色太深，换浅色系"

**不要让 Claude 在你没明确要求时自动 push / upload**——这个约束已经写进 CLAUDE Code 默认行为里，但仍建议你每次明确指令。

### 5.3 新建一个 skill 的样板

```
skills/your-skill/
├── SKILL.md           # YAML frontmatter + Markdown 说明
└── references/        # 脚本、模板文件
```

`SKILL.md` 第一行必须是 YAML frontmatter，`description` 决定 Claude 何时加载它：

```markdown
---
name: your-skill
description: Use when the user wants to ...
---

# Your Skill

## Key paths
...

## Commands
...
```

---

## 6. 常见故障排查

| 症状 | 原因 | 解决 |
|---|---|---|
| `ols` 登录失败 / 401 | cookie 过期 | 重新跑 `make_olauth.py` |
| `ot-upload.py` 报 `Delete component does not match` | 服务端当前文档是 mojibake，但脚本没转码 | 脚本里 `cur.encode('latin-1').decode('utf-8')` 已处理，确认你用的是 `references/` 下那个版本 |
| Overleaf 编译报 `Unable to load picture` | 图片只在本地、没传到 Overleaf | Web UI 拖上去（REST 接口对我们不开放） |
| 本地 PDF 打不开（"无法打开此文件"） | `render.js` 的 `.pdf` 其实是 PNG | 用 `img2pdf` 重新转 |
| 图片在 PDF 里只占一小角 | draw.io 画布自带大量白边 | 用 `PIL + np` 检测 non-white 区域裁掉（见 3.5） |
| 中文字体不显示 / 变方框 | mxClient 渲染时字体缺失 | 系统安装 `fonts-noto-cjk`：`sudo apt install fonts-noto-cjk` |
| `render.js` 启动失败 | chromium 路径不对 | 改 `render.js` 顶部 `CHROMIUM` 常量，或装 `chromium-browser` |

---

## 7. 写作节奏建议

一章的典型迭代：

1. **粗纲**：告诉 Claude 章节主题和目标字数，让它先列一级/二级节标题
2. **填内容**：逐节让 Claude 写，每节写完本地打开看一遍，别一次生成全章
3. **画图**：遇到需要图示的概念（架构、流程、对比）就画，不要堆到最后
4. **同步**：每写完一节就 `ot-upload.py` 上传，在 Overleaf 上实际编译预览一下，避免 LaTeX 语法错误积压
5. **commit**：每天工作结束 commit 一次到 GitHub，包括 `.tex`、`figures/`、`drawio` 源文件

图和 PDF 一起进 git，才能 rollback；`drawio_generator.py` 脚本也进 git，未来想改图直接改脚本重新渲染，比改 `.drawio` XML 方便。
