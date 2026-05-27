"""
SJB PK 功能模块（重设计版）
"""

from __future__ import annotations

import random

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

MOVES = ("石头", "剪刀", "布")
MOVE_ICON = {"石头": "✊", "剪刀": "✌️", "布": "🖐️"}
MOVE_BEATS = {"石头": "剪刀", "剪刀": "布", "布": "石头"}
DIFFICULTIES: list[tuple[str, int, str]] = [
    ("Easy",   1, "#4CAF50"),
    ("Normal", 3, "#2196F3"),
    ("Hard",   6, "#FF5722"),
    ("mmy",    5, "#9C27B0"),
]

_RESULT_COLORS: dict[str, tuple[str, str]] = {
    "win":  ("#E8F5E9", "#2E7D32"),
    "lose": ("#FFEBEE", "#C62828"),
    "draw": ("#FFF8E1", "#F57F17"),
    "idle": ("#F0F7F4", "#4A9970"),
}


def _judge(a: str, b: str) -> int:
    if a == b:
        return 0
    return 1 if MOVE_BEATS[a] == b else -1


def _random_move() -> str:
    return random.choice(MOVES)


def _counter_move(player: str) -> str:
    return next(m for m, beaten in MOVE_BEATS.items() if beaten == player)


def _shadow(radius: int = 16, alpha: int = 28) -> QGraphicsDropShadowEffect:
    e = QGraphicsDropShadowEffect()
    e.setBlurRadius(radius)
    e.setColor(QColor(0, 0, 0, alpha))
    e.setOffset(0, 3)
    return e


