"""
drawio_generator.py — 用 Python 程序化生成 draw.io XML 文件。

支持的元素：
  - 矩形、圆角矩形、菱形、圆形、平行四边形等基础形状
  - 带箭头的连线（直线/折线/曲线）
  - 文本标注、分组
  - 泳道（swimlane）
  - 预设样式主题

用法示例：
    from drawio_generator import DrawioDiagram, Style

    d = DrawioDiagram()
    n1 = d.add_box("开始", x=100, y=100)
    n2 = d.add_box("处理", x=300, y=100)
    d.add_arrow(n1, n2, label="下一步")
    d.save("/tmp/my_diagram.drawio")
"""

import xml.etree.ElementTree as ET
import uuid


# ── 预设样式字符串 ─────────────────────────────────────────────────────────────

class Style:
    BOX          = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
    BOX_GREEN    = "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
    BOX_YELLOW   = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
    BOX_RED      = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;"
    BOX_GRAY     = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;"
    BOX_DARK     = "rounded=1;whiteSpace=wrap;html=1;fillColor=#647687;strokeColor=#314354;fontColor=#ffffff;"
    BOX_PLAIN    = "whiteSpace=wrap;html=1;"
    DIAMOND      = "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
    CIRCLE       = "ellipse;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
    TERMINAL     = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;arcSize=50;"
    PROCESS      = "shape=process;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
    DATABASE     = "shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
    DOCUMENT_    = "shape=document;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
    CLOUD        = "shape=cloud;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
    SWIMLANE     = "swimlane;fontStyle=1;align=center;startSize=30;fillColor=#dae8fc;strokeColor=#6c8ebf;"
    ARROW        = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;"
    ARROW_H      = "edgeStyle=orthogonalEdgeStyle;rounded=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
    ARROW_SIMPLE = "endArrow=block;endFill=1;"
    ARROW_DASHED = "endArrow=block;endFill=1;dashed=1;"
    ARROW_CURVED = "edgeStyle=elbowEdgeStyle;elbow=vertical;rounded=1;endArrow=block;endFill=1;"
    TEXT         = "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];autosize=1;"


# ── 主类 ──────────────────────────────────────────────────────────────────────

