# 咩咩羊 Tools

咩咩羊 Tools 是一款基于 PySide6 构建的桌面工具箱，提供多项实用小功能，界面简洁友好。

## 功能模块

| 模块 | 说明 |
|------|------|
| 🔋 电量检测 | 趣味动画进度条检测当前电脑电量 |
| 🕐 时间工具 | 实时时钟 + 全球多时区对照 + 时间戳双向转换 |
| 📡 MQTT 转发 | MQTT 客户端，支持自定义消息发送及 OTA 升级指令模版 |
| ✊ 石头剪刀布 | 多难度 AI 对战（Easy / Normal / Hard / mmy） |

## 环境要求

- Python 3.10+
- PySide6
- paho-mqtt
- openpyxl

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python src/main.py
```

## 打包为 EXE

确保已安装 PyInstaller：

```bash
pip install pyinstaller
```

然后执行打包脚本：

```bash
build.bat
```

或手动执行：

```bash
pyinstaller mmyTools.spec
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean mmyTools.spec
```

打包完成后，可执行文件位于 `dist/mmyTools.exe`。

## 项目结构

```
mmy_basic/
├── src/
│   ├── main.py                  # 程序入口
│   ├── ui/
│   │   └── main_window.py       # 主窗口
│   ├── features/
│   │   ├── battery/             # 电量检测
│   │   ├── time_getter/         # 时间工具
│   │   ├── mqtt_forwarder/      # MQTT 转发
│   │   └── sjb_pk/              # 石头剪刀布
│   └── resources/
│       └── styles.py            # 全局样式表
├── sheep.ico                    # 应用图标
├── mmyTools.spec                # PyInstaller 打包配置
├── build.bat                    # 一键打包脚本
└── requirements.txt
```

## License

MIT License