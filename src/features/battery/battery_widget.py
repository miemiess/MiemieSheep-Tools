"""
电脑电量查询功能模块
趣味功能：动画进度条检测 → 弹出"有电"结果弹窗
"""
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QDialog, QFrame
)
from PySide6.QtCore import Qt, QTimer


class ResultDialog(QDialog):
    """检测成功结果弹窗"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("检测结果")
        self.setFixedSize(340, 260)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #F0F7F4;
                border-radius: 16px;
            }
            QLabel {
                color: #2C3E50;
                background: transparent;
            }
            QPushButton {
                background-color: #3EC78C;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
                font-family: "Microsoft YaHei", sans-serif;
            }
            QPushButton:hover {
                background-color: #2DB57B;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 24, 24, 24)

        sheep_lbl = QLabel("🐑")
        sheep_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sheep_lbl.setStyleSheet("font-size: 62px;")

        result_lbl = QLabel("有电！⚡")
        result_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_lbl.setStyleSheet(
            "font-size: 30px; font-weight: bold; color: #1A6B45;"
        )

        sub_lbl = QLabel("咩~ 电量充足，咩咩羊精力满满！")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("font-size: 13px; color: #7CB89C;")

        ok_btn = QPushButton("太好了！🎉")
        ok_btn.setFixedWidth(150)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        btn_row.addStretch()

        layout.addWidget(sheep_lbl)
        layout.addWidget(result_lbl)
        layout.addWidget(sub_lbl)
        layout.addSpacing(8)
        layout.addLayout(btn_row)


class BatteryWidget(QWidget):
    """电脑电量查询页面"""

    _STATUS_MESSAGES = [
        (0,  25,  "正在连接电源管理模块... 🔌"),
        (25, 50,  "正在读取 ACPI 电量数据... 📊"),
        (50, 75,  "正在分析电池健康状态... 🔍"),
        (75, 95,  "即将完成，请稍候... ⚡"),
        (95, 100, "检测完成！✅"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("featurePage")
        self._value = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(22)
        layout.setContentsMargins(50, 30, 50, 30)

        # 图标
        icon_lbl = QLabel("🔋")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 76px;")

        # 标题
        title_lbl = QLabel("电脑电量查询")
        title_lbl.setObjectName("featureTitle")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 副标题
        sub_lbl = QLabel("趣味功能 · 点击检测你的电量满不满 🐑")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("font-size: 13px; color: #8BAF9B;")

        # 分隔线
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #DCF0E6;")

        # 状态文字
        self._status_lbl = QLabel("点击开始检测，看看你的电量如何 🔌")
        self._status_lbl.setObjectName("batteryStatusLabel")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 进度条容器（限制最大宽度）
        pb_wrapper = QWidget()
        pb_wrapper.setFixedWidth(520)
        pb_layout = QHBoxLayout(pb_wrapper)
        pb_layout.setContentsMargins(0, 0, 0, 0)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(True)
        self._progress.setFormat("%p%")
        pb_layout.addWidget(self._progress)

        # 按钮
        self._start_btn = QPushButton("🐑  开始检测")
        self._start_btn.setObjectName("primaryButton")
        self._start_btn.setFixedWidth(200)
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.clicked.connect(self._start)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._start_btn)
        btn_row.addStretch()

        layout.addStretch()
        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)
        layout.addWidget(divider)
        layout.addSpacing(8)
        layout.addWidget(self._status_lbl)
        layout.addWidget(pb_wrapper, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(btn_row)
        layout.addStretch()

    def _start(self):
        self._value = 0
        self._progress.setValue(0)
        self._status_lbl.setStyleSheet("font-size: 15px; color: #4A9970;")
        self._status_lbl.setText("正在连接电源管理模块... 🔌")
        self._start_btn.setEnabled(False)
        self._timer.start(25)   # 每 25ms 走一格，约 2.5 秒填满

    def _tick(self):
        self._value += 1
        self._progress.setValue(self._value)

        for lo, hi, msg in self._STATUS_MESSAGES:
            if lo <= self._value < hi:
                self._status_lbl.setText(msg)
                break

        if self._value >= 100:
            self._timer.stop()
            self._status_lbl.setText("咩咩羊满血复活！⚡🐑")
            self._status_lbl.setStyleSheet(
                "font-size: 15px; color: #1FA069; font-weight: bold;"
            )
            dlg = ResultDialog(self)
            dlg.exec()
            self._start_btn.setEnabled(True)