class DrawioDiagram:
    """程序化构建 draw.io (.drawio) 文件。"""

    def __init__(self, name: str = "Diagram", width: int = 1200, height: int = 800):
        self.name   = name
        self.width  = width
        self.height = height
        self._cells: list[ET.Element] = []
        self._id    = 2          # 0 和 1 被 root 占用
        self._id_map: dict[str, str] = {}   # user_id → internal_id

    # ── 内部帮助 ─────────────────────────────────────────────────────────────

    def _next_id(self) -> str:
        i = str(self._id)
        self._id += 1
        return i

    def _cell(self, value: str, style: str, x: float, y: float,
              w: float, h: float, vertex: bool = True,
              uid: str | None = None) -> str:
        cid = self._next_id()
        cell = ET.Element("mxCell")
        cell.set("id", cid)
        cell.set("value", value)
        cell.set("style", style)
        cell.set("parent", "1")
        if vertex:
            cell.set("vertex", "1")
        geo = ET.SubElement(cell, "mxGeometry")
        geo.set("x", str(x)); geo.set("y", str(y))
        geo.set("width", str(w)); geo.set("height", str(h))
        geo.set("as", "geometry")
        self._cells.append(cell)
        if uid:
            self._id_map[uid] = cid
        return cid

    def _edge(self, src: str, tgt: str, label: str, style: str,
              src_exit: str | None = None, tgt_entry: str | None = None) -> str:
        cid = self._next_id()
        cell = ET.Element("mxCell")
        cell.set("id", cid)
        cell.set("value", label)
        cell.set("style", style)
        cell.set("edge", "1")
        cell.set("source", src)
        cell.set("target", tgt)
        cell.set("parent", "1")
        geo = ET.SubElement(cell, "mxGeometry")
        geo.set("relative", "1")
        geo.set("as", "geometry")
        self._cells.append(cell)
        return cid

    def _resolve(self, node_id) -> str:
        """将用户给的 id（字符串或数字）解析为内部 cell id。"""
        s = str(node_id)
        return self._id_map.get(s, s)

    # ── 公共 API — 形状 ───────────────────────────────────────────────────────

    def add_box(self, label: str, x: float = 100, y: float = 100,
                w: float = 160, h: float = 60, style: str = Style.BOX,
                uid: str | None = None) -> str:
        """添加矩形节点，返回内部 cell id。"""
        return self._cell(label, style, x, y, w, h, uid=uid)

    def add_diamond(self, label: str, x: float = 100, y: float = 100,
                    w: float = 120, h: float = 80, uid: str | None = None) -> str:
        """添加菱形（判断节点）。"""
        return self._cell(label, Style.DIAMOND, x, y, w, h, uid=uid)

    def add_circle(self, label: str, x: float = 100, y: float = 100,
                   w: float = 80, h: float = 80, style: str = Style.CIRCLE,
                   uid: str | None = None) -> str:
        """添加圆形。"""
        return self._cell(label, style, x, y, w, h, uid=uid)

    def add_terminal(self, label: str, x: float = 100, y: float = 100,
                     w: float = 120, h: float = 40, uid: str | None = None) -> str:
        """添加流程图起止端（圆角）。"""
        return self._cell(label, Style.TERMINAL, x, y, w, h, uid=uid)

    def add_database(self, label: str, x: float = 100, y: float = 100,
                     w: float = 120, h: float = 80, uid: str | None = None) -> str:
        """添加数据库圆柱体。"""
        return self._cell(label, Style.DATABASE, x, y, w, h, uid=uid)

    def add_cloud(self, label: str, x: float = 100, y: float = 100,
                  w: float = 160, h: float = 80, uid: str | None = None) -> str:
        """添加云形状。"""
        return self._cell(label, Style.CLOUD, x, y, w, h, uid=uid)

    def add_text(self, label: str, x: float = 100, y: float = 100,
                 w: float = 200, h: float = 40, uid: str | None = None) -> str:
        """添加纯文本标注。"""
        return self._cell(label, Style.TEXT, x, y, w, h, uid=uid)

    def add_swimlane(self, label: str, x: float = 100, y: float = 100,
                     w: float = 400, h: float = 200, uid: str | None = None) -> str:
        """添加泳道容器。"""
        return self._cell(label, Style.SWIMLANE, x, y, w, h, uid=uid)

    # ── 公共 API — 连线 ───────────────────────────────────────────────────────

    def add_arrow(self, src_id, tgt_id, label: str = "",
                  style: str = Style.ARROW, uid: str | None = None) -> str:
        """添加有向箭头。src_id/tgt_id 可以是 add_box 返回的 id。"""
        src = self._resolve(src_id)
        tgt = self._resolve(tgt_id)
        cid = self._next_id()
        cell = ET.Element("mxCell")
        cell.set("id", cid)
        cell.set("value", label)
        cell.set("style", style)
        cell.set("edge", "1")
        cell.set("source", src)
        cell.set("target", tgt)
        cell.set("parent", "1")
        geo = ET.SubElement(cell, "mxGeometry")
        geo.set("relative", "1")
        geo.set("as", "geometry")
        self._cells.append(cell)
        if uid:
            self._id_map[uid] = cid
        return cid

    def add_dashed_arrow(self, src_id, tgt_id, label: str = "") -> str:
        return self.add_arrow(src_id, tgt_id, label, Style.ARROW_DASHED)

    # ── 高阶构建器 ────────────────────────────────────────────────────────────

    def add_flowchart_row(self, labels: list[str], y: float = 100,
                          x_start: float = 100, gap: float = 60,
                          box_w: float = 160, box_h: float = 60,
                          style: str = Style.BOX) -> list[str]:
        """横向排列一排矩形并自动连线，返回 cell id 列表。"""
        ids = []
        x = x_start
        for lbl in labels:
            nid = self.add_box(lbl, x=x, y=y, w=box_w, h=box_h, style=style)
            ids.append(nid)
            x += box_w + gap
        for i in range(len(ids) - 1):
            self.add_arrow(ids[i], ids[i + 1])
        return ids

    def add_vertical_chain(self, labels: list[str], x: float = 100,
                           y_start: float = 100, gap: float = 40,
                           box_w: float = 160, box_h: float = 60,
                           style: str = Style.BOX) -> list[str]:
        """纵向排列一列矩形并自动连线，返回 cell id 列表。"""
        ids = []
        y = y_start
        for lbl in labels:
            nid = self.add_box(lbl, x=x, y=y, w=box_w, h=box_h, style=style)
            ids.append(nid)
            y += box_h + gap
        for i in range(len(ids) - 1):
            self.add_arrow(ids[i], ids[i + 1])
        return ids

    # ── 序列化 ───────────────────────────────────────────────────────────────

    def to_xml_string(self) -> str:
        """返回 draw.io XML 字符串（未压缩，可直接用编辑器打开）。"""
        mxfile = ET.Element("mxfile")
        mxfile.set("host", "Claude-Code")
        diagram = ET.SubElement(mxfile, "diagram")
        diagram.set("id", str(uuid.uuid4()))
        diagram.set("name", self.name)
        model = ET.SubElement(diagram, "mxGraphModel")
        model.set("dx", "1422"); model.set("dy", "762")
        model.set("grid", "1"); model.set("gridSize", "10")
        model.set("guides", "1"); model.set("tooltips", "1")
        model.set("connect", "1"); model.set("arrows", "1")
        model.set("fold", "1"); model.set("page", "1")
        model.set("pageScale", "1"); model.set("pageWidth", str(self.width))
        model.set("pageHeight", str(self.height))
        model.set("math", "0"); model.set("shadow", "0")
        root = ET.SubElement(model, "root")
        c0 = ET.SubElement(root, "mxCell"); c0.set("id", "0")
        c1 = ET.SubElement(root, "mxCell"); c1.set("id", "1"); c1.set("parent", "0")
        for cell in self._cells:
            root.append(cell)
        ET.indent(mxfile, space="  ")
        return ET.tostring(mxfile, encoding="unicode", xml_declaration=False)

    def save(self, path: str):
        """保存 .drawio 文件。"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_xml_string())
        print(f"[drawio] Saved: {path}")


# ── 便捷函数 ──────────────────────────────────────────────────────────────────

def make_flowchart(steps: list[str], title: str = "Flowchart") -> DrawioDiagram:
    """快速创建线性流程图。"""
    d = DrawioDiagram(title)
    ids = []
    x, y = 80, 80
    start = d.add_terminal("开始", x=x, y=y, w=120, h=40)
    ids.append(start)
    y += 80
    for step in steps:
        nid = d.add_box(step, x=x, y=y, w=180, h=60)
        ids.append(nid)
        y += 100
    end = d.add_terminal("结束", x=x, y=y, w=120, h=40)
    ids.append(end)
    for i in range(len(ids) - 1):
        d.add_arrow(ids[i], ids[i+1])
    return d


def make_pipeline(stages: list[dict], title: str = "Pipeline") -> DrawioDiagram:
    """
    快速创建水平流水线图。
    stages: [{"label": "...", "style": Style.BOX_BLUE, "sub": "副标题"}, ...]
    """
    d = DrawioDiagram(title, width=1400, height=400)
    x, y = 60, 160
    gap = 50
    box_w, box_h = 160, 80
    ids = []
    for s in stages:
        lbl = s.get("label", "")
        sty = s.get("style", Style.BOX)
        sub = s.get("sub", "")
        if sub:
            lbl = f"<b>{lbl}</b><br/><font style='font-size:11px;color:#555'>{sub}</font>"
        nid = d.add_box(lbl, x=x, y=y, w=box_w, h=box_h, style=sty)
        ids.append(nid)
        x += box_w + gap
    for i in range(len(ids) - 1):
        d.add_arrow(ids[i], ids[i+1])
    return d
