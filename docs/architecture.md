# 架构设计文档

## 进程模型

```
┌─────────────────┐          IPC           ┌─────────────────┐
│   Main Process   │ ◄──────────────────► │ Renderer Process │
│   (Node.js)      │   contextBridge       │   (Chromium)     │
│                  │   ipcRenderer/ipcMain │                  │
│  - 剪贴板监控    │                        │  - React UI     │
│  - SQLite DB     │                        │  - 卡片列表     │
│  - 系统托盘      │                        │  - 搜索/设置    │
│  - 全局快捷键    │                        │                  │
│  - 文件系统IO   │                        │                  │
└─────────────────┘                        └─────────────────┘
```

## IPC 通道表

| 通道名称 | 方向 | 请求 | 响应 | 说明 |
|----------|------|------|------|------|
| `history:getAll` | Renderer → Main | 无 | `Array<Record>` | 获取所有历史记录 |
| `history:search` | Renderer → Main | `{ keyword: string }` | `Array<Record>` | 按关键词搜索 |
| `history:copy` | Renderer → Main | `{ id: number }` | `{ success: boolean }` | 复制到剪贴板 |
| `history:togglePin` | Renderer → Main | `{ id: number }` | `{ pinned: boolean }` | 切换置顶 |
| `history:delete` | Renderer → Main | `{ id: number }` | `{ success: boolean }` | 删除记录 |
| `settings:get` | Renderer → Main | 无 | `{ retentionDays: number }` | 获取设置 |
| `settings:set` | Renderer → Main | `{ key, value }` | `{ success: boolean }` | 更新设置 |
| `window:hide` | Renderer → Main | 无 | 无 | 隐藏面板 |

## 数据流

### 写入流程（复制内容）
```
用户 Ctrl+C → 系统剪贴板变更 → 主进程 500ms 轮询检测
  → 是否与上次内容相同？
    → 是：忽略
    → 否：判断类型 → 文字：写 content 字段
                    → 图片：写 PNG 到 images/，路径存 image_path
      → INSERT INTO clipboard_history → 完成
```

### 读取流程（查看历史）
```
用户 Alt+V → 主进程显示窗口 → 渲染进程挂载
  → ipcRenderer.invoke('history:getAll')
    → 主进程查询 SQLite（ORDER BY pinned DESC, created_at DESC）
      → 返回记录数组 → React 渲染卡片列表
```

### 粘贴流程（点击卡片）
```
用户点击卡片 → ipcRenderer.invoke('history:copy', { id })
  → 主进程查询记录 → type='text' → clipboard.writeText(content)
                    → type='image' → nativeImage.createFromPath → clipboard.writeImage
  → 返回 { success: true } → 3秒后自动隐藏面板
```

## 数据库 Schema

```sql
CREATE TABLE IF NOT EXISTS clipboard_history (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  type        TEXT NOT NULL CHECK(type IN ('text', 'image')),
  content     TEXT,
  image_path  TEXT,
  pinned      INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- 默认设置
INSERT OR IGNORE INTO settings (key, value) VALUES ('retention_days', '3');
```

## 文件存储规划

```
E:\剪切板历史保存\
├── history.db          # SQLite 数据库
└── images\             # 图片文件
    ├── 2026-05-19_143021_abc123.png
    ├── 2026-05-19_143025_def456.png
    └── ...
```

图片命名格式：`{日期}_{时间}_{随机6位}.png`
