"""
时间工具功能模块（增强版）
功能：
  Tab1 - 实时时钟 + 全球多时区对照
  Tab2 - 日期时间 → UTC时间戳 转换器
  Tab3 - 时间戳 → 多时区时间 解析器
"""
import datetime

# ---------------------------------------------------------------------------
# 时区支持：优先 zoneinfo(+tzdata)，降级到固定偏移量
# ---------------------------------------------------------------------------
try:
    from zoneinfo import ZoneInfo as _ZI
    _ZONEINFO_OK = True
except ImportError:
    _ZONEINFO_OK = False

_FIXED_OFFSETS: dict[str, float] = {
    "UTC": 0,
    "Asia/Shanghai": 8,   "Asia/Hong_Kong": 8,  "Asia/Taipei": 8,
    "Asia/Singapore": 8,  "Asia/Tokyo": 9,       "Asia/Kolkata": 5.5,
    "Asia/Dubai": 4,
    "Europe/London": 0,   "Europe/Paris": 1,     "Europe/Berlin": 1,
    "Europe/Moscow": 3,
    "America/New_York": -5, "America/Los_Angeles": -8,
    "America/Sao_Paulo": -3, "Australia/Sydney": 10,
}


def _get_tz(tz_name: str):
    if _ZONEINFO_OK:
        try:
            return _ZI(tz_name)
        except Exception:
            pass
    h = _FIXED_OFFSETS.get(tz_name, 0)
    total_min = int(h * 60)
    return datetime.timezone(datetime.timedelta(minutes=total_min))


def _now_tz(tz_name: str) -> datetime.datetime:
    return datetime.datetime.now(tz=_get_tz(tz_name))


def _ts_to_dt(ts: float, tz_name: str) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(ts, tz=_get_tz(tz_name))


def _fmt_offset(dt: datetime.datetime) -> str:
    off = dt.utcoffset()
    if off is None:
        return "UTC+00:00"
    s = int(off.total_seconds())
    sign = "+" if s >= 0 else "-"
    s = abs(s)
    h, m = divmod(s // 60, 60)
    return f"UTC{sign}{h:02d}:{m:02d}"


_WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]

COMMON_ZONES: list[tuple[str, str]] = [
    ("UTC 协调世界时",      "UTC"),
    ("中国标准时间 +8",     "Asia/Shanghai"),
    ("香港时间 +8",          "Asia/Hong_Kong"),
    ("台北时间 +8",          "Asia/Taipei"),
    ("新加坡时间 +8",        "Asia/Singapore"),
    ("日本标准时间 +9",      "Asia/Tokyo"),
    ("印度标准时间 +5:30",   "Asia/Kolkata"),
    ("迪拜时间 +4",          "Asia/Dubai"),
    ("英国时间 ±0/+1",       "Europe/London"),
    ("中欧时间 +1/+2",       "Europe/Paris"),
    ("德国时间 +1/+2",       "Europe/Berlin"),
    ("莫斯科时间 +3",        "Europe/Moscow"),
    ("美国东部 -5/-4",       "America/New_York"),
    ("美国西部 -8/-7",       "America/Los_Angeles"),
    ("巴西时间 -3",           "America/Sao_Paulo"),
    ("澳大利亚东部 +10/+11", "Australia/Sydney"),
]

# ---------------------------------------------------------------------------
# PySide6 imports
# ---------------------------------------------------------------------------
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTabWidget, QDateTimeEdit, QComboBox, QLineEdit,
    QGridLayout, QGroupBox, QScrollArea, QApplication,
)
from PySide6.QtCore import Qt, QTimer, QDateTime


# ---------------------------------------------------------------------------
# 共用辅助函数
# ---------------------------------------------------------------------------
def _copy_btn(get_text) -> QPushButton:
    """返回一个小型剪贴板复制按钮"""
    btn = QPushButton("📋")
    btn.setFixedSize(26, 26)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setToolTip("复制到剪贴板")
    btn.setStyleSheet("""
        QPushButton { background:transparent; border:none; font-size:13px; }
        QPushButton:hover { background:#DCF0E6; border-radius:5px; }
    """)
    btn.clicked.connect(lambda: QApplication.clipboard().setText(get_text()))
    return btn


def _res_row(grid: QGridLayout, row: int, label: str, default: str = "—") -> QLabel:
    """在 QGridLayout 中添加一行 label + value + copy_btn"""
    lbl = QLabel(label)
    lbl.setStyleSheet("font-size:12px; color:#4A9970; font-weight:bold;")
    val = QLabel(default)
    val.setStyleSheet(
        "font-size:14px; font-weight:bold; color:#1A6B45; font-family:Consolas;"
    )
    grid.addWidget(lbl, row, 0)
    grid.addWidget(val, row, 1)
    grid.addWidget(_copy_btn(lambda v=val: v.text()), row, 2)
    return val


