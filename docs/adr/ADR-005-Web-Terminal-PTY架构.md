# ADR-005: Web Terminal PTY 架构

**状态**: Accepted  
**日期**: 2026-05-22

## 背景

Web Terminal 需要支持真实交互式终端体验，包括 Tab 补全、方向键、Ctrl+C、`vim`、`top`、`less` 等依赖 TTY 的程序。逐命令 `subprocess.run` 模式无法满足这些能力，并且会让前端承担 prompt、行编辑和输出格式处理等不该承担的职责。

## 决策

Terminal 模块采用 PTY + WebSocket 直通架构。

### 后端

后端使用 Django Channels WebSocket Consumer 管理终端会话。

核心行为：

- 为每个连接创建一个 PTY 进程。
- Unix/macOS 默认启动 `$SHELL --login`。
- Windows 场景使用兼容 PTY 实现。
- 前端输入原样写入 PTY。
- PTY 输出原样推送给前端。
- resize 消息同步窗口尺寸。
- disconnect 时清理子进程和 PTY。

### 前端

前端使用 xterm.js：

- `term.onData()` 将原始按键发送给后端。
- Shell 自己负责回显、补全、颜色和行编辑。
- 窗口尺寸变化时发送 cols / rows。

### 通信协议

前端到后端：

```json
{ "type": "input", "data": "<raw_keystroke>" }
```

```json
{ "type": "resize", "cols": 120, "rows": 32 }
```

后端到前端：

```json
{ "type": "output", "data": "<pty_output>" }
```

```json
{ "type": "exit", "code": 0 }
```

```json
{ "type": "error", "message": "..." }
```

## 安全约束

1. WebSocket 必须校验登录态或 JWT。
2. Terminal 只作为研发辅助入口，不承担任务调度或数据开发执行器职责。
3. 命令审计和危险命令控制属于纵深防御，不能视为绝对沙箱。
4. 后续远程主机能力必须补齐授权、审计和隔离策略。

## 构建约束

xterm 生产构建压缩问题按 `docs/troubleshooting/esbuild-xterm-requestMode-bug.md` 处理。不得为了规避构建问题回退到逐命令 subprocess 架构。

## 影响

1. 终端体验接近真实 shell。
2. 前端保持薄封装，不实现本地命令行编辑器。
3. 每个连接会占用 PTY 和子进程，需要关注并发与资源回收。
4. 安全边界必须持续通过权限、审计和隔离增强。

## 相关文档

- `docs/architecture/modules/terminal.md`
- `docs/troubleshooting/esbuild-xterm-requestMode-bug.md`