def _mk_lbl(text: str, style: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(style)
    return lbl


def _mk_pick_lbl(bg: str, bd: str) -> QLabel:
    lbl = QLabel("？")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setFixedSize(60, 60)
    lbl.setStyleSheet(
        f"font-size:32px; background:{bg}; border:2px dashed {bd}; border-radius:12px;"
    )
    return lbl


# ─────────────────────────────────────────────────────────────────────────────
#  出拳大按钮
# ─────────────────────────────────────────────────────────────────────────────
_MOVE_THEMES: dict[str, dict[str, str]] = {
    "石头": dict(bg="#FFF3E0", fg="#E65100", border="#FFCC80",
                 hover="#FF8F00", pressed="#E65100"),
    "剪刀": dict(bg="#E3F2FD", fg="#1565C0", border="#90CAF9",
                 hover="#1E88E5", pressed="#1565C0"),
    "布":   dict(bg="#F3E5F5", fg="#6A1B9A", border="#CE93D8",
                 hover="#8E24AA", pressed="#6A1B9A"),
}

_MOVE_BTN_QSS = (
    "QPushButton {{"
    "background:{bg}; color:{fg};"
    "border:2px solid {border}; border-radius:12px;"
    "font-size:13px; font-weight:bold; padding:0;"
    "}}"
    "QPushButton:hover {{ background:{hover}; border-color:{hover}; color:white; }}"
    "QPushButton:pressed {{ background:{pressed}; }}"
)


class MoveButton(QPushButton):
    def __init__(self, move: str, icon_size: int = 28, parent=None):
        super().__init__(parent)
        t = _MOVE_THEMES[move]
        self.setStyleSheet(_MOVE_BTN_QSS.format(**t))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(icon_size + 30)
        self.setGraphicsEffect(_shadow(10, 18))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(0)

        ico = QLabel(MOVE_ICON[move])
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet(
            f"font-size:{icon_size}px; background:transparent; border:none;"
        )
        ico.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        txt = QLabel(move)
        txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        txt.setStyleSheet(
            f"font-size:11px; font-weight:bold; color:{t['fg']};"
            "background:transparent; border:none;"
        )
        txt.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        lay.addWidget(ico)
        lay.addWidget(txt)


# ─────────────────────────────────────────────────────────────────────────────
#  战果横幅
# ─────────────────────────────────────────────────────────────────────────────
class ResultBanner(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(38)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 4, 14, 4)
        self._lbl = QLabel("")
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl.setStyleSheet(
            "font-size:14px; font-weight:bold; background:transparent; border:none;"
        )
        lay.addWidget(self._lbl)
        self.set_state("idle", "")

    def set_state(self, state: str, detail: str = "") -> None:
        bg, fg = _RESULT_COLORS.get(state, _RESULT_COLORS["idle"])
        prefix = {"win": "🎉 ", "lose": "💔 ", "draw": "🤝 ", "idle": ""}.get(state, "")
        self._lbl.setText(f"{prefix}{detail}")
        self._lbl.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{fg};"
            "background:transparent; border:none;"
        )
        self.setStyleSheet(
            f"QFrame{{background:{bg}; border:2px solid {fg}44; border-radius:10px;}}"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  心型进度条
# ─────────────────────────────────────────────────────────────────────────────
class HeartBar(QWidget):
    def __init__(self, total: int = 1, color: str = "#E53935", parent=None):
        super().__init__(parent)
        self._labels: list[QLabel] = []
        self._color = color
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(4)
        self._lay.addStretch()
        self.reset(total, color)

    def reset(self, total: int, color: str = "#E53935") -> None:
        self._color = color
        while self._lay.count() > 1:
            item = self._lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._labels = []
        for _ in range(total):
            lbl = QLabel("♡")
            lbl.setStyleSheet("font-size:20px; color:#DDD;")
            self._labels.append(lbl)
            self._lay.insertWidget(self._lay.count() - 1, lbl)

    def set_filled(self, n: int) -> None:
        for i, lbl in enumerate(self._labels):
            if i < n:
                lbl.setText("♥")
                lbl.setStyleSheet(f"font-size:20px; color:{self._color};")
            else:
                lbl.setText("♡")
                lbl.setStyleSheet("font-size:20px; color:#DDD;")


# ─────────────────────────────────────────────────────────────────────────────
#  模式选择页
# ─────────────────────────────────────────────────────────────────────────────
class ModeSelectPage(QWidget):
    mode_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 0, 40, 20)
        root.setSpacing(0)
        root.addStretch(2)

        emoji_lbl = QLabel("✊  ✌️  🖐️")
        emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_lbl.setStyleSheet("font-size:46px; letter-spacing:10px;")

        name_lbl = QLabel("石头  剪刀  布")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(
            "font-size:24px; font-weight:bold; color:#1A6B45; letter-spacing:6px;"
        )
        sub_lbl = QLabel("选择对战模式开始游戏")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("font-size:12px; color:#9AB9A8;")

        root.addWidget(emoji_lbl)
        root.addSpacing(6)
        root.addWidget(name_lbl)
        root.addSpacing(4)
        root.addWidget(sub_lbl)
        root.addStretch(1)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(20)
        cards_row.addStretch()
        cards_row.addWidget(self._make_card(
            "👥", "PVP", "双人对战", "红方 vs 蓝方\n出拳结算 · 累计比分",
            "#DD4A4A", "pvp",
        ))
        cards_row.addWidget(self._make_card(
            "🤖", "PVE", "挑战电脑", "四种难度\nEasy · Normal · Hard · mmy 😈",
            "#3D7FCC", "pve",
        ))
        cards_row.addStretch()

        root.addLayout(cards_row)
        root.addStretch(2)

    def _make_card(self, icon: str, tag: str, title: str,
                   desc: str, color: str, mode: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(240, 180)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(
            "QFrame {"
            "background: white;"
            "border: 2px solid #E0EDE6;"
            "border-radius: 18px;"
            "}"
            f"QFrame:hover {{ border: 2px solid {color}; background: #FAFFFE; }}"
        )
        card.setGraphicsEffect(_shadow(18, 28))

        lay = QVBoxLayout(card)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setContentsMargins(16, 18, 16, 18)
        lay.setSpacing(5)

        styles = [
            (icon,  "font-size:38px; background:transparent; border:none;"),
            (tag,   f"font-size:20px; font-weight:900; color:{color}; background:transparent; border:none; letter-spacing:4px;"),
            (title, "font-size:13px; font-weight:bold; color:#3A5A4A; background:transparent; border:none;"),
            (desc,  "font-size:11px; color:#9AB9A8; background:transparent; border:none;"),
        ]
        for text, style in styles:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(style)
            lay.addWidget(lbl)

        card.mousePressEvent = lambda e, m=mode: (
            self.mode_selected.emit(m)
            if e.button() == Qt.MouseButton.LeftButton else None
        )
        return card


# ─────────────────────────────────────────────────────────────────────────────
#  PVP 出拳横排
# ─────────────────────────────────────────────────────────────────────────────
class _FighterRow(QFrame):
    move_selected = Signal(str)

    def __init__(self, label: str, color: str, reverse: bool = False, parent=None):
        super().__init__(parent)
        self._color = color
        self.setStyleSheet(
            f"QFrame {{ background:white; border:2px solid {color}44; border-radius:14px; }}"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(10)

        name = QLabel(label)
        name.setFixedWidth(64)
        name.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{color};"
            "background:transparent; border:none;"
        )

        self._picked = QLabel("？")
        self._picked.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._picked.setFixedSize(52, 52)
        self._picked.setStyleSheet(
            f"font-size:28px; background:{color}11;"
            f"border:2px dashed {color}66; border-radius:10px;"
        )

        btns_lay = QHBoxLayout()
        btns_lay.setSpacing(6)
        for move in MOVES:
            b = MoveButton(move, icon_size=20)
            b.setMinimumHeight(38)
            b.clicked.connect(lambda _=False, m=move: self.move_selected.emit(m))
            btns_lay.addWidget(b)

        rand = QPushButton("🎲")
        rand.setFixedSize(38, 38)
        rand.setCursor(Qt.CursorShape.PointingHandCursor)
        rand.setToolTip("随机")
        rand.setStyleSheet(
            "QPushButton { background:#F0F7F4; border:2px solid #C8E6D5;"
            "border-radius:10px; font-size:16px; }"
            "QPushButton:hover { background:#C8E6D5; }"
        )
        rand.clicked.connect(lambda: self.move_selected.emit(_random_move()))

        if reverse:
            lay.addLayout(btns_lay)
            lay.addWidget(rand)
            lay.addStretch()
            lay.addWidget(self._picked)
            lay.addWidget(name)
        else:
            lay.addWidget(name)
            lay.addWidget(self._picked)
            lay.addStretch()
            lay.addLayout(btns_lay)
            lay.addWidget(rand)

    def set_move(self, move: str | None) -> None:
        if move:
            self._picked.setText(MOVE_ICON[move])
            self._picked.setStyleSheet(
                f"font-size:26px; background:{self._color}22;"
                f"border:2px solid {self._color}; border-radius:10px;"
            )
        else:
            self._picked.setText("？")
            self._picked.setStyleSheet(
                f"font-size:28px; background:{self._color}11;"
                f"border:2px dashed {self._color}66; border-radius:10px;"
            )


# ─────────────────────────────────────────────────────────────────────────────
#  PVP 页面
# ─────────────────────────────────────────────────────────────────────────────
class PvpPage(QWidget):
    back_to_mode = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._red_move: str | None = None
        self._blue_move: str | None = None
        self._red_score = 0
        self._blue_score = 0
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 8, 14, 10)
        root.setSpacing(9)

        # 顶栏
        top = QHBoxLayout()
        back = QPushButton("← 返回")
        back.setObjectName("backButton")
        back.setFixedWidth(82)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(self.back_to_mode.emit)
        tag = QLabel("👥  PVP 双人对战")
        tag.setStyleSheet("font-size:15px; font-weight:bold; color:#1A6B45;")
        top.addWidget(back)
        top.addSpacing(10)
        top.addWidget(tag)
        top.addStretch()

        # 比分板
        sb = QFrame()
        sb.setFixedHeight(76)
        sb.setStyleSheet(
            "QFrame {"
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #FFF5F5, stop:0.5 #FAFFFE, stop:1 #F0F5FF);"
            "border: 2px solid #E0E8F4;"
            "border-radius: 14px;"
            "}"
        )
        sb.setGraphicsEffect(_shadow(14, 20))
        sb_lay = QHBoxLayout(sb)
        sb_lay.setContentsMargins(20, 6, 20, 6)

        self._red_score_lbl = QLabel("0")
        self._red_score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._red_score_lbl.setStyleSheet(
            "font-size:38px; font-weight:900; color:#DD4A4A;"
            "font-family:Consolas; background:transparent; border:none;"
        )
        red_name = QLabel("🔴 红方")
        red_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        red_name.setStyleSheet(
            "font-size:11px; color:#DD4A4A; font-weight:bold;"
            "background:transparent; border:none;"
        )

        self._blue_score_lbl = QLabel("0")
        self._blue_score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._blue_score_lbl.setStyleSheet(
            "font-size:38px; font-weight:900; color:#3D7FCC;"
            "font-family:Consolas; background:transparent; border:none;"
        )
        blue_name = QLabel("蓝方 🔵")
        blue_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blue_name.setStyleSheet(
            "font-size:11px; color:#3D7FCC; font-weight:bold;"
            "background:transparent; border:none;"
        )

        vs = QLabel("VS")
        vs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vs.setStyleSheet(
            "font-size:20px; font-weight:900; color:#C4D8C8;"
            "background:transparent; border:none;"
        )

        red_col = QVBoxLayout()
        red_col.setSpacing(0)
        red_col.addWidget(self._red_score_lbl)
        red_col.addWidget(red_name)

        blue_col = QVBoxLayout()
        blue_col.setSpacing(0)
        blue_col.addWidget(self._blue_score_lbl)
        blue_col.addWidget(blue_name)

        sb_lay.addLayout(red_col)
        sb_lay.addStretch()
        sb_lay.addWidget(vs)
        sb_lay.addStretch()
        sb_lay.addLayout(blue_col)

        # 战果横幅
        self._banner = ResultBanner()

        # 出拳行
        self._red_row = _FighterRow("🔴 红方", "#DD4A4A", reverse=False)
        self._blue_row = _FighterRow("🔵 蓝方", "#3D7FCC", reverse=True)
        self._red_row.move_selected.connect(self._on_red)
        self._blue_row.move_selected.connect(self._on_blue)

        # 底部按钮
        btm = QHBoxLayout()
        btm.addStretch()

        clr_btn = QPushButton("↩ 清空本回合")
        clr_btn.setStyleSheet(
            "QPushButton { background:#F5FFFB; color:#3EC78C;"
            "border:2px solid #3EC78C; border-radius:9px;"
            "padding:5px 14px; font-size:12px; font-weight:bold; }"
            "QPushButton:hover { background:#3EC78C; color:white; }"
        )
        clr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clr_btn.clicked.connect(self._clear_round)

        rst_btn = QPushButton("🗑 重置比分")
        rst_btn.setStyleSheet(
            "QPushButton { background:#FFF5F5; color:#DD4A4A;"
            "border:2px solid #DD4A4A; border-radius:9px;"
            "padding:5px 14px; font-size:12px; font-weight:bold; }"
            "QPushButton:hover { background:#DD4A4A; color:white; }"
        )
        rst_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rst_btn.clicked.connect(self._reset_scores)

        btm.addWidget(clr_btn)
        btm.addSpacing(8)
        btm.addWidget(rst_btn)

        root.addLayout(top)
        root.addWidget(sb)
        root.addWidget(self._banner)
        root.addWidget(self._red_row)
        root.addWidget(self._blue_row)
        root.addStretch()
        root.addLayout(btm)

    def _on_red(self, move: str) -> None:
        self._red_move = move
        self._red_row.set_move(move)
        self._try_settle()

    def _on_blue(self, move: str) -> None:
        self._blue_move = move
        self._blue_row.set_move(move)
        self._try_settle()

    def _try_settle(self) -> None:
        if not (self._red_move and self._blue_move):
            if self._red_move:
                self._banner.set_state("idle", "红方已出拳，等待蓝方…")
            elif self._blue_move:
                self._banner.set_state("idle", "蓝方已出拳，等待红方…")
            return

        r = _judge(self._red_move, self._blue_move)
        ri, bi = MOVE_ICON[self._red_move], MOVE_ICON[self._blue_move]
        if r == 1:
            self._red_score += 1
            self._banner.set_state("win", f"{ri} 胜 {bi}  ·  红方得分")
        elif r == -1:
            self._blue_score += 1
            self._banner.set_state("lose", f"{bi} 胜 {ri}  ·  蓝方得分")
        else:
            self._banner.set_state("draw", f"{ri} vs {bi}  ·  平局不得分")

        self._red_score_lbl.setText(str(self._red_score))
        self._blue_score_lbl.setText(str(self._blue_score))
        QTimer.singleShot(900, lambda: self._clear_round(keep_tip=True))

    def _clear_round(self, keep_tip: bool = False) -> None:
        self._red_move = None
        self._blue_move = None
        self._red_row.set_move(None)
        self._blue_row.set_move(None)
        if not keep_tip:
            self._banner.set_state("idle", "双方出拳，分出胜负")

    def _reset_scores(self) -> None:
        self._red_score = 0
        self._blue_score = 0
        self._red_score_lbl.setText("0")
        self._blue_score_lbl.setText("0")
        self._clear_round()
        self._banner.set_state("idle", "比分已重置，新的对局开始！")


