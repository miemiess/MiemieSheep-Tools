"""
高速转发功能模块 —— MQTT 客户端
支持自定义消息发送 + 预设模版（OTA 升级指令）
"""
import datetime
import json
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QGroupBox,
    QFormLayout, QSpinBox, QFrame, QSizePolicy,
    QFileDialog,
)
from PySide6.QtCore import Qt, QObject, Signal, QTimer

CONN_TIMEOUT_MS = 3000  # 连接超时：3 秒

# -------------------------------------------------------------------
# 模版 1：OTA 升级指令固定 Payload
# -------------------------------------------------------------------
TEMPLATE_1_PAYLOAD = json.dumps(
    {
        "cmd": "ota",
        "requestId": "ota_001",
        "data": {
            "espfileUrl": (
                "http://ql-rms.oss-cn-shenzhen.aliyuncs.com/2026-05-25/"
                "0dbd062998d743d7a5f6962add5ca6f3customer_app.bin"
            ),
            "espver": "1.1",
            "espfilesize": 170000,
            "espfilesha256": (
                "3531eeb07bf687955420d6137261c4a095ddefe6f8fef5d3b9df446053a465a0"
            ),
        },
    },
    ensure_ascii=False,
    indent=None,
)


# -------------------------------------------------------------------
# MQTT 管理器（连接超时 3 秒 + 发布结果信号）
# -------------------------------------------------------------------
class MQTTManager(QObject):
    sig_connected    = Signal()
    sig_disconnected = Signal()
    sig_log          = Signal(str)   # HTML 片段
    sig_publish_ok   = Signal()      # publish rc == 0
    sig_publish_fail = Signal()      # publish failed

    def __init__(self, parent=None):
        super().__init__(parent)
        self._client = None
        self._conn_timer = QTimer(self)
        self._conn_timer.setSingleShot(True)
        self._conn_timer.setInterval(CONN_TIMEOUT_MS)
        self._conn_timer.timeout.connect(self._on_conn_timeout)

    # ---- 连接 --------------------------------------------------------
    def connect_broker(self, host: str, port: int, client_id: str,
                       username: str, password: str, keepalive: int):
        self.disconnect_broker()
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            self.sig_log.emit(
                self._fmt("[ERROR]", "paho-mqtt 未安装，请执行: pip install paho-mqtt", "red")
            )
            self.sig_disconnected.emit()
            return
        try:
            try:
                client = mqtt.Client(
                    mqtt.CallbackAPIVersion.VERSION1,
                    client_id=client_id,
                    clean_session=True,
                )
            except AttributeError:
                client = mqtt.Client(client_id=client_id, clean_session=True)

            if username:
                client.username_pw_set(username, password or "")

            client.on_connect    = self._on_connect
            client.on_disconnect = self._on_disconnect
            client.on_message    = self._on_message

            self._client = client
            self._client.connect_async(host, port, keepalive)
            self._client.loop_start()
            self._conn_timer.start()
            self.sig_log.emit(
                self._fmt("[INFO]",
                          f"正在连接 {host}:{port}（{CONN_TIMEOUT_MS // 1000} 秒超时）...",
                          "cyan")
            )
        except Exception as exc:
            self.sig_log.emit(self._fmt("[ERROR]", f"连接异常: {exc}", "red"))
            self.sig_disconnected.emit()

    def _on_conn_timeout(self):
        self.sig_log.emit(
            self._fmt("[ERROR]",
                      f"连接超时（{CONN_TIMEOUT_MS // 1000} 秒），已自动断开，请检查地址与网络",
                      "red")
        )
        self.disconnect_broker()
        self.sig_disconnected.emit()

    # ---- 断开 --------------------------------------------------------
    def disconnect_broker(self):
        self._conn_timer.stop()
        if self._client is not None:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass
            self._client = None

    # ---- 发布 --------------------------------------------------------
    def publish(self, topic: str, payload: str):
        if self._client is None:
            self.sig_log.emit(self._fmt("[WARN]", "尚未连接到 MQTT 服务器", "orange"))
            self.sig_publish_fail.emit()
            return
        try:
            result = self._client.publish(topic, payload)
            if result.rc == 0:
                short = payload if len(payload) <= 120 else payload[:120] + "…"
                self.sig_log.emit(
                    self._fmt("[SENT ✓]",
                              f"Topic: {topic}<br>&nbsp;&nbsp;Payload: {short}",
                              "#5EF09E")
                )
                self.sig_publish_ok.emit()
            else:
                self.sig_log.emit(
                    self._fmt("[ERROR]", f"发送失败，rc={result.rc}", "red")
                )
                self.sig_publish_fail.emit()
        except Exception as exc:
            self.sig_log.emit(self._fmt("[ERROR]", f"发送异常: {exc}", "red"))
            self.sig_publish_fail.emit()

    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected()

    # ---- paho 回调（在 paho 内部线程，Qt Signal 自动跨线程安全）-------
    def _on_connect(self, client, userdata, flags, rc):
        self._conn_timer.stop()
        _CODES = {1: "协议版本错误", 2: "Client ID 无效",
                  3: "服务器不可用", 4: "用户名/密码错误", 5: "未授权"}
        if rc == 0:
            self.sig_connected.emit()
            self.sig_log.emit(self._fmt("[CONN ✓]", "成功连接到 MQTT 服务器", "#5EF09E"))
        else:
            msg = _CODES.get(rc, f"未知错误码 {rc}")
            self.sig_log.emit(self._fmt("[ERROR]", f"连接失败: {msg}", "red"))
            self.sig_disconnected.emit()

    def _on_disconnect(self, client, userdata, rc):
        self._conn_timer.stop()
        self.sig_disconnected.emit()
        if rc == 0:
            self.sig_log.emit(self._fmt("[INFO]", "已主动断开连接", "cyan"))
        else:
            self.sig_log.emit(
                self._fmt("[WARN]", f"意外断开，rc={rc}，请检查网络", "orange")
            )

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
        except Exception:
            payload = repr(msg.payload)
        self.sig_log.emit(
            self._fmt("[RECV]",
                      f"Topic: {msg.topic}<br>&nbsp;&nbsp;Payload: {payload}",
                      "#56CCF2")
        )

    @staticmethod
    def _fmt(tag: str, body: str, color: str) -> str:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        return (
            f'<span style="color:#888;">[{ts}]</span> '
            f'<span style="color:{color};font-weight:bold;">{tag}</span> '
            f'<span style="color:#C8E6D5;">{body}</span>'
        )


