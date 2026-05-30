# CLAUDE.md — 剪贴板历史管理软件

## 项目概述
Windows 本地剪贴板历史管理工具，记录文字和图片复制历史，
支持搜索、置顶、删除，可设置保留期限（1/3/5天）。

## 技术栈
Python 3.12 + tkinter (ttkbootstrap) + SQLite
详见 [docs/tech-stack.md](docs/tech-stack.md)

## 标准文件路径

| 文件 | 路径 | 说明 |
|------|------|------|
| 需求文档 | [docs/requirements.md](docs/requirements.md) | 完整功能需求规格 |
| 技术选型 | [docs/tech-stack.md](docs/tech-stack.md) | 技术栈及版本说明 |
| 设计规范 | [docs/design-spec.md](docs/design-spec.md) | UI 颜色/间距/字体标准 |
| 架构文档 | [docs/architecture.md](docs/architecture.md) | 系统架构与数据流 |
| 开发步骤 | [docs/dev-checklist.md](docs/dev-checklist.md) | 阶段划分与验收清单 |
| 开发日志 | [开发日志/](开发日志/) | 每日完成 + 待办 |

## 源代码文件

| 文件 | 说明 |
|------|------|
| [main.py](main.py) | 主程序入口（窗口、托盘、快捷键、数据库全部集成） |

## 工作约定

1. **渐进开发**：每次只做一个阶段，该阶段验收通过后再开始下一个
2. **每日日志**：每次开发结束后，在 开发日志/ 下创建当日 .md 文件
3. **修改前读文件**：修改任何文件前必须先读取
4. **不跨阶段**：严格按 dev-checklist.md 的阶段顺序执行

## 启动方式

```bash
# 安装依赖
pip install pyperclip pillow pystray keyboard ttkbootstrap pywin32

# 运行
python main.py
```

## 关键配置

- 数据存储路径：`E:\剪切板历史保存\`
- 图片子目录：`E:\剪切板历史保存\images\`
- 数据库文件：`E:\剪切板历史保存\history.db`
- 快捷键：`Alt+V`
- 轮询间隔：500ms
