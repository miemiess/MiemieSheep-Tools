MAIN_STYLE = """
/* ================== Global ================== */
QMainWindow {
    background-color: #F0F7F4;
}
QWidget {
    font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 13px;
    color: #2C3E50;
}

/* ================== Header ================== */
QWidget#headerWidget {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2ECC8F, stop:0.5 #3EC78C, stop:1 #2DB57B);
    border-bottom: 2px solid #24A56B;
}
QLabel#appTitle {
    font-size: 22px;
    font-weight: bold;
    color: white;
    letter-spacing: 2px;
}
QLabel#appSubtitle {
    font-size: 11px;
    color: rgba(255,255,255,0.75);
}
QLabel#headerIcon {
    font-size: 38px;
}

/* ================== Home Page ================== */
QWidget#homePage {
    background-color: #F0F7F4;
}
QLabel#homeGreeting {
    font-size: 17px;
    font-weight: bold;
    color: #1A6B45;
}

/* ================== Feature Cards ================== */
QFrame#featureCard {
    background-color: white;
    border-radius: 18px;
    border: 2px solid #DCF0E6;
}
QFrame#featureCard:hover {
    border: 2px solid #3EC78C;
    background-color: #F5FFFB;
}
QFrame#comingSoonCard {
    background-color: #F6FAF8;
    border-radius: 18px;
    border: 2px dashed #C4D8CE;
}
QLabel#cardIcon {
    font-size: 38px;
}
QLabel#cardTitle {
    font-size: 14px;
    font-weight: bold;
    color: #1A6B45;
}
QLabel#cardDesc {
    font-size: 11px;
    color: #8BAF9B;
}
QLabel#cardIconDimmed {
    font-size: 38px;
    color: #B8CEC7;
}
QLabel#cardTitleDimmed {
    font-size: 14px;
    font-weight: bold;
    color: #9EB5AB;
}
QLabel#cardDescDimmed {
    font-size: 11px;
    color: #B8CEC7;
}

/* ================== Feature Page ================== */
QWidget#featurePage {
    background-color: #F0F7F4;
}
QWidget#topBar {
    background-color: #EDFAF3;
    border-bottom: 1px solid #D0EBE0;
}
QPushButton#backButton {
    background-color: transparent;
    color: #2ECC8F;
    border: 2px solid #2ECC8F;
    border-radius: 8px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#backButton:hover {
    background-color: #2ECC8F;
    color: white;
}
QLabel#featureTitle {
    font-size: 20px;
    font-weight: bold;
    color: #1A6B45;
}

/* ================== Progress Bar ================== */
QProgressBar {
    border: 3px solid #A8DEC2;
    border-radius: 14px;
    background-color: #EBF8F2;
    text-align: center;
    font-size: 14px;
    font-weight: bold;
    color: #1A6B45;
    min-height: 36px;
    max-height: 36px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #56CCF2, stop:0.45 #2F80ED, stop:1 #3EC78C);
    border-radius: 11px;
}

/* ================== Buttons ================== */
QPushButton#primaryButton {
    background-color: #3EC78C;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 28px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#primaryButton:hover {
    background-color: #2DB57B;
}
QPushButton#primaryButton:pressed {
    background-color: #1FA069;
}
QPushButton#primaryButton:disabled {
    background-color: #A8D5BF;
    color: #D8F0E7;
}
QPushButton#dangerButton {
    background-color: #FF6B6B;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 28px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#dangerButton:hover {
    background-color: #E85555;
}
QPushButton#dangerButton:pressed {
    background-color: #D04040;
}
QPushButton#templateButton {
    background-color: #FFB347;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#templateButton:hover {
    background-color: #FF9800;
}
QPushButton#templateButton:disabled {
    background-color: #FFD9A0;
    color: #FFF5E6;
}
QPushButton#sendButton {
    background-color: #5B9BD5;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#sendButton:hover {
    background-color: #4A8AC4;
}
QPushButton#sendButton:disabled {
    background-color: #AACCEE;
}

/* ================== Input Fields ================== */
QLineEdit {
    border: 2px solid #C8E6D5;
    border-radius: 8px;
    padding: 5px 10px;
    background-color: white;
    font-size: 13px;
    color: #2C3E50;
}
QLineEdit:focus {
    border: 2px solid #3EC78C;
    background-color: #FAFFFD;
}
QSpinBox {
    border: 2px solid #C8E6D5;
    border-radius: 8px;
    padding: 4px 8px;
    background-color: white;
    font-size: 13px;
}
QSpinBox:focus {
    border: 2px solid #3EC78C;
}
QSpinBox::up-button, QSpinBox::down-button {
    border: none;
    background: #E8F5EE;
    border-radius: 4px;
}
QTextEdit {
    border: 2px solid #C8E6D5;
    border-radius: 8px;
    padding: 6px;
    background-color: white;
    font-size: 12px;
    color: #2C3E50;
}
QTextEdit:focus {
    border: 2px solid #3EC78C;
}

/* ================== Group Box ================== */
QGroupBox {
    font-size: 13px;
    font-weight: bold;
    color: #1A6B45;
    border: 2px solid #C8E6D5;
    border-radius: 10px;
    margin-top: 8px;
    padding-top: 4px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
    background-color: #F0F7F4;
}

/* ================== Time Display ================== */
QLabel#timeLocalLabel {
    font-size: 24px;
    font-weight: bold;
    color: #1A6B45;
    letter-spacing: 1px;
}
QLabel#timeUTCLabel {
    font-size: 14px;
    color: #4A9970;
}
QLabel#timestampLabel {
    font-size: 20px;
    font-weight: bold;
    color: #5B9BD5;
    font-family: Consolas, "Courier New", monospace;
}
QLabel#timeStatusLabel {
    font-size: 16px;
    color: #7CB89C;
}

/* ================== Time Result Frame ================== */
QFrame#timeResultFrame {
    background-color: white;
    border-radius: 18px;
    border: 2px solid #DCF0E6;
}

/* ================== Battery ================== */
QLabel#batteryStatusLabel {
    font-size: 15px;
    color: #4A9970;
}

/* ================== MQTT Log ================== */
QTextEdit#logTextEdit {
    background-color: #192823;
    color: #5EF09E;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
    border: 2px solid #274035;
    border-radius: 8px;
}

/* ================== Scroll Bars ================== */
QScrollBar:vertical {
    background: #E8F5EE;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #A0D4B8;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #E8F5EE;
    height: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #A0D4B8;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ================== Dialog ================== */
QDialog {
    background-color: #F0F7F4;
}

/* ================== QTabWidget ================== */
QTabWidget::pane {
    border: 2px solid #C8E6D5;
    border-radius: 0 10px 10px 10px;
    background-color: #FAFFFE;
}
QTabBar::tab {
    background-color: #E0F2EC;
    color: #2C6E49;
    border: 2px solid #C8E6D5;
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: bold;
    margin-right: 3px;
    min-width: 80px;
}
QTabBar::tab:selected {
    background-color: #3EC78C;
    color: white;
    border-color: #3EC78C;
}
QTabBar::tab:hover:!selected {
    background-color: #C8E6D5;
}

/* ================== QDateTimeEdit ================== */
QDateTimeEdit {
    border: 2px solid #C8E6D5;
    border-radius: 8px;
    padding: 5px 10px;
    background: white;
    font-size: 13px;
    color: #2C3E50;
    font-family: Consolas, monospace;
}
QDateTimeEdit:focus {
    border: 2px solid #3EC78C;
}
QDateTimeEdit::drop-down {
    border: none;
    background: #E8F5EE;
    width: 22px;
    border-radius: 0 8px 8px 0;
}
QDateTimeEdit::up-button,
QDateTimeEdit::down-button {
    border: none;
    background: transparent;
}

/* ================== QGroupBox (time tabs) ================== */
QGroupBox {
    border: 2px solid #C8E6D5;
    border-radius: 10px;
    margin-top: 6px;
    padding: 6px 8px 8px 8px;
    font-size: 12px;
    font-weight: bold;
    color: #2C6E49;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    background-color: #F0F7F4;
}
"""