# ─────────────────────────────────────────────────────────────────────────────
#  PVE 页面
# ─────────────────────────────────────────────────────────────────────────────
class PvePage(QWidget):
    back_to_mode = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._wins = 0
        self._goal = 1
        self._mode = "Easy"
        self._mode_color = "#4CAF50"
        self._finished = False
        self._diff_btns: list[QPushButton] = []
        self._setup_ui()
        self._apply_mode(0)

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 8, 14, 10)
        root.setSpacing(9)

        # 顶栏
        top = QHBoxLayout()
        back = QPushButton("← 返回")
        back.setObjectName("backButton")
        back.setFixedWidth(82)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(self.back_to_mode.emit)
        tag = QLabel("🤖  PVE 挑战电脑")
        tag.setStyleSheet("font-size:15px; font-weight:bold; color:#1A6B45;")
        top.addWidget(back)
        top.addSpacing(10)
        top.addWidget(tag)
        top.addStretch()

        # 难度选择行
        diff_row = QHBoxLayout()
        diff_row.setSpacing(8)
        diff_row.addWidget(
            _mk_lbl("难度：", "font-size:12px; color:#4A9970; font-weight:bold;")
        )
        for i, (name, _need, _color) in enumerate(DIFFICULTIES):
            caption = "mmy 😈" if name == "mmy" else name
            b = QPushButton(caption)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFixedHeight(30)
            b.clicked.connect(lambda _=False, idx=i: self._apply_mode(idx))
            self._diff_btns.append(b)
            diff_row.addWidget(b)
        diff_row.addStretch()

        rst_btn = QPushButton("↩ 重新挑战")
        rst_btn.setStyleSheet(
            "QPushButton { background:#F0FFF8; color:#3EC78C;"
            "border:2px solid #3EC78C; border-radius:8px;"
            "padding:4px 12px; font-size:12px; font-weight:bold; }"
            "QPushButton:hover { background:#3EC78C; color:white; }"
        )
        rst_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rst_btn.clicked.connect(lambda: self._apply_mode(
            next(i for i, (n, _g, _c) in enumerate(DIFFICULTIES) if n == self._mode)
        ))
        diff_row.addWidget(rst_btn)

        # 进度卡片
        prog_card = QFrame()
        prog_card.setFixedHeight(52)
        prog_card.setStyleSheet(
            "QFrame { background:white; border:2px solid #E0EDE6; border-radius:12px; }"
        )
        pc_lay = QHBoxLayout(prog_card)
        pc_lay.setContentsMargins(14, 4, 14, 4)
        pc_lay.addWidget(
            _mk_lbl("进度", "font-size:11px; color:#9AB9A8; font-weight:bold;")
        )
        pc_lay.addSpacing(10)
        self._heart_bar = HeartBar(1)
        pc_lay.addWidget(self._heart_bar, 1)
        pc_lay.addSpacing(8)
        self._prog_text = QLabel("0 / 1")
        self._prog_text.setStyleSheet(
            "font-size:13px; font-weight:bold; color:#4A9970; font-family:Consolas;"
        )
        pc_lay.addWidget(self._prog_text)

        # 对战区
        arena = QFrame()
        arena.setFixedHeight(120)
        arena.setStyleSheet(
            "QFrame {"
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #F2FBF7, stop:1 #FAFFFE);"
            "border: 2px solid #D9EDE5;"
            "border-radius: 16px;"
            "}"
        )
        arena.setGraphicsEffect(_shadow(14, 18))
        ar = QGridLayout(arena)
        ar.setContentsMargins(14, 8, 14, 8)

        self._player_icon = _mk_pick_lbl("#F0FFF8", "#C8E6D5")
        self._ai_icon = _mk_pick_lbl("#F0F5FF", "#B0C8E8")

        for col, lbl_text, widget in [
            (0, "你",   self._player_icon),
            (2, "电脑", self._ai_icon),
        ]:
            t = _mk_lbl(lbl_text, "font-size:11px; color:#9AB9A8; font-weight:bold;")
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ar.addWidget(t, 0, col, Qt.AlignmentFlag.AlignHCenter)
            ar.addWidget(widget, 1, col, Qt.AlignmentFlag.AlignHCenter)

        vs = _mk_lbl("VS", "font-size:18px; font-weight:900; color:#C4D8C8;")
        vs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ar.addWidget(vs, 0, 1, 2, 1, Qt.AlignmentFlag.AlignCenter)
        ar.setColumnStretch(0, 1)
        ar.setColumnStretch(1, 0)
        ar.setColumnStretch(2, 1)

        # 战果横幅
        self._banner = ResultBanner()

        # 出拳按钮
        pick_row = QHBoxLayout()
        pick_row.setSpacing(10)
        for move in MOVES:
            b = MoveButton(move, icon_size=28)
            b.setMinimumHeight(62)
            b.clicked.connect(lambda _=False, m=move: self._play_round(m))
            pick_row.addWidget(b)

        rand_btn = QPushButton("🎲\n随机")
        rand_btn.setFixedWidth(56)
        rand_btn.setMinimumHeight(62)
        rand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rand_btn.setStyleSheet(
            "QPushButton { background:#F0F7F4; color:#4A9970;"
            "border:2px solid #C8E6D5; border-radius:12px;"
            "font-size:13px; font-weight:bold; }"
            "QPushButton:hover { background:#3EC78C; color:white; border-color:#3EC78C; }"
        )
        rand_btn.clicked.connect(lambda: self._play_round(_random_move()))
        pick_row.addWidget(rand_btn)

        root.addLayout(top)
        root.addLayout(diff_row)
        root.addWidget(prog_card)
        root.addWidget(arena)
        root.addWidget(self._banner)
        root.addLayout(pick_row)
        root.addStretch()

    def _apply_mode(self, idx: int) -> None:
        name, goal, color = DIFFICULTIES[idx]
        self._mode = name
        self._goal = goal
        self._mode_color = color
        self._wins = 0
        self._finished = False

        for i, btn in enumerate(self._diff_btns):
            _, _, c = DIFFICULTIES[i]
            if i == idx:
                btn.setStyleSheet(
                    f"QPushButton {{ background:{c}; color:white;"
                    f"border:2px solid {c}; border-radius:8px;"
                    "padding:4px 12px; font-size:12px; font-weight:bold; }"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton { background:white; color:#6A8F7A;"
                    "border:2px solid #D0E8D8; border-radius:8px;"
                    "padding:4px 12px; font-size:12px; font-weight:bold; }"
                    f"QPushButton:hover {{ background:{c}; color:white; border-color:{c}; }}"
                )

        self._heart_bar.reset(goal, color)
        self._prog_text.setText(f"0 / {goal}")
        self._reset_arena()
        tips = {
            "Easy":   "赢 1 局即胜利！",
            "Normal": "连赢 3 局挑战成功！",
            "Hard":   "连赢 6 局，硬核挑战！",
            "mmy":    "😈",
        }
        self._banner.set_state("idle", tips.get(name, "出拳开始挑战"))

    def _reset_arena(self) -> None:
        self._player_icon.setText("？")
        self._player_icon.setStyleSheet(
            "font-size:32px; background:#F0FFF8; border:2px dashed #C8E6D5; border-radius:12px;"
        )
        self._ai_icon.setText("？")
        self._ai_icon.setStyleSheet(
            "font-size:32px; background:#F0F5FF; border:2px dashed #B0C8E8; border-radius:12px;"
        )

    def _refresh_progress(self) -> None:
        self._heart_bar.set_filled(self._wins)
        self._prog_text.setText(f"{self._wins} / {self._goal}")

    def _play_round(self, player_move: str) -> None:
        if self._finished:
            self._banner.set_state("idle", "点击「重新挑战」开始新一轮 ↑")
            return

        ai_move = _random_move()
        if self._mode == "mmy" and self._wins >= self._goal - 1:
            ai_move = _counter_move(player_move)

        self._player_icon.setText(MOVE_ICON[player_move])
        self._player_icon.setStyleSheet(
            "font-size:32px; background:#E8F5E9; border:2px solid #4CAF50; border-radius:12px;"
        )
        self._ai_icon.setText(MOVE_ICON[ai_move])
        self._ai_icon.setStyleSheet(
            "font-size:32px; background:#E3F2FD; border:2px solid #2196F3; border-radius:12px;"
        )

        pi, ai = MOVE_ICON[player_move], MOVE_ICON[ai_move]
        result = _judge(player_move, ai_move)

        if result == 1:
            self._wins += 1
            self._refresh_progress()
            if self._wins >= self._goal:
                self._banner.set_state("win", f"🎊 挑战成功！达成 {self._goal} 连胜！")
                self._finished = True
            else:
                self._banner.set_state(
                    "win", f"{pi} 胜 {ai}  ·  连胜 {self._wins}/{self._goal}"
                )
        elif result == -1:
            self._wins = 0
            self._refresh_progress()
            self._finished = True
            if self._mode == "mmy":
                self._banner.set_state("lose", f"😈 mmy：注定无法赢！{ai} 胜 {pi}")
            else:
                self._banner.set_state("lose", f"{ai} 胜 {pi}  ·  连胜中断，挑战失败")
        else:
            self._banner.set_state("draw", f"{pi} vs {ai}  ·  平局，继续出拳")


# ─────────────────────────────────────────────────────────────────────────────
#  顶层 Widget
# ─────────────────────────────────────────────────────────────────────────────
class SjbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("featurePage")
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        head = QHBoxLayout()
        ico = QLabel("✊")
        ico.setStyleSheet("font-size:28px;")
        title = QLabel("SJB PK")
        title.setObjectName("featureTitle")
        sub = QLabel("石头剪刀布  ·  双人对战  ·  电脑挑战")
        sub.setStyleSheet("font-size:11px; color:#9AB9A8;")
        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(title)
        col.addWidget(sub)
        head.addWidget(ico)
        head.addSpacing(6)
        head.addLayout(col)
        head.addStretch()

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color:#DCF0E6;")

        self._stack = QStackedWidget()
        self._mode_page = ModeSelectPage()
        self._pvp_page  = PvpPage()
        self._pve_page  = PvePage()

        self._mode_page.mode_selected.connect(self._switch_mode)
        self._pvp_page.back_to_mode.connect(lambda: self._stack.setCurrentIndex(0))
        self._pve_page.back_to_mode.connect(lambda: self._stack.setCurrentIndex(0))

        self._stack.addWidget(self._mode_page)
        self._stack.addWidget(self._pvp_page)
        self._stack.addWidget(self._pve_page)

        root.addLayout(head)
        root.addWidget(div)
        root.addWidget(self._stack, 1)

    def _switch_mode(self, mode: str) -> None:
        self._stack.setCurrentIndex(1 if mode == "pvp" else 2)