# ---------------------------------------------------------------------------
# 时区对照表行 Widget
# ---------------------------------------------------------------------------
class TzRow(QFrame):
    def __init__(self, display: str, tz_name: str, parent=None):
        super().__init__(parent)
        self._tz_name = tz_name
        self.setObjectName("tzTableRow")
        self.setStyleSheet("""
            QFrame#tzTableRow {
                background: white;
                border-radius: 5px;
                border: 1px solid #EAF5EE;
            }
            QFrame#tzTableRow:hover { border: 1px solid #3EC78C; }
        """)
        self.setMaximumHeight(34)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 3, 8, 3)
        lay.setSpacing(6)

        name_lbl = QLabel(display)
        name_lbl.setFixedWidth(175)
        name_lbl.setStyleSheet(
            "font-size:11px; color:#2C6E49; font-weight:bold;"
        )
        self._off_lbl = QLabel("UTC+00:00")
        self._off_lbl.setFixedWidth(78)
        self._off_lbl.setStyleSheet(
            "font-size:11px; color:#7CB89C; font-family:Consolas;"
        )
        self._time_lbl = QLabel("--:--:--")
        self._time_lbl.setFixedWidth(70)
        self._time_lbl.setStyleSheet(
            "font-size:13px; font-weight:bold; color:#1A6B45; font-family:Consolas;"
        )
        self._date_lbl = QLabel("----/--/--")
        self._date_lbl.setFixedWidth(88)
        self._date_lbl.setStyleSheet(
            "font-size:11px; color:#7CB89C; font-family:Consolas;"
        )
        self._wd_lbl = QLabel("")
        self._wd_lbl.setStyleSheet("font-size:11px; color:#9EB5AB;")

        lay.addWidget(name_lbl)
        lay.addWidget(self._off_lbl)
        lay.addWidget(self._time_lbl)
        lay.addWidget(self._date_lbl)
        lay.addWidget(self._wd_lbl, 1)
        lay.addWidget(
            _copy_btn(
                lambda: (
                    f"{self._date_lbl.text()} "
                    f"{self._time_lbl.text()} "
                    f"({self._off_lbl.text()})"
                )
            )
        )

    def update_dt(self, dt: datetime.datetime):
        self._off_lbl.setText(_fmt_offset(dt))
        self._time_lbl.setText(dt.strftime("%H:%M:%S"))
        self._date_lbl.setText(dt.strftime("%Y-%m-%d"))
        self._wd_lbl.setText(f"星期{_WEEKDAYS[dt.weekday()]}")


# ---------------------------------------------------------------------------
# 时区对照表 Widget（可复用）
# ---------------------------------------------------------------------------
class TzTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[TzRow] = []
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 4, 0)
        lay.setSpacing(2)

        # 表头
        hdr = QFrame()
        hdr.setStyleSheet("background-color:#C8E6D5; border-radius:5px;")
        hdr.setMaximumHeight(24)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(8, 2, 8, 2)
        hdr_lay.setSpacing(6)
        for txt, w in [("时区名称", 175), ("UTC偏移", 78),
                       ("时间", 70), ("日期", 88), ("", 0)]:
            lbl = QLabel(txt)
            if w:
                lbl.setFixedWidth(w)
            lbl.setStyleSheet("font-size:11px; color:#1A6B45; font-weight:bold;")
            hdr_lay.addWidget(lbl)
        lay.addWidget(hdr)

        for display, tz_name in COMMON_ZONES:
            row = TzRow(display, tz_name)
            self._rows.append(row)
            lay.addWidget(row)
        lay.addStretch()

    def update_ts(self, ts: float):
        for row in self._rows:
            row.update_dt(_ts_to_dt(ts, row._tz_name))

    def update_now(self):
        ts = datetime.datetime.now(datetime.timezone.utc).timestamp()
        self.update_ts(ts)


