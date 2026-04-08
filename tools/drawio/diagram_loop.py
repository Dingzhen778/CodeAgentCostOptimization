"""
diagram_loop.py — draw.io 图表生成与人工反馈改进循环。

流程：
  1. Claude 生成 DrawioDiagram Python 代码
  2. 执行代码 → 生成 .drawio 文件
  3. render.js 渲染 → PNG
  4. 将 PNG 路径返回给 Claude，Claude 读取图片确认效果
  5. 用户看图给反馈 → Claude 修改代码 → 回到 2

命令行快速使用：
  python3 diagram_loop.py build <spec_file.py> <output_prefix>
  python3 diagram_loop.py render <input.drawio> <output.png>
  python3 diagram_loop.py demo

内嵌 API 使用（由 Claude Code 调用）：
  from tools.drawio.diagram_loop import DiagramSession
  session = DiagramSession(work_dir="/tmp/diagrams")
  png = session.run_code(python_code_str)     # 生成并渲染，返回 PNG 路径
  png = session.render_drawio(drawio_path)    # 仅渲染
"""

import os
import sys
import subprocess
import textwrap
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────────────────────────
TOOLS_DIR   = Path(__file__).parent
RENDER_JS   = TOOLS_DIR / "render.js"
PROJECT_ROOT = TOOLS_DIR.parent.parent


# ── DiagramSession ────────────────────────────────────────────────────────────

