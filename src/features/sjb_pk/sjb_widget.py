"""
SJB PK 功能模块
- 入口：选择 PVP / PVE
- PVP：红蓝双方出拳，判定胜负并累计比分
- PVE：四难度挑战；mmy 模式在第 5 胜前强制玩家失败
"""

from __future__ import annotations

import random

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

MOVES = ("石头", "剪刀", "布")
MOVE_ICON = {
    "石头": "✊",
    "剪刀": "✌",
    "布": "🖐",
}
MOVE_BEATS = {
    "石头": "剪刀",
    "剪刀": "布",
    "布": "石头",
}
DIFFICULTIES: list[tuple[str, int]] = [
    ("Easy", 1),
    ("Normal", 3),
    ("Hard", 6),
    ("mmy", 5),
]


def _judge(a: str, b: str) -> int:
    """返回 1 表示 a 胜；-1 表示 b 胜；0 表示平局。"""
    if a == b:
        return 0
    return 1 if MOVE_BEATS[a] == b else -1


def _random_move() -> str:
    return random.choice(MOVES)


def _counter_move(player_move: str) -> str:
    for move, beaten in MOVE_BEATS.items():
        if beaten == player_move:
            return move
    return "石头"


class ModeSelectPage(QWidget):
    mode_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        banner = QFrame()
        banner.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #E9F9F1, stop:1 #F8FFFC);
                border: 2px solid #C8E6D5;
                border-radius: 14px;
            }
            """
        )
        b_lay = QVBoxLayout(banner)
        b_lay.setContentsMargins(16, 14, 16, 14)
        b_lay.setSpacing(6)

        title = QLabel("⚔ SJB PK 对战大厅")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color:#1A6B45;")
        subtitle = QLabel("选择模式开始对战：玩家对玩家 或 玩家挑战电脑")
        subtitle.setStyleSheet("font-size: 13px; color:#6DA788;")
        b_lay.addWidget(title)
        b_lay.addWidget(subtitle)

        mode_box = QHBoxLayout()
        mode_box.setSpacing(14)

        pvp_btn = QPushButton("👥 PVP 双人对战")
        pvp_btn.setObjectName("primaryButton")
        pvp_btn.setMinimumHeight(46)
        pvp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pvp_btn.clicked.connect(lambda: self.mode_selected.emit("pvp"))

        pve_btn = QPushButton("🤖 PVE 挑战电脑")
        pve_btn.setObjectName("templateButton")
        pve_btn.setMinimumHeight(46)
        pve_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pve_btn.clicked.connect(lambda: self.mode_selected.emit("pve"))

        mode_box.addWidget(pvp_btn)
        mode_box.addWidget(pve_btn)

        tips = QLabel(
            "PVP：红方和蓝方分别出拳，自动结算并累积比分\n"
            "PVE：Easy(1) / Normal(3) / Hard(6) / mmy(5，最终必败)"
        )
        tips.setStyleSheet(
            "font-size:12px; color:#4A9970; background:#F5FFFB;"
            "border:1px solid #D5EFE2; border-radius:10px; padding:10px;"
        )

        root.addWidget(banner)
        root.addLayout(mode_box)
        root.addWidget(tips)
        root.addStretch()


class FighterPanel(QFrame):
    move_selected = Signal(str)

    def __init__(self, title: str, accent: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            QFrame {{
                background: white;
                border: 2px solid {accent};
                border-radius: 14px;
            }}
            """
        )
        self._setup_ui(title, accent)

    def _setup_ui(self, title: str, accent: str):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        ttl = QLabel(title)
        ttl.setStyleSheet(f"font-size:16px; font-weight:bold; color:{accent};")
        self._move_label = QLabel("等待出拳")
        self._move_label.setStyleSheet("font-size:13px; color:#7CB89C;")

        lay.addWidget(ttl)
        lay.addWidget(self._move_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self._btn_group = QButtonGroup(self)
        for move in MOVES:
            btn = QPushButton(f"{MOVE_ICON[move]} {move}")
            btn.setObjectName("primaryButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(34)
            btn.clicked.connect(lambda _=False, m=move: self.move_selected.emit(m))
            self._btn_group.addButton(btn)
            btn_row.addWidget(btn)

        random_btn = QPushButton("🎲 随机")
        random_btn.setObjectName("sendButton")
        random_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        random_btn.setMinimumHeight(34)
        random_btn.clicked.connect(lambda: self.move_selected.emit(_random_move()))

        lay.addLayout(btn_row)
        lay.addWidget(random_btn)

    def set_move(self, move: str | None):
        if not move:
            self._move_label.setText("等待出拳")
            return
        self._move_label.setText(f"已选择：{MOVE_ICON[move]} {move}")


class PvpPage(QWidget):
    back_to_mode = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._red_move: str | None = None
        self._blue_move: str | None = None
        self._red_score = 0
        self._blue_score = 0
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        head = QHBoxLayout()
        title = QLabel("👥 PVP 双人对战")
        title.setStyleSheet("font-size:20px; font-weight:bold; color:#1A6B45;")

        back_btn = QPushButton("← 选择其他模式")
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_to_mode.emit)

        head.addWidget(title)
        head.addStretch()
        head.addWidget(back_btn)

        score_card = QFrame()
        score_card.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #FFF1F1, stop:1 #EEF8FF);
                border: 2px solid #DCEAF7;
                border-radius: 12px;
            }
            """
        )
        sc_lay = QHBoxLayout(score_card)
        sc_lay.setContentsMargins(14, 8, 14, 8)

        self._score_lbl = QLabel("🔴 红方 0 : 0 蓝方 🔵")
        self._score_lbl.setStyleSheet(
            "font-size:26px; font-weight:bold; color:#215A74; font-family:Consolas;"
        )
        self._round_lbl = QLabel("等待双方出拳")
        self._round_lbl.setStyleSheet("font-size:13px; color:#4A9970;")

        sc_lay.addWidget(self._score_lbl)
        sc_lay.addStretch()
        sc_lay.addWidget(self._round_lbl)

        self._red_panel = FighterPanel("🔴 红方（上）", "#DD4A4A")
        self._blue_panel = FighterPanel("🔵 蓝方（下）", "#3D7FCC")

        self._red_panel.move_selected.connect(self._on_red_selected)
        self._blue_panel.move_selected.connect(self._on_blue_selected)

        bottom = QHBoxLayout()
        reset_btn = QPushButton("重置比分")
        reset_btn.setObjectName("dangerButton")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_scores)

        clear_btn = QPushButton("清空本回合")
        clear_btn.setObjectName("templateButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_round)

        bottom.addStretch()
        bottom.addWidget(clear_btn)
        bottom.addWidget(reset_btn)

        root.addLayout(head)
        root.addWidget(score_card)
        root.addWidget(self._red_panel)
        root.addWidget(self._blue_panel)
        root.addLayout(bottom)

    def _on_red_selected(self, move: str):
        self._red_move = move
        self._red_panel.set_move(move)
        self._try_settle()

    def _on_blue_selected(self, move: str):
        self._blue_move = move
        self._blue_panel.set_move(move)
        self._try_settle()

    def _try_settle(self):
        if not self._red_move or not self._blue_move:
            if self._red_move and not self._blue_move:
                self._round_lbl.setText("红方已出拳，等待蓝方")
            elif self._blue_move and not self._red_move:
                self._round_lbl.setText("蓝方已出拳，等待红方")
            return

        result = _judge(self._red_move, self._blue_move)
        if result == 1:
            self._red_score += 1
            text = f"本回合：红方胜（{self._red_move} 胜 {self._blue_move}）"
        elif result == -1:
            self._blue_score += 1
            text = f"本回合：蓝方胜（{self._blue_move} 胜 {self._red_move}）"
        else:
            text = f"本回合：平局（{self._red_move} vs {self._blue_move}）"

        self._score_lbl.setText(f"🔴 红方 {self._red_score} : {self._blue_score} 蓝方 🔵")
        self._round_lbl.setText(text)
        self._clear_round(keep_tip=True)

    def _clear_round(self, keep_tip: bool = False):
        self._red_move = None
        self._blue_move = None
        self._red_panel.set_move(None)
        self._blue_panel.set_move(None)
        if not keep_tip:
            self._round_lbl.setText("等待双方出拳")

    def _reset_scores(self):
        self._red_score = 0
        self._blue_score = 0
        self._score_lbl.setText("🔴 红方 0 : 0 蓝方 🔵")
        self._round_lbl.setText("比分已重置，开始新对局")
        self._clear_round(keep_tip=True)


class PvePage(QWidget):
    back_to_mode = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._wins = 0
        self._goal = 1
        self._mode = "Easy"
        self._finished = False
        self._setup_ui()
        self._apply_mode("Easy")

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        head = QHBoxLayout()
        title = QLabel("🤖 PVE 挑战电脑")
        title.setStyleSheet("font-size:20px; font-weight:bold; color:#1A6B45;")

        back_btn = QPushButton("← 选择其他模式")
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_to_mode.emit)

        head.addWidget(title)
        head.addStretch()
        head.addWidget(back_btn)

        cfg = QFrame()
        cfg.setStyleSheet(
            "QFrame{background:#F8FFFC; border:2px solid #D5EFE2; border-radius:10px;}"
        )
        cfg_lay = QHBoxLayout(cfg)
        cfg_lay.setContentsMargins(12, 8, 12, 8)

        cfg_lay.addWidget(QLabel("难度:"))
        self._diff_combo = QComboBox()
        for name, need in DIFFICULTIES:
            desc = f"{name}（连胜 {need} 次）"
            if name == "mmy":
                desc = "mmy"
            self._diff_combo.addItem(desc, (name, need))
        self._diff_combo.currentIndexChanged.connect(self._on_diff_change)

        self._progress_lbl = QLabel("")
        self._progress_lbl.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#1A6B45;"
            "font-family:Consolas;"
        )

        reset_btn = QPushButton("重新挑战")
        reset_btn.setObjectName("templateButton")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_run)

        cfg_lay.addWidget(self._diff_combo)
        cfg_lay.addStretch()
        cfg_lay.addWidget(self._progress_lbl)
        cfg_lay.addSpacing(8)
        cfg_lay.addWidget(reset_btn)

        arena = QFrame()
        arena.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #F0FAF5, stop:1 #FFFFFF);
                border: 2px solid #DDEFE5;
                border-radius: 14px;
            }
            """
        )
        a_lay = QGridLayout(arena)
        a_lay.setContentsMargins(14, 12, 14, 12)
        a_lay.setHorizontalSpacing(10)
        a_lay.setVerticalSpacing(6)

        self._player_pick = QLabel("你：未出拳")
        self._ai_pick = QLabel("电脑：未出拳")
        self._player_pick.setStyleSheet("font-size:16px; font-weight:bold; color:#1A6B45;")
        self._ai_pick.setStyleSheet("font-size:16px; font-weight:bold; color:#3D7FCC;")
        self._status = QLabel("选择你的出拳，开始挑战")
        self._status.setStyleSheet("font-size:13px; color:#4A9970;")

        a_lay.addWidget(self._player_pick, 0, 0)
        a_lay.addWidget(self._ai_pick, 0, 1)
        a_lay.addWidget(self._status, 1, 0, 1, 2)

        pick_row = QHBoxLayout()
        pick_row.setSpacing(8)
        for move in MOVES:
            btn = QPushButton(f"{MOVE_ICON[move]} {move}")
            btn.setObjectName("primaryButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(36)
            btn.clicked.connect(lambda _=False, m=move: self._play_round(m))
            pick_row.addWidget(btn)

        random_btn = QPushButton("🎲 随机出拳")
        random_btn.setObjectName("sendButton")
        random_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        random_btn.setMinimumHeight(36)
        random_btn.clicked.connect(lambda: self._play_round(_random_move()))
        pick_row.addWidget(random_btn)

        root.addLayout(head)
        root.addWidget(cfg)
        root.addWidget(arena)
        root.addLayout(pick_row)
        root.addStretch()

    def _on_diff_change(self):
        mode, goal = self._diff_combo.currentData()
        self._apply_mode(mode, goal)

    def _apply_mode(self, mode: str, goal: int | None = None):
        if goal is None:
            for name, need in DIFFICULTIES:
                if name == mode:
                    goal = need
                    break
        self._mode = mode
        self._goal = goal or 1
        self._wins = 0
        self._finished = False
        self._player_pick.setText("你：未出拳")
        self._ai_pick.setText("电脑：未出拳")
        self._status.setText("选择你的出拳，开始挑战")
        self._refresh_progress()

    def _reset_run(self):
        self._apply_mode(self._mode, self._goal)

    def _refresh_progress(self):
        self._progress_lbl.setText(f"进度 {self._wins}/{self._goal}")

    def _play_round(self, player_move: str):
        if self._finished:
            self._status.setText("本轮已结束，请点击“重新挑战”再来一局")
            return

        ai_move = _random_move()
        if self._mode == "mmy" and self._wins >= self._goal - 1:
            ai_move = _counter_move(player_move)

        self._player_pick.setText(f"你：{MOVE_ICON[player_move]} {player_move}")
        self._ai_pick.setText(f"电脑：{MOVE_ICON[ai_move]} {ai_move}")

        result = _judge(player_move, ai_move)
        if result == 1:
            self._wins += 1
            if self._wins >= self._goal:
                if self._mode == "mmy":
                    self._status.setText("mmy 规则触发：你本不该赢，系统判定失败 ❌")
                    self._finished = True
                    self._wins = 0
                else:
                    self._status.setText(f"挑战成功！你已达成 {self._goal} 连胜 ✅")
                    self._finished = True
            else:
                self._status.setText("本回合胜利，继续挑战下一回合")
        elif result == -1:
            self._status.setText("你输了，本轮挑战结束。点击“重新挑战”重开")
            self._finished = True
            self._wins = 0
        else:
            self._status.setText("平局，本回合不计入连胜，继续出拳")

        if self._mode == "mmy" and self._wins >= self._goal:
            self._status.setText("mmy 模式：挑战失败 ❌")
            self._finished = True
            self._wins = 0

        self._refresh_progress()


class SjbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("featurePage")
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        head = QHBoxLayout()
        icon_lbl = QLabel("✊")
        icon_lbl.setStyleSheet("font-size:32px;")
        title_lbl = QLabel("SJB PK")
        title_lbl.setObjectName("featureTitle")
        sub_lbl = QLabel("石头剪刀布 · 双人对战 · 电脑挑战")
        sub_lbl.setStyleSheet("font-size:12px; color:#8BAF9B;")

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_col.addWidget(title_lbl)
        title_col.addWidget(sub_lbl)

        head.addWidget(icon_lbl)
        head.addLayout(title_col)
        head.addStretch()

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color:#DCF0E6;")

        self._stack = QStackedWidget()

        self._mode_page = ModeSelectPage()
        self._pvp_page = PvpPage()
        self._pve_page = PvePage()

        self._mode_page.mode_selected.connect(self._switch_mode)
        self._pvp_page.back_to_mode.connect(lambda: self._stack.setCurrentIndex(0))
        self._pve_page.back_to_mode.connect(lambda: self._stack.setCurrentIndex(0))

        self._stack.addWidget(self._mode_page)
        self._stack.addWidget(self._pvp_page)
        self._stack.addWidget(self._pve_page)

        root.addLayout(head)
        root.addWidget(divider)
        root.addWidget(self._stack, 1)

    def _switch_mode(self, mode: str):
        if mode == "pvp":
            self._stack.setCurrentIndex(1)
        else:
            self._stack.setCurrentIndex(2)
