# SY陪练助手 本地版

一个完全本地运行的 Windows 连招录制、编辑、练习和回放工具。项目已去掉联网授权、登录校验和激活码逻辑，启动后直接读取本地连招文件。

## 功能

- 本地读取和保存 `.combo.json` 连招文件
- 全局键鼠录制、停止和回放
- 连招步骤表格编辑
- 时间轴预览
- 悬浮窗显示
- 练习模式提示
- F1-F12 快捷键可配置
- 默认附带本地连招数据

## 运行

环境要求：

- Windows
- Python 3.10+
- PySide6

启动方式：

```bat
run_local.bat
```

或者：

```bash
python app.py
```

如果当前 Python 环境没有 PySide6，可以先执行：

```bash
python -m pip install -r requirements.txt
```

## 目录

- `app.py`：主程序
- `run_local.bat`：本地启动脚本
- `requirements.txt`：依赖说明
- `assets/`：图标和提示音
- `连招/`：本地连招数据

## 说明

- 程序默认读取当前目录下的 `连招` 文件夹。
- 配置文件 `combo_coach_settings.json` 会在本地运行后自动生成，不会提交到仓库。
- 如果全局键鼠录制或回放被系统拦截，请尝试以管理员身份运行。

## 许可证

MIT License

