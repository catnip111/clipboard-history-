# 剪贴板历史管理工具

Windows 本地剪贴板历史管理工具，记录文字和图片复制历史，支持搜索、置顶、删除，可设置保留期限。

## 技术栈

Python 3.12 + tkinter (ttkbootstrap) + SQLite

## 快速开始

```bash
pip install -r requirements.txt
python main.py
```

## 功能

- 自动记录文字和图片复制历史
- 搜索历史记录
- 置顶 / 删除记录
- 设置保留期限（1 / 3 / 5 天）

## 项目结构

```
├── main.py          # 主程序入口
├── assets/          # 资源文件
├── docs/            # 项目文档
│   ├── requirements.md   # 需求文档
│   ├── architecture.md   # 架构文档
│   ├── design-spec.md    # 设计规范
│   └── tech-stack.md     # 技术选型
└── 开发日志/         # 每日开发记录
```


第一个vibe coding出来的软件，纪念一下。