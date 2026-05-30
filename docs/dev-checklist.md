# 开发步骤与阶段验收清单

## 阶段 1：项目骨架搭建

### 任务清单
- [ ] 初始化 npm 项目（`npm init`）
- [ ] 安装依赖：electron, react, react-dom, vite, @vitejs/plugin-react, better-sqlite3, electron-builder
- [ ] 创建 `electron/main.js`（最小 Electron 启动）
- [ ] 创建 `src/index.html` + `src/main.jsx` + `src/App.jsx`（最小 React 渲染）
- [ ] 配置 `vite.config.js`
- [ ] 配置 `package.json` scripts（dev / build）
- [ ] 创建 `docs/` 所有标准文档
- [ ] 创建 `开发日志/` 文件夹
- [ ] 编写 `CLAUDE.md`

### 验收条件
- `npm run dev` 能成功启动 Electron 窗口
- 窗口中显示 React 渲染的 "Hello Clipboard History"

---

## 阶段 2：数据库 + 剪贴板监控

### 任务清单
- [ ] 编写 `electron/database.js`（初始化、建表、CRUD）
- [ ] 编写 `electron/clipboard-monitor.js`（500ms 轮询、去重）
- [ ] 在 `main.js` 中集成数据库和剪贴板监控
- [ ] 确认数据写入 `E:\剪切板历史保存\`

### 验收条件
- 复制一段文字后，用 SQLite 工具查看 `history.db`，确认记录存在
- 复制图片后，`E:\剪切板历史保存\images\` 下有对应的 PNG 文件

---

## 阶段 3：系统托盘 + 全局快捷键

### 任务清单
- [ ] 编写 `electron/tray.js`（托盘图标、右键菜单）
- [ ] 在 `main.js` 中注册 `Alt+V` 全局快捷键
- [ ] 双击托盘图标弹出历史面板
- [ ] 编写 `electron/ipc-handlers.js`（基础 IPC 通道）

### 验收条件
- 软件启动后系统托盘显示图标
- 右键菜单有三个选项（打开历史/设置/退出）且可点击
- 按 `Alt+V` 弹出历史面板窗口
- 双击托盘图标也弹出窗口

---

## 阶段 4：历史面板 UI（只读）

### 任务清单
- [ ] 编写 `electron/preload.js`（暴露安全 API）
- [ ] 编写 `src/App.css`（全局样式 + 主题变量）
- [ ] 编写 `src/components/SearchBar.jsx`
- [ ] 编写 `src/components/EmptyState.jsx`
- [ ] 编写 `src/components/ClipboardCard.jsx`
- [ ] 编写 `src/components/CardList.jsx`
- [ ] 编写 `src/hooks/useClipboard.js`
- [ ] 组装 `src/App.jsx`

### 验收条件
- 面板正确展示所有历史记录
- 列表按时间降序排列
- 置顶卡片排在最上方，带有视觉标识
- 文字卡片显示内容预览，图片卡片显示缩略图

---

## 阶段 5：交互功能

### 任务清单
- [ ] 点击文字卡片 → 写入剪贴板 → 面板隐藏
- [ ] 点击图片卡片 → 写入剪贴板 → 面板隐藏
- [ ] 置顶/取消置顶按钮功能
- [ ] 删除按钮功能（确认弹窗 + 删除图片文件）
- [ ] 搜索框实时过滤

### 验收条件
- 点击文字卡片后，Ctrl+V 能粘贴到其他地方
- 点击图片卡片后，Ctrl+V 能粘贴图片
- 置顶按钮切换正常
- 删除后记录消失，图片文件也被清除
- 搜索输入后列表实时过滤，匹配关键词

---

## 阶段 6：设置面板 + 自动清理

### 任务清单
- [ ] 编写 `src/components/SettingsPanel.jsx`
- [ ] 实现保留天数读取/写入（SQLite settings 表）
- [ ] 在 `main.js` 中实现启动时清理
- [ ] 实现每小时定时清理（setInterval）
- [ ] 设置面板入口（托盘右键菜单或面板内按钮）

### 验收条件
- 设置面板可切换 1/3/5 天
- 切换后立即生效，下次启动仍保持
- 启动时自动删除过期记录
- 每小时自动检查并清理

---

## 阶段 7：打包 + 最终测试

### 任务清单
- [ ] 配置 `electron-builder`（NSIS 安装包）
- [ ] 创建应用图标 `assets/icon.png`
- [ ] 运行 `npm run build` 生成 .exe
- [ ] 在干净环境安装测试
- [ ] 完整验收清单全部通过

### 验收条件
- 生成的 .exe 安装包可正常安装
- 安装后可启动，所有功能正常
- 卸载后无残留文件
- 完整验证清单全部通过