# ---------------------------------------------------------------------------
# Tab 1：实时时钟 + 全球时区对照
# ---------------------------------------------------------------------------
class ClockTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._setup_ui()
        self._tick()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(8)

        # ── 主时钟卡片 ──────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("clockCard")
        card.setStyleSheet("""
            QFrame#clockCard {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #EBF8F2, stop:1 #F5FFFB);
                border-radius: 14px;
                border: 2px solid #C8E6D5;
            }
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.setSpacing(2)
        card_lay.setContentsMargins(16, 10, 16, 10)

        self._main_time = QLabel("--:--:--")
        self._main_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._main_time.setStyleSheet(
            "font-size:54px; font-weight:bold; color:#1A6B45;"
            " font-family:Consolas,monospace; letter-spacing:5px;"
        )
        self._main_date = QLabel("----/--/--")
        self._main_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._main_date.setStyleSheet("font-size:14px; color:#4A9970;")

        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        tz_lbl = QLabel("主时区:")
        tz_lbl.setStyleSheet("font-size:12px; color:#4A9970; font-weight:bold;")
        self._tz_combo = QComboBox()
        for d, n in COMMON_ZONES:
            self._tz_combo.addItem(d, n)
        self._tz_combo.setCurrentIndex(1)   # 默认 Asia/Shanghai
        self._tz_combo.setFixedWidth(185)
        self._tz_combo.currentIndexChanged.connect(self._tick)

        self._auto_btn = QPushButton("▶  自动刷新")
        self._auto_btn.setObjectName("primaryButton")
        self._auto_btn.setFixedSize(108, 30)
        self._auto_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._auto_btn.clicked.connect(self._toggle_auto)

        now_btn = QPushButton("⟳ 刷新")
        now_btn.setObjectName("primaryButton")
        now_btn.setFixedSize(64, 30)
        now_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        now_btn.clicked.connect(self._tick)

        ts_lbl = QLabel("UTC 时间戳:")
        ts_lbl.setStyleSheet("font-size:11px; color:#7CB89C;")
        self._ts_lbl = QLabel("0")
        self._ts_lbl.setStyleSheet(
            "font-size:13px; font-weight:bold; color:#5B9BD5; font-family:Consolas;"
        )

        ctrl.addWidget(tz_lbl)
        ctrl.addWidget(self._tz_combo)
        ctrl.addWidget(self._auto_btn)
        ctrl.addWidget(now_btn)
        ctrl.addStretch()
        ctrl.addWidget(ts_lbl)
        ctrl.addWidget(self._ts_lbl)
        ctrl.addWidget(_copy_btn(lambda: self._ts_lbl.text()))

        card_lay.addWidget(self._main_time)
        card_lay.addWidget(self._main_date)
        card_lay.addSpacing(4)
        card_lay.addLayout(ctrl)
        lay.addWidget(card)

        # ── 时区对照表 ─────────────────────────────────────────────────
        tbl_hdr = QLabel("🌍  全球时区实时对照")
        tbl_hdr.setStyleSheet("font-size:12px; font-weight:bold; color:#1A6B45;")
        lay.addWidget(tbl_hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._tztable = TzTable()
        scroll.setWidget(self._tztable)
        lay.addWidget(scroll, 1)

    def _toggle_auto(self):
        self._running = not self._running
        if self._running:
            self._timer.start()
            self._auto_btn.setText("⏸  暂停刷新")
            self._auto_btn.setStyleSheet("""
                QPushButton {
                    background-color:#FFB347; color:white; border:none;
                    border-radius:10px; padding:5px 12px;
                    font-size:12px; font-weight:bold;
                }
                QPushButton:hover { background-color:#FF9800; }
            """)
        else:
            self._timer.stop()
            self._auto_btn.setText("▶  自动刷新")
            self._auto_btn.setStyleSheet("")

    def _tick(self):
        tz_name = self._tz_combo.currentData()
        now = _now_tz(tz_name)
        wd = _WEEKDAYS[now.weekday()]
        self._main_time.setText(now.strftime("%H:%M:%S"))
        self._main_date.setText(
            now.strftime(f"%Y年%m月%d日  星期{wd}  ") + _fmt_offset(now)
        )
        ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        self._ts_lbl.setText(str(ts))
        self._tztable.update_now()


# ---------------------------------------------------------------------------
# Tab 2：日期时间 → 时间戳 转换器
# ---------------------------------------------------------------------------
class ConvertTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ts_sec: QLabel | None = None
        self._ts_ms:  QLabel | None = None
        self._utc_lbl: QLabel | None = None
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(8)

        # ── 输入区 ───────────────────────────────────────────────────────
        in_grp = QGroupBox("📅  输入日期时间")
        in_lay = QHBoxLayout(in_grp)
        in_lay.setSpacing(10)

        self._dt_edit = QDateTimeEdit()
        self._dt_edit.setDisplayFormat("yyyy-MM-dd  HH:mm:ss")
        self._dt_edit.setDateTime(QDateTime.currentDateTime())
        self._dt_edit.setFixedWidth(210)
        self._dt_edit.setCalendarPopup(True)

        tz_lbl = QLabel("时区:")
        tz_lbl.setStyleSheet("color:#4A9970; font-weight:bold; font-size:12px;")
        self._in_tz = QComboBox()
        for d, n in COMMON_ZONES:
            self._in_tz.addItem(d, n)
        self._in_tz.setCurrentIndex(1)   # 默认 Asia/Shanghai
        self._in_tz.setFixedWidth(185)

        conv_btn = QPushButton("🔄  转换")
        conv_btn.setObjectName("primaryButton")
        conv_btn.setFixedSize(88, 30)
        conv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        conv_btn.clicked.connect(self._convert)

        now_btn = QPushButton("📌 填入当前")
        now_btn.setObjectName("primaryButton")
        now_btn.setFixedSize(96, 30)
        now_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        now_btn.clicked.connect(self._fill_now)

        in_lay.addWidget(self._dt_edit)
        in_lay.addWidget(tz_lbl)
        in_lay.addWidget(self._in_tz)
        in_lay.addWidget(conv_btn)
        in_lay.addWidget(now_btn)
        in_lay.addStretch()
        lay.addWidget(in_grp)

        # ── 时间戳结果 ───────────────────────────────────────────────────
        ts_grp = QGroupBox("⏱  时间戳结果")
        ts_grid = QGridLayout(ts_grp)
        ts_grid.setSpacing(6)
        ts_grid.setColumnStretch(1, 1)
        self._ts_sec  = _res_row(ts_grid, 0, "Unix 时间戳（秒）:", "—")
        self._ts_ms   = _res_row(ts_grid, 1, "Unix 时间戳（毫秒）:", "—")
        self._utc_lbl = _res_row(ts_grid, 2, "UTC 标准时间:", "—")
        lay.addWidget(ts_grp)

        # ── 各时区 ───────────────────────────────────────────────────────
        tbl_hdr = QLabel("🌍  各时区对应时间")
        tbl_hdr.setStyleSheet("font-size:12px; font-weight:bold; color:#1A6B45;")
        lay.addWidget(tbl_hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._tztable = TzTable()
        scroll.setWidget(self._tztable)
        lay.addWidget(scroll, 1)

    def _fill_now(self):
        tz_name = self._in_tz.currentData()
        now = _now_tz(tz_name)
        self._dt_edit.setDateTime(
            QDateTime(now.year, now.month, now.day,
                      now.hour, now.minute, now.second)
        )
        self._convert()

    def _convert(self):
        tz_name = self._in_tz.currentData()
        qdt     = self._dt_edit.dateTime()
        naive   = datetime.datetime(
            qdt.date().year(), qdt.date().month(), qdt.date().day(),
            qdt.time().hour(), qdt.time().minute(), qdt.time().second(),
        )
        aware = naive.replace(tzinfo=_get_tz(tz_name))
        ts    = aware.timestamp()
        utc   = aware.astimezone(datetime.timezone.utc)

        self._ts_sec.setText(str(int(ts)))
        self._ts_ms.setText(str(int(ts * 1000)))
        self._utc_lbl.setText(utc.strftime("%Y-%m-%d %H:%M:%S  UTC"))
        self._tztable.update_ts(ts)


# ---------------------------------------------------------------------------
# Tab 3：时间戳 → 多时区 解析器
# ---------------------------------------------------------------------------
class ParseTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sec_lbl:  QLabel | None = None
        self._ms_lbl:   QLabel | None = None
        self._us_lbl:   QLabel | None = None
        self._utc_lbl:  QLabel | None = None
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(8)

        # ── 输入区 ───────────────────────────────────────────────────────
        in_grp = QGroupBox("🔢  输入时间戳")
        in_lay = QHBoxLayout(in_grp)
        in_lay.setSpacing(10)

        ts_lbl = QLabel("时间戳:")
        ts_lbl.setStyleSheet("color:#4A9970; font-weight:bold; font-size:12px;")
        self._ts_edit = QLineEdit()
        self._ts_edit.setPlaceholderText("秒(10位) / 毫秒(13位) / 微秒(16位)")
        self._ts_edit.setFixedWidth(220)
        self._ts_edit.returnPressed.connect(self._parse)

        unit_lbl = QLabel("单位:")
        unit_lbl.setStyleSheet("color:#4A9970; font-weight:bold; font-size:12px;")
        self._unit = QComboBox()
        self._unit.addItems(["自动判断", "秒 (s)", "毫秒 (ms)", "微秒 (μs)"])
        self._unit.setFixedWidth(118)

        parse_btn = QPushButton("🔍  解析")
        parse_btn.setObjectName("primaryButton")
        parse_btn.setFixedSize(88, 30)
        parse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        parse_btn.clicked.connect(self._parse)

        now_btn = QPushButton("📌 当前时间戳")
        now_btn.setObjectName("primaryButton")
        now_btn.setFixedSize(110, 30)
        now_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        now_btn.clicked.connect(self._use_now)

        in_lay.addWidget(ts_lbl)
        in_lay.addWidget(self._ts_edit)
        in_lay.addWidget(unit_lbl)
        in_lay.addWidget(self._unit)
        in_lay.addWidget(parse_btn)
        in_lay.addWidget(now_btn)
        in_lay.addStretch()
        lay.addWidget(in_grp)

        # ── 标准化结果 ───────────────────────────────────────────────────
        norm_grp = QGroupBox("⏱  标准化时间戳")
        norm_grid = QGridLayout(norm_grp)
        norm_grid.setSpacing(6)
        norm_grid.setColumnStretch(1, 1)
        self._sec_lbl = _res_row(norm_grid, 0, "Unix（秒）:", "—")
        self._ms_lbl  = _res_row(norm_grid, 1, "Unix（毫秒）:", "—")
        self._us_lbl  = _res_row(norm_grid, 2, "Unix（微秒）:", "—")
        self._utc_lbl = _res_row(norm_grid, 3, "UTC 标准时间:", "—")
        lay.addWidget(norm_grp)

        # ── 各时区 ───────────────────────────────────────────────────────
        tbl_hdr = QLabel("🌍  各时区对应时间")
        tbl_hdr.setStyleSheet("font-size:12px; font-weight:bold; color:#1A6B45;")
        lay.addWidget(tbl_hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._tztable = TzTable()
        scroll.setWidget(self._tztable)
        lay.addWidget(scroll, 1)

    def _use_now(self):
        ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        self._ts_edit.setText(str(ts))
        self._parse()

    def _parse(self):
        text = self._ts_edit.text().strip()
        if not text:
            return
        try:
            raw = float(text)
        except ValueError:
            self._utc_lbl.setText("❌ 格式无效，请输入数字")
            return

        unit = self._unit.currentIndex()
        if unit == 0:   # 自动判断
            if raw > 1e15:
                ts = raw / 1_000_000   # 微秒
            elif raw > 1e12:
                ts = raw / 1_000       # 毫秒
            else:
                ts = raw               # 秒
        elif unit == 1:
            ts = raw
        elif unit == 2:
            ts = raw / 1_000
        else:
            ts = raw / 1_000_000

        # 合理性检查（1970-01-01 ~ 3000-01-01）
        if not (0 <= ts <= 32503680000):
            self._utc_lbl.setText("❌ 时间戳超出合理范围")
            return

        self._sec_lbl.setText(str(int(ts)))
        self._ms_lbl.setText(str(int(ts * 1_000)))
        self._us_lbl.setText(str(int(ts * 1_000_000)))
        utc_dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        self._utc_lbl.setText(utc_dt.strftime("%Y-%m-%d %H:%M:%S  UTC"))
        self._tztable.update_ts(ts)


# ---------------------------------------------------------------------------
# 主 Widget（含标题 + QTabWidget）
# ---------------------------------------------------------------------------
class TimeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("featurePage")
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 12, 20, 12)
        lay.setSpacing(8)

        # 标题行
        hdr = QHBoxLayout()
        icon_lbl = QLabel("🕐")
        icon_lbl.setStyleSheet("font-size:32px;")
        title_lbl = QLabel("时间工具")
        title_lbl.setObjectName("featureTitle")
        sub_lbl = QLabel("实时时钟  ·  时间转换  ·  时间戳解析  ·  16 时区对照")
        sub_lbl.setStyleSheet("font-size:12px; color:#8BAF9B;")
        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_col.addWidget(title_lbl)
        title_col.addWidget(sub_lbl)
        hdr.addWidget(icon_lbl)
        hdr.addLayout(title_col)
        hdr.addStretch()
        lay.addLayout(hdr)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color:#DCF0E6;")
        lay.addWidget(div)

        tabs = QTabWidget()
        tabs.addTab(ClockTab(),   "🕐  实时时钟")
        tabs.addTab(ConvertTab(), "📅  时间转换")
        tabs.addTab(ParseTab(),   "🔢  时间戳解析")
        lay.addWidget(tabs, 1)