class DiagramSession:
    """管理一次图表生成-反馈迭代会话。"""

    def __init__(self, work_dir: str = "/tmp/diagrams", name: str = "diagram"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.name    = name
        self.version = 0
        self.history: list[dict] = []   # [{code, drawio, png, feedback}]

    # ── 核心方法 ──────────────────────────────────────────────────────────────

    def run_code(self, code: str, scale: float = 1.5) -> str:
        """
        执行 Python 代码（必须调用 d.save(path) 保存 .drawio 文件），
        然后渲染为 PNG，返回 PNG 路径。

        code 示例:
            from tools.drawio.drawio_generator import DrawioDiagram, Style
            d = DrawioDiagram("My Diagram")
            n1 = d.add_box("A", x=100, y=100)
            n2 = d.add_box("B", x=300, y=100)
            d.add_arrow(n1, n2)
            d.save(OUTPUT_PATH)   # OUTPUT_PATH 由 DiagramSession 注入

        注意: 代码中用 OUTPUT_PATH 作为保存路径占位符，
              DiagramSession 会自动替换为实际路径。
        """
        self.version += 1
        vname    = f"{self.name}_v{self.version}"
        drawio_p = self.work_dir / f"{vname}.drawio"
        png_p    = self.work_dir / f"{vname}.png"

        # 注入 sys.path 和 OUTPUT_PATH
        sys_path_inject = textwrap.dedent(f"""\
            import sys
            sys.path.insert(0, r'{PROJECT_ROOT}')
            OUTPUT_PATH = r'{drawio_p}'
        """)
        full_code = sys_path_inject + "\n" + code

        # 执行代码
        result = subprocess.run(
            [sys.executable, "-c", full_code],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Diagram code execution failed:\n"
                f"STDOUT: {result.stdout}\n"
                f"STDERR: {result.stderr}"
            )

        if not drawio_p.exists():
            raise FileNotFoundError(
                f"Code ran but did not create {drawio_p}. "
                "Make sure the code calls d.save(OUTPUT_PATH)."
            )

        # 渲染 PNG
        png_path = self.render_drawio(str(drawio_p), str(png_p), scale)

        self.history.append({
            "version": self.version,
            "code":    code,
            "drawio":  str(drawio_p),
            "png":     png_path,
            "feedback": None,
        })
        return png_path

    def render_drawio(self, drawio_path: str, output_path: str | None = None,
                      scale: float = 1.5) -> str:
        """直接渲染 .drawio → PNG，返回 PNG 路径。"""
        if output_path is None:
            output_path = drawio_path.replace(".drawio", ".png")
        result = subprocess.run(
            ["node", str(RENDER_JS), drawio_path, output_path, str(scale)],
            capture_output=True, text=True, cwd=str(TOOLS_DIR)
        )
        if result.returncode != 0:
            raise RuntimeError(f"Render failed:\n{result.stderr}\n{result.stdout}")
        print(f"[render] {result.stdout.strip()}")
        return output_path

    def record_feedback(self, feedback: str):
        """记录用户对最新版本的反馈。"""
        if self.history:
            self.history[-1]["feedback"] = feedback

    def latest_png(self) -> str | None:
        return self.history[-1]["png"] if self.history else None

    def latest_drawio(self) -> str | None:
        return self.history[-1]["drawio"] if self.history else None

    def summary(self) -> str:
        lines = [f"Session: {self.name}, {len(self.history)} version(s)"]
        for h in self.history:
            fb = h["feedback"] or "(no feedback yet)"
            lines.append(f"  v{h['version']}: {h['png']}  feedback: {fb}")
        return "\n".join(lines)


# ── Demo diagrams ─────────────────────────────────────────────────────────────

DEMO_CODE_PIPELINE = """
from tools.drawio.drawio_generator import DrawioDiagram, Style, make_pipeline

stages = [
    {"label": "Issue Input",    "style": Style.BOX_GRAY,   "sub": "GitHub issue"},
    {"label": "Repo Clone",     "style": Style.BOX,        "sub": "仓库环境"},
    {"label": "Code Search",    "style": Style.BOX,        "sub": "BM25 / 嵌入"},
    {"label": "Context Build",  "style": Style.BOX_YELLOW, "sub": "上下文组织"},
    {"label": "Patch Gen",      "style": Style.BOX_GREEN,  "sub": "LLM 生成"},
    {"label": "Test & Verify",  "style": Style.BOX_GREEN,  "sub": "测试验证"},
    {"label": "Submit / Fail",  "style": Style.BOX_RED,    "sub": "结果输出"},
]
d = make_pipeline(stages, "Code Repair Agent Pipeline")
d.save(OUTPUT_PATH)
"""

DEMO_CODE_FLOWCHART = """
from tools.drawio.drawio_generator import DrawioDiagram, Style

d = DrawioDiagram("代码修复智能体执行流程", width=1000, height=900)

# 节点定义（纵向布局）
x, step = 180, 100
s   = d.add_terminal("开始",              x=x, y=40,  w=140, h=40)
n1  = d.add_box("接收 GitHub Issue",      x=x, y=130, w=200, h=60, style=Style.BOX_GRAY)
n2  = d.add_box("构建仓库环境",            x=x, y=240, w=200, h=60)
n3  = d.add_box("代码搜索定位",            x=x, y=350, w=200, h=60)
n4  = d.add_box("组织上下文",              x=x, y=460, w=200, h=60, style=Style.BOX_YELLOW)
n5  = d.add_box("LLM 生成补丁",           x=x, y=570, w=200, h=60, style=Style.BOX_GREEN)
d6  = d.add_diamond("测试通过?",           x=x, y=690, w=200, h=70)
n7  = d.add_box("提交补丁",               x=x, y=830, w=200, h=60, style=Style.BOX_GREEN)
n8  = d.add_box("重试 / 调整",            x=440, y=690, w=180, h=60, style=Style.BOX_RED)
e   = d.add_terminal("结束",              x=x+30, y=950, w=140, h=40)

# 连线
for src, tgt in [(s,n1),(n1,n2),(n2,n3),(n3,n4),(n4,n5),(n5,d6),(n7,e)]:
    d.add_arrow(src, tgt)
d.add_arrow(d6, n7,  label="是")
d.add_arrow(d6, n8,  label="否")
d.add_arrow(n8, n3,  label="返回搜索")

d.save(OUTPUT_PATH)
"""

DEMO_CODE_COST_ARCH = """
from tools.drawio.drawio_generator import DrawioDiagram, Style

d = DrawioDiagram("代码修复智能体推理成本来源分析", width=1400, height=700)

# 阶段标题行
phases = [
    ("问题理解", 60,  100, Style.BOX_GRAY),
    ("代码定位", 260, 100, Style.BOX),
    ("上下文组织", 460, 100, Style.BOX_YELLOW),
    ("补丁生成", 660, 100, Style.BOX_GREEN),
    ("验证重试", 860, 100, Style.BOX_RED),
]
phase_ids = []
for lbl, x, y, sty in phases:
    nid = d.add_box(lbl, x=x, y=y, w=160, h=50, style=sty)
    phase_ids.append(nid)
# 连接阶段
for i in range(len(phase_ids)-1):
    d.add_arrow(phase_ids[i], phase_ids[i+1])

# 每个阶段的成本来源标注
cost_items = [
    (60,  220, "Issue tokens\\n+ 系统 prompt"),
    (260, 220, "搜索结果\\n+ 文件内容"),
    (460, 220, "多文件拼接\\n+ 跨文件上下文"),
    (660, 220, "模型输出\\nchain-of-thought"),
    (860, 220, "测试输出\\n+ 重试历史"),
]
cost_ids = []
for x, y, lbl in cost_items:
    nid = d.add_box(lbl, x=x, y=y, w=160, h=70, style=Style.BOX_GRAY)
    cost_ids.append(nid)

# 向下虚线标注
for pi, ci in zip(phase_ids, cost_ids):
    d.add_dashed_arrow(pi, ci, label="产生")

# 累计成本说明
total = d.add_box(
    "总推理成本 = Σ (每轮输入 tokens + 输出 tokens)",
    x=180, y=370, w=700, h=60,
    style="rounded=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=14;fontStyle=1;"
)

d.add_text("← 过程性成本，随轮次累积增长 →", x=200, y=450, w=650, h=40)
d.save(OUTPUT_PATH)
"""


# ── CLI entry point ───────────────────────────────────────────────────────────

def cmd_demo(args):
    """运行内置 demo 并保存 PNG。"""
    demos = {
        "pipeline":  (DEMO_CODE_PIPELINE,   "/tmp/demo_pipeline.png"),
        "flowchart": (DEMO_CODE_FLOWCHART,   "/tmp/demo_flowchart.png"),
        "cost":      (DEMO_CODE_COST_ARCH,   "/tmp/demo_cost.png"),
    }
    name = args[0] if args else "pipeline"
    if name not in demos:
        print(f"Available demos: {list(demos.keys())}")
        return
    code, png = demos[name]
    session = DiagramSession(work_dir="/tmp/diagrams", name=name)
    result  = session.run_code(code)
    print(f"Demo '{name}' rendered → {result}")


def cmd_render(args):
    """render <input.drawio> <output.png>"""
    if len(args) < 2:
        print("Usage: render <input.drawio> <output.png>"); return
    session = DiagramSession()
    session.render_drawio(args[0], args[1])


def cmd_build(args):
    """build <spec.py> <output_prefix>"""
    if len(args) < 2:
        print("Usage: build <spec.py> <prefix>"); return
    code = Path(args[0]).read_text()
    session = DiagramSession(work_dir=str(Path(args[1]).parent), name=Path(args[1]).name)
    png = session.run_code(code)
    print(f"Built → {png}")


if __name__ == "__main__":
    cmds = {"demo": cmd_demo, "render": cmd_render, "build": cmd_build}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print("Usage: python3 diagram_loop.py [demo|render|build] [args...]")
        print("       python3 diagram_loop.py demo [pipeline|flowchart|cost]")
    else:
        cmds[sys.argv[1]](sys.argv[2:])
