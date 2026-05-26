"""
主窗口 —— 咩咩羊Tools
包含：标题栏、功能卡片主页、各功能页面的导航
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGridLayout,
    QStackedWidget, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from features.battery.battery_widget import BatteryWidget
from features.time_getter.time_widget import TimeWidget
from features.mqtt_forwarder.mqtt_widget import MQTTWidget
from features.sjb_pk.sjb_widget import SjbWidget
from resources.styles import MAIN_STYLE


# -------------------------------------------------------------------
# 可点击功能卡片
# -------------------------------------------------------------------
class ClickableCard(QFrame):
    clicked = Signal()

    def __init__(self, icon: str, title: str, desc: str,
                 enabled: bool = True, parent=None):
        super().__init__(parent)
        self._enabled = enabled
        self.setObjectName("featureCard" if enabled else "comingSoonCard")
        self.setFixedSize(200, 162)
        if enabled:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._build(icon, title, desc, enabled)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 80, 40, 28))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def _build(self, icon, title, desc, enabled):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 16, 10, 16)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setObjectName("cardIcon" if enabled else "cardIconDimmed")

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setObjectName("cardTitle" if enabled else "cardTitleDimmed")

        desc_lbl = QLabel(desc)
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setObjectName("cardDesc" if enabled else "cardDescDimmed")

        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)

    def mousePressEvent(self, event):
        if self._enabled and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# -------------------------------------------------------------------
# 主页（功能选择网格）
# -------------------------------------------------------------------
class HomePage(QWidget):
    navigate = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homePage")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(18)
        layout.setContentsMargins(40, 28, 40, 28)

        greeting = QLabel("🐑  你好！欢迎使用咩咩羊工具箱")
        greeting.setObjectName("homeGreeting")
        greeting.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("选择一个功能开始使用吧~  更多功能持续添加中 ✨")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("font-size: 12px; color: #A0C8B0;")

        # 功能卡片
        card1 = ClickableCard("🔋", "电脑电量查询", "趣味检测你的电量")
        card1.clicked.connect(lambda: self.navigate.emit(1))

        card2 = ClickableCard("🕐", "时间获取", "获取 UTC 时间戳")
        card2.clicked.connect(lambda: self.navigate.emit(2))

        card3 = ClickableCard("📡", "高速转发", "MQTT 消息转发")
        card3.clicked.connect(lambda: self.navigate.emit(3))

        card4 = ClickableCard("✊", "SJB PK", "石头剪刀布 PVE / PVP")
        card4.clicked.connect(lambda: self.navigate.emit(4))
        card5 = ClickableCard("🎨", "功能开发中", "敬请期待...", enabled=False)
        card6 = ClickableCard("🌟", "功能开发中", "敬请期待...", enabled=False)

        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setSpacing(20)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.addWidget(card1, 0, 0)
        grid.addWidget(card2, 0, 1)
        grid.addWidget(card3, 0, 2)
        grid.addWidget(card4, 1, 0)
        grid.addWidget(card5, 1, 1)
        grid.addWidget(card6, 1, 2)

        layout.addStretch()
        layout.addWidget(greeting)
        layout.addWidget(sub)
        layout.addSpacing(10)
        layout.addWidget(grid_w, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()


# -------------------------------------------------------------------
# 功能页包装器（含顶部返回按钮栏）
# -------------------------------------------------------------------
class FeaturePage(QWidget):
    go_back = Signal()

    def __init__(self, feature_widget: QWidget, parent=None):
        super().__init__(parent)
        self.setObjectName("featurePage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部导航栏
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(44)
        bar_layout = QHBoxLayout(top_bar)
        bar_layout.setContentsMargins(16, 6, 16, 6)

        back_btn = QPushButton("←  返回主界面")
        back_btn.setObjectName("backButton")
        back_btn.setFixedWidth(140)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.go_back.emit)

        bar_layout.addWidget(back_btn)
        bar_layout.addStretch()

        layout.addWidget(top_bar)
        layout.addWidget(feature_widget, 1)


# -------------------------------------------------------------------
# 主窗口
# -------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("咩咩羊 Tools")
        self.setMinimumSize(920, 700)
        self.resize(920, 720)
        self.setStyleSheet(MAIN_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        self._stack = QStackedWidget()

        home = HomePage()
        home.navigate.connect(self._stack.setCurrentIndex)

        battery_page = FeaturePage(BatteryWidget())
        battery_page.go_back.connect(lambda: self._stack.setCurrentIndex(0))

        time_page = FeaturePage(TimeWidget())
        time_page.go_back.connect(lambda: self._stack.setCurrentIndex(0))

        mqtt_page = FeaturePage(MQTTWidget())
        mqtt_page.go_back.connect(lambda: self._stack.setCurrentIndex(0))

        sjb_page = FeaturePage(SjbWidget())
        sjb_page.go_back.connect(lambda: self._stack.setCurrentIndex(0))

        self._stack.addWidget(home)          # 0
        self._stack.addWidget(battery_page)  # 1
        self._stack.addWidget(time_page)     # 2
        self._stack.addWidget(mqtt_page)     # 3
        self._stack.addWidget(sjb_page)      # 4

        root.addWidget(self._stack, 1)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("headerWidget")
        header.setFixedHeight(64)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(22, 0, 22, 0)
        layout.setSpacing(12)

        icon_lbl = QLabel("🐑")
        icon_lbl.setObjectName("headerIcon")

        text_col = QWidget()
        text_layout = QVBoxLayout(text_col)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)

        app_title = QLabel("咩咩羊 Tools")
        app_title.setObjectName("appTitle")

        app_sub = QLabel("咩咩羊的万能工具箱 🐑✨")
        app_sub.setObjectName("appSubtitle")

        text_layout.addWidget(app_title)
        text_layout.addWidget(app_sub)

        ver_lbl = QLabel("v 1.0.0")
        ver_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.55); font-size: 11px;"
        )

        layout.addWidget(icon_lbl)
        layout.addWidget(text_col)
        layout.addStretch()
        layout.addWidget(ver_lbl)

        return header