# -------------------------------------------------------------------
# Excel 批量管理器
# -------------------------------------------------------------------
class ExcelBatchManager:
    """读取 Excel 中 uid 列，发送成功后将对应单元格标绿保存"""

    def __init__(self):
        self._path: str | None = None
        self._wb = None
        self._ws = None
        self._uid_col: int | None = None        # 1-based 列号
        self._uid_rows: list[tuple[int, str]] = []  # (行号, uid值)

    def import_file(self, path: str) -> tuple[bool, str]:
        try:
            import openpyxl
        except ImportError:
            return False, "请先安装 openpyxl：pip install openpyxl"
        try:
            wb = openpyxl.load_workbook(path)
            ws = wb.active
            # 在第一行找 'uid' 列（不区分大小写）
            uid_col = None
            for cell in ws[1]:
                if cell.value and str(cell.value).strip().lower() == "uid":
                    uid_col = cell.column
                    break
            if uid_col is None:
                wb.close()
                return False, "第一行中未找到 'uid' 列标题，请检查 Excel 文件"
            # 从第 2 行起读取所有非空 UID
            uid_rows: list[tuple[int, str]] = []
            for row in range(2, ws.max_row + 1):
                val = ws.cell(row=row, column=uid_col).value
                if val is not None and str(val).strip():
                    uid_rows.append((row, str(val).strip()))
            if not uid_rows:
                wb.close()
                return False, "uid 列中无有效数据（第 2 行起）"
            self.reset()
            self._path    = path
            self._wb      = wb
            self._ws      = ws
            self._uid_col = uid_col
            self._uid_rows = uid_rows
            return True, f"成功读取 {len(uid_rows)} 个 UID"
        except Exception as exc:
            return False, f"读取 Excel 失败: {exc}"

    def mark_green(self, list_idx: int):
        """将第 list_idx 个 UID 单元格标绿并立即保存"""
        if self._wb is None or list_idx >= len(self._uid_rows):
            return
        try:
            from openpyxl.styles import PatternFill
            row_idx, _ = self._uid_rows[list_idx]
            cell = self._ws.cell(row=row_idx, column=self._uid_col)
            cell.fill = PatternFill(fill_type="solid", fgColor="92D050")
            self._wb.save(self._path)
        except Exception:
            pass  # 标色失败不中断主流程

    def get_uid(self, idx: int) -> str:
        return self._uid_rows[idx][1] if 0 <= idx < len(self._uid_rows) else ""

    @property
    def count(self) -> int:
        return len(self._uid_rows)

    @property
    def file_name(self) -> str:
        return os.path.basename(self._path) if self._path else ""

    def reset(self):
        if self._wb:
            try:
                self._wb.close()
            except Exception:
                pass
        self._path     = None
        self._wb       = None
        self._ws       = None
        self._uid_col  = None
        self._uid_rows = []


