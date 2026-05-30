# 技术选型说明

## 最终方案：Python + tkinter

因 Electron 存在 Windows 已知 Bug (#49034)，`require('electron')` 无法正常返回 API，
且 NW.js 在 Windows 11 Insider Build 26200 上无法启动，最终改用 Python 方案。

| 层级 | 技术 | 版本 | 选型理由 |
|------|------|------|----------|
| 语言 | Python | 3.12.10 | 稳定可靠，无浏览器引擎兼容问题 |
| UI 框架 | tkinter + ttkbootstrap | 1.20 | tkinter 内置，ttkbootstrap 提供现代化主题 |
| 剪贴板文字 | pyperclip | 1.11 | 跨平台剪贴板读写 |
| 剪贴板图片 | pywin32 + Pillow | 306 / 12.2 | Windows 原生剪贴板 + 图片处理 |
| 数据库 | sqlite3 | 内置 | Python 标准库，无需安装 |
| 系统托盘 | pystray | 0.19 | 轻量级系统托盘，支持右键菜单 |
| 全局快捷键 | keyboard | 0.13 | 全局热键监听 (Alt+V) |
| 打包 | PyInstaller | — | 一键生成 Windows .exe |

## 运行环境
- Windows 10/11
- Python 3.12+
- 无需管理员权限（快捷键可能需要）