# -------------------------------------------------------------------
# 批量执行面板（嵌入在模版区下方）
# -------------------------------------------------------------------
_BTN_CSS = """
    QPushButton {{
        background-color: {c}; color: white; border: none;
        border-radius: 7px; padding: 3px 14px;
        font-size: 12px; font-weight: bold;
    }}
    QPushButton:hover   {{ background-color: {ch}; }}
    QPushButton:disabled {{ background-color: {cd}; color: #bbb; }}
"""


def _make_btn(text: str, hex_color: str) -> QPushButton:
    """创建统一风格的操作按钮"""
    import colorsys
    btn = QPushButton(text)
    btn.setFixedHeight(30)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    # 生成 hover / disabled 色（简单深/浅变体）
    btn.setStyleSheet(_BTN_CSS.format(c=hex_color, ch=hex_color + "CC", cd=hex_color + "55"))
    return btn


class BatchExecutionPanel(QFrame):
    """
    Excel 批量 UID → 模版 1 发送面板
    状态机: empty → imported → sending → sent_ok | sent_fail → done
    """

    def __init__(self, mqtt_mgr: "MQTTManager", parent=None):
        super().__init__(parent)
        self._mqtt       = mqtt_mgr
        self._excel      = ExcelBatchManager()
        self._idx        = 0
        self._batch_active = False   # 区分批量发送与单次发送

        self._mqtt.sig_publish_ok.connect(self._on_publish_ok)
        self._mqtt.sig_publish_fail.connect(self._on_publish_fail)
        self._mqtt.sig_connected.connect(self._refresh_start_btn)
        self._mqtt.sig_disconnected.connect(self._refresh_start_btn)

        self._setup_ui()
        self._set_state("empty")

    # ----------------------------------------------------------------
    # UI 构建
    # ----------------------------------------------------------------
    def _setup_ui(self):
        self.setObjectName("batchPanelFrame")
        self.setStyleSheet("""
            QFrame#batchPanelFrame {
                background-color: #F5FFFB;
                border-radius: 10px;
                border: 2px solid #C8E6D5;
            }
        """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 8, 12, 10)
        outer.setSpacing(6)

        # ── 标题行 ────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title_lbl = QLabel("📊  Excel 批量执行  —  模版 1 OTA 推送")
        title_lbl.setStyleSheet(
            "font-weight:bold; font-size:12px; color:#1A6B45;"
        )
        self._reimport_btn = self._small_btn("重新导入", "#5B9BD5")
        self._reimport_btn.clicked.connect(self._do_import)
        self._reimport_btn.hide()
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        hdr.addWidget(self._reimport_btn)
        outer.addLayout(hdr)

        # ── 文件 + 进度行 ─────────────────────────────────────────
        info_row = QHBoxLayout()
        self._file_lbl     = QLabel("未导入文件")
        self._file_lbl.setStyleSheet(
            "font-size:11px; color:#8BAF9B; font-family:Consolas;"
        )
        self._progress_lbl = QLabel("")
        self._progress_lbl.setStyleSheet(
            "font-size:11px; color:#5B9BD5; font-weight:bold;"
        )
        info_row.addWidget(self._file_lbl)
        info_row.addStretch()
        info_row.addWidget(self._progress_lbl)
        outer.addLayout(info_row)

        # ── 当前 UID + 状态行 ────────────────────────────────────
        uid_row = QHBoxLayout()
        uid_prefix = QLabel("当前 UID:")
        uid_prefix.setStyleSheet("font-size:12px; color:#4A9970;")
        uid_prefix.setFixedWidth(65)
        self._cur_uid_lbl = QLabel("")
        self._cur_uid_lbl.setStyleSheet(
            "font-size:13px; font-weight:bold; color:#1A6B45; font-family:Consolas;"
        )
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(
            "font-size:12px; color:#3EC78C; font-weight:bold;"
        )
        uid_row.addWidget(uid_prefix)
        uid_row.addWidget(self._cur_uid_lbl, 1)
        uid_row.addWidget(self._status_lbl)
        outer.addLayout(uid_row)

        # ── 操作按钮行 ───────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._import_btn = _make_btn("📂  导入 Excel",  "#5B9BD5")
        self._start_btn  = _make_btn("▶  开始执行",    "#3EC78C")
        self._next_btn   = _make_btn("→  下一个",      "#3EC78C")
        self._retry_btn  = _make_btn("↺  重试",        "#FFB347")
        self._skip_btn   = _make_btn("⏭  跳过",        "#9E9E9E")
        self._abort_btn  = _make_btn("■  终止",        "#FF6B6B")
        self._reset_btn  = _make_btn("🔄  重置",        "#5B9BD5")

        self._import_btn.clicked.connect(self._do_import)
        self._start_btn.clicked.connect(self._do_start)
        self._next_btn.clicked.connect(self._do_next)
        self._retry_btn.clicked.connect(self._do_retry)
        self._skip_btn.clicked.connect(self._do_skip)
        self._abort_btn.clicked.connect(self._do_abort)
        self._reset_btn.clicked.connect(self._do_reset)

        for b in (self._import_btn, self._start_btn, self._next_btn,
                  self._retry_btn, self._skip_btn, self._abort_btn, self._reset_btn):
            btn_row.addWidget(b)
        btn_row.addStretch()
        outer.addLayout(btn_row)

    # ----------------------------------------------------------------
    # 状态机
    # ----------------------------------------------------------------
    #               import reimport start next retry skip abort reset
    _STATE_VIS = {
        "empty":     (True,  False, False, False, False, False, False, False),
        "imported":  (False, True,  True,  False, False, False, False, False),
        "sending":   (False, False, False, False, False, False, False, False),
        "sent_ok":   (False, True,  False, True,  True,  False, True,  False),
        "sent_fail": (False, True,  False, False, True,  True,  True,  False),
        "done":      (False, True,  False, False, False, False, False, True ),
    }
    _STATE_MSG = {
        "empty":     ("",                        "#3EC78C"),
        "imported":  ("就绪，点击开始执行",        "#3EC78C"),
        "sending":   ("⏳ 发送中...",             "#FFB347"),
        "sent_ok":   ("✅ 发送成功，单元格已标绿", "#3EC78C"),
        "sent_fail": ("❌ 发送失败",               "#FF6B6B"),
        "done":      ("🎉 全部执行完毕！",          "#3EC78C"),
    }

    def _set_state(self, state: str):
        btns = [
            self._import_btn, self._reimport_btn, self._start_btn,
            self._next_btn,   self._retry_btn,    self._skip_btn,
            self._abort_btn,  self._reset_btn,
        ]
        for btn, vis in zip(btns, self._STATE_VIS.get(state, (False,) * 8)):
            btn.setVisible(vis)
        self._cur_uid_lbl.setVisible(state != "empty")
        # uid 前缀也只在非 empty 时显示
        text, color = self._STATE_MSG.get(state, ("", "#3EC78C"))
        self._status_lbl.setText(text)
        self._status_lbl.setStyleSheet(
            f"font-size:12px; color:{color}; font-weight:bold;"
        )

    def _refresh_start_btn(self):
        self._start_btn.setEnabled(self._mqtt.is_connected())

    @staticmethod
    def _small_btn(text: str, color: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(24)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {color};
                border: 1px solid {color}; border-radius: 5px;
                padding: 1px 8px; font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {color}22; }}
        """)
        return btn

    # ----------------------------------------------------------------
    # 事件处理
    # ----------------------------------------------------------------
    def _do_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Excel 文件", "", "Excel 文件 (*.xlsx *.xls)"
        )
        if not path:
            return
        ok, msg = self._excel.import_file(path)
        if ok:
            self._idx = 0
            self._file_lbl.setText(f"📄 {self._excel.file_name}")
            self._progress_lbl.setText(f"0 / {self._excel.count}")
            self._cur_uid_lbl.setText(self._excel.get_uid(0))
            self._reimport_btn.show()
            self._set_state("imported")
            self._refresh_start_btn()
        else:
            self._status_lbl.setText(f"❌ {msg}")
            self._status_lbl.setStyleSheet(
                "font-size:12px; color:#FF6B6B; font-weight:bold;"
            )

    def _do_start(self):
        if not self._mqtt.is_connected():
            self._status_lbl.setText("⚠️ 请先连接 MQTT 服务器")
            self._status_lbl.setStyleSheet(
                "font-size:12px; color:#FF6B6B; font-weight:bold;"
            )
            return
        self._idx = 0
        self._send_current()

    def _send_current(self):
        if self._idx >= self._excel.count:
            self._set_state("done")
            self._progress_lbl.setText(
                f"{self._excel.count} / {self._excel.count}"
            )
            return
        uid   = self._excel.get_uid(self._idx)
        topic = f"/func/4/{uid}/get"
        self._cur_uid_lbl.setText(uid)
        self._progress_lbl.setText(
            f"{self._idx + 1} / {self._excel.count}"
        )
        self._set_state("sending")
        self._batch_active = True
        self._mqtt.publish(topic, TEMPLATE_1_PAYLOAD)

    def _on_publish_ok(self):
        if not self._batch_active:
            return
        self._batch_active = False
        self._excel.mark_green(self._idx)
        # 如果是最后一个，直接进入 done
        if self._idx >= self._excel.count - 1:
            self._progress_lbl.setText(
                f"{self._excel.count} / {self._excel.count}"
            )
            self._set_state("done")
        else:
            self._set_state("sent_ok")

    def _on_publish_fail(self):
        if not self._batch_active:
            return
        self._batch_active = False
        self._set_state("sent_fail")

    def _do_next(self):
        self._idx += 1
        self._send_current()

    def _do_retry(self):
        self._send_current()

    def _do_skip(self):
        self._idx += 1
        if self._idx >= self._excel.count:
            self._set_state("done")
            self._progress_lbl.setText(
                f"{self._excel.count} / {self._excel.count}"
            )
        else:
            uid = self._excel.get_uid(self._idx)
            self._cur_uid_lbl.setText(uid)
            self._progress_lbl.setText(
                f"{self._idx + 1} / {self._excel.count}"
            )
            self._set_state("imported")

    def _do_abort(self):
        self._batch_active = False
        uid = self._excel.get_uid(self._idx)
        self._cur_uid_lbl.setText(uid)
        self._status_lbl.setText("已终止执行")
        self._status_lbl.setStyleSheet(
            "font-size:12px; color:#9E9E9E; font-weight:bold;"
        )
        self._set_state("imported")

    def _do_reset(self):
        self._batch_active = False
        self._excel.reset()
        self._idx = 0
        self._file_lbl.setText("未导入文件")
        self._progress_lbl.setText("")
        self._cur_uid_lbl.setText("")
        self._reimport_btn.hide()
        self._set_state("empty")


# -------------------------------------------------------------------
# MQTT 页面 Widget
# -------------------------------------------------------------------
class MQTTWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("featurePage")
        self._mqtt = MQTTManager(self)
        self._mqtt.sig_connected.connect(self._on_connected)
        self._mqtt.sig_disconnected.connect(self._on_disconnected)
        self._mqtt.sig_log.connect(self._append_log)
        self._connected = False
        self._batch_panel: BatchExecutionPanel | None = None
        self._setup_ui()

    # ----------------------------------------------------------------
    # UI 构建
    # ----------------------------------------------------------------
    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(18, 10, 18, 14)
        main.setSpacing(10)

        # ---- 标题行 ------------------------------------------------
        title_row = QHBoxLayout()
        icon_lbl = QLabel("📡")
        icon_lbl.setStyleSheet("font-size: 26px;")
        title_lbl = QLabel("高速转发  —  MQTT 客户端")
        title_lbl.setObjectName("featureTitle")
        title_row.addWidget(icon_lbl)
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        main.addLayout(title_row)

        # ---- 连接配置 Group ----------------------------------------
        conn_grp = QGroupBox("⚙️  连接配置")
        conn_layout = QHBoxLayout(conn_grp)
        conn_layout.setSpacing(14)

        # 左列表单
        left_form = QFormLayout()
        left_form.setSpacing(6)
        left_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._host_edit = QLineEdit("broker.emqx.io")
        self._host_edit.setPlaceholderText("MQTT Broker 地址")
        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(1883)
        self._port_spin.setFixedWidth(90)
        self._cid_edit = QLineEdit()
        self._cid_edit.setPlaceholderText("留空则自动生成")
        left_form.addRow("Broker:", self._host_edit)
        left_form.addRow("端口:", self._port_spin)
        left_form.addRow("Client ID:", self._cid_edit)

        # 右列表单
        right_form = QFormLayout()
        right_form.setSpacing(6)
        right_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText("用户名（可选）")
        self._pass_edit = QLineEdit()
        self._pass_edit.setPlaceholderText("密码（可选）")
        self._pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._ka_spin = QSpinBox()
        self._ka_spin.setRange(1, 3600)
        self._ka_spin.setValue(60)
        self._ka_spin.setFixedWidth(90)
        right_form.addRow("用户名:", self._user_edit)
        right_form.addRow("密码:", self._pass_edit)
        right_form.addRow("心跳(s):", self._ka_spin)

        # 状态 + 按钮列
        ctrl_col = QVBoxLayout()
        ctrl_col.setSpacing(10)

        status_row = QHBoxLayout()
        self._dot_lbl = QLabel("⚫")
        self._dot_lbl.setStyleSheet("font-size: 16px;")
        self._status_lbl = QLabel("未连接")
        self._status_lbl.setStyleSheet("font-size: 13px; color: #7CB89C;")
        status_row.addWidget(self._dot_lbl)
        status_row.addWidget(self._status_lbl)
        status_row.addStretch()

        self._conn_btn = QPushButton("🔌  连接")
        self._conn_btn.setObjectName("primaryButton")
        self._conn_btn.setFixedWidth(110)
        self._conn_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._conn_btn.clicked.connect(self._toggle_connection)

        ctrl_col.addLayout(status_row)
        ctrl_col.addWidget(self._conn_btn)
        ctrl_col.addStretch()

        conn_layout.addLayout(left_form, 4)
        conn_layout.addLayout(right_form, 4)
        conn_layout.addLayout(ctrl_col, 3)
        main.addWidget(conn_grp)

        # ---- 发送区 + 模版区（横向并排）-----------------------------
        mid_row = QHBoxLayout()
        mid_row.setSpacing(10)

        # 自定义发送
        send_grp = QGroupBox("📤  自定义发送")
        send_layout = QVBoxLayout(send_grp)
        send_layout.setSpacing(6)

        topic_row = QHBoxLayout()
        topic_lbl = QLabel("主题:")
        topic_lbl.setFixedWidth(42)
        self._topic_edit = QLineEdit()
        self._topic_edit.setPlaceholderText("输入发布主题")
        topic_row.addWidget(topic_lbl)
        topic_row.addWidget(self._topic_edit)

        self._msg_edit = QTextEdit()
        self._msg_edit.setPlaceholderText("输入消息内容（支持 JSON）...")
        self._msg_edit.setMaximumHeight(70)

        self._send_btn = QPushButton("⚡  发送")
        self._send_btn.setObjectName("sendButton")
        self._send_btn.setEnabled(False)
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.clicked.connect(self._send_custom)

        send_btn_row = QHBoxLayout()
        send_btn_row.addStretch()
        send_btn_row.addWidget(self._send_btn)

        send_layout.addLayout(topic_row)
        send_layout.addWidget(self._msg_edit)
        send_layout.addLayout(send_btn_row)

        # 模版区
        tpl_grp = QGroupBox("📋  消息模板")
        tpl_layout = QVBoxLayout(tpl_grp)
        tpl_layout.setSpacing(8)

        uid_row = QHBoxLayout()
        uid_lbl = QLabel("设备 UID:")
        uid_lbl.setFixedWidth(65)
        self._uid_edit = QLineEdit()
        self._uid_edit.setPlaceholderText("输入目标设备 UID")
        uid_row.addWidget(uid_lbl)
        uid_row.addWidget(self._uid_edit)

        # 实时预览目标主题
        self._tpl1_topic_lbl = QLabel("主题: /func/4/{UID}/get")
        self._tpl1_topic_lbl.setStyleSheet(
            "font-size: 11px; color: #5B9BD5; font-family: Consolas;"
        )
        self._uid_edit.textChanged.connect(self._update_tpl1_topic)

        tpl1_desc = QLabel("模版 1：OTA 固件升级指令")
        tpl1_desc.setStyleSheet("font-size: 11px; color: #8BAF9B;")

        self._tpl1_btn = QPushButton("🚀  发送模版 1")
        self._tpl1_btn.setObjectName("templateButton")
        self._tpl1_btn.setEnabled(False)
        self._tpl1_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._tpl1_btn.clicked.connect(self._send_template_1)

        tpl_layout.addLayout(uid_row)
        tpl_layout.addWidget(self._tpl1_topic_lbl)
        tpl_layout.addWidget(tpl1_desc)
        tpl_layout.addWidget(self._tpl1_btn)
        tpl_layout.addStretch()

        mid_row.addWidget(send_grp, 6)
        mid_row.addWidget(tpl_grp, 4)
        main.addLayout(mid_row)

        # ---- 批量执行面板 — 常显，初始为 empty 状态 --------
        self._batch_panel = BatchExecutionPanel(self._mqtt, self)
        main.addWidget(self._batch_panel)

        # ---- 日志区 ------------------------------------------------
        log_grp = QGroupBox("🖥️  消息日志")
        log_layout = QVBoxLayout(log_grp)
        log_layout.setContentsMargins(6, 4, 6, 6)
        log_layout.setSpacing(4)

        log_header = QHBoxLayout()
        log_header.addStretch()
        clr_btn = QPushButton("清空")
        clr_btn.setFixedWidth(58)
        clr_btn.setStyleSheet("""
            QPushButton {
                background: #274035;
                color: #5EF09E;
                border: 1px solid #3A6050;
                border-radius: 5px;
                padding: 2px 6px;
                font-size: 11px;
            }
            QPushButton:hover { background: #3A5045; }
        """)
        clr_btn.clicked.connect(self._clear_log)
        log_header.addWidget(clr_btn)

        self._log_edit = QTextEdit()
        self._log_edit.setObjectName("logTextEdit")
        self._log_edit.setReadOnly(True)
        self._log_edit.setMinimumHeight(110)
        self._log_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        log_layout.addLayout(log_header)
        log_layout.addWidget(self._log_edit)
        main.addWidget(log_grp, 1)

    # ----------------------------------------------------------------
    # 事件处理
    # ----------------------------------------------------------------
    def _update_tpl1_topic(self, uid: str):
        uid_part = uid if uid else "{UID}"
        self._tpl1_topic_lbl.setText(f"主题: /func/4/{uid_part}/get")

    def _toggle_connection(self):
        if self._connected:
            self._mqtt.disconnect_broker()
        else:
            host = self._host_edit.text().strip()
            if not host:
                self._append_log(MQTTManager._fmt("[WARN]", "请填写 Broker 地址", "orange"))
                return
            self._conn_btn.setEnabled(False)
            self._conn_btn.setText("连接中...")
            self._mqtt.connect_broker(
                host=host,
                port=self._port_spin.value(),
                client_id=self._cid_edit.text().strip(),
                username=self._user_edit.text().strip(),
                password=self._pass_edit.text(),
                keepalive=self._ka_spin.value(),
            )

    def _on_connected(self):
        self._connected = True
        self._dot_lbl.setText("🟢")
        self._status_lbl.setText("已连接")
        self._conn_btn.setText("🔌  断开")
        self._conn_btn.setEnabled(True)
        self._conn_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B; color: white;
                border: none; border-radius: 10px;
                padding: 10px 20px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #E85555; }
        """)
        self._send_btn.setEnabled(True)
        self._tpl1_btn.setEnabled(True)

    def _on_disconnected(self):
        self._connected = False
        self._dot_lbl.setText("⚫")
        self._status_lbl.setText("未连接")
        self._conn_btn.setText("🔌  连接")
        self._conn_btn.setEnabled(True)
        self._conn_btn.setStyleSheet("")
        self._send_btn.setEnabled(False)
        self._tpl1_btn.setEnabled(False)

    def _send_custom(self):
        topic = self._topic_edit.text().strip()
        msg = self._msg_edit.toPlainText().strip()
        if not topic:
            self._append_log(MQTTManager._fmt("[WARN]", "请输入发布主题", "orange"))
            return
        if not msg:
            self._append_log(MQTTManager._fmt("[WARN]", "消息内容不能为空", "orange"))
            return
        self._mqtt.publish(topic, msg)

    def _send_template_1(self):
        uid = self._uid_edit.text().strip()
        if not uid:
            self._append_log(MQTTManager._fmt("[WARN]", "请输入设备 UID", "orange"))
            return
        topic = f"/func/4/{uid}/get"
        self._mqtt.publish(topic, TEMPLATE_1_PAYLOAD)

    def _append_log(self, html_line: str):
        self._log_edit.append(html_line)
        sb = self._log_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear_log(self):
        self._log_edit.clear()
