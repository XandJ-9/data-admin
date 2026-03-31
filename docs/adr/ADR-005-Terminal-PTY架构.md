# ADR-005: Terminal 模块 PTY 交互式架构

**Status**: Accepted  
**Date**: 2026-03-31

## Context

Web Terminal 模块最初采用 subprocess 逐命令执行方案：前端拼装完整命令行，后端 `subprocess.run()` 执行并返回 stdout/stderr。该方案存在以下问题：

1. **无交互能力**：不支持 Tab 补全、方向键历史、Ctrl+C 中断等终端交互
2. **无法运行交互式程序**：vim、top、less 等需要 TTY 的程序无法使用
3. **前后端职责混乱**：前端需自行渲染 prompt、处理行编辑、管理输入缓冲
4. **输出格式问题**：subprocess 输出 `\n` 需手动转换为 `\r\n` 以适配 xterm.js

## Decision

采用 **PTY（伪终端）+ WebSocket 直通** 架构：

### 后端（Django Channels AsyncWebsocketConsumer）

- 使用 `pty.fork()` 创建真实伪终端，spawn `/bin/zsh`
- 通过 `asyncio loop.add_reader()` 事件驱动读取 PTY 输出，替代 busy-polling
- 支持三种 WebSocket 消息类型：
  - `input`：原始按键转发到 PTY（`os.write(fd, data)`）
  - `resize`：同步窗口尺寸（`fcntl.ioctl(fd, TIOCSWINSZ, ...)`）
  - `command`：兼容旧协议，写入命令 + `\n`
- 安全审计：维护输入缓冲区，Enter 时提取命令并校验黑名单（`security.is_command_allowed()`），拦截时发送 ANSI 红色 BLOCKED 提示并 `Ctrl+U` 清除输入

### 前端（xterm.js + WebSocket）

- 所有按键通过 `term.onData()` 直接转发后端，无本地缓冲
- Shell 自行处理回显、补全、颜色输出
- 窗口 resize 时自动发送 `cols/rows` 同步 PTY 尺寸
- Tokyo Night 主题配色 + 16 色 ANSI 调色板

### WebSocket 认证

- 自定义 `JwtAuthMiddleware`：优先从 query string 读取 JWT token，降级到 session cookie
- 匿名用户拒绝连接

### 通信协议

```
前端 → 后端:
  { type: "input", data: "<raw_keystroke>" }
  { type: "resize", cols: 80, rows: 24 }
  { type: "command", data: "ls -la" }  // 兼容旧协议

后端 → 前端:
  { type: "output", data: "<pty_output>" }
  { type: "exit", code: 0 }
  { type: "error", message: "..." }
```

## Consequences

**优点**：
- 完整终端体验：Tab 补全、方向键、Ctrl+C/D、交互式程序均原生支持
- 前端极简：无需管理 prompt、行编辑、命令历史，全部由 Shell 处理
- 事件驱动 I/O：`loop.add_reader()` 高效利用 asyncio 事件循环，无 CPU 空转
- 协议向前兼容：保留 `command` 类型支持旧版前端

**缺点/风险**：
- **平台限制**：`pty.fork()` 仅支持 Unix/macOS，不可在 Windows 上运行（开发环境约束可接受）
- **资源管理**：每个 WebSocket 连接占用一个 PTY + 子进程，需关注并发连接数上限
- **安全边界**：PTY 模式下命令拦截基于输入缓冲模式匹配，存在绕过风险（如通过管道、别名），属深度防御而非绝对安全
- **进程清理**：需确保 disconnect 时正确 kill 子进程并关闭 fd，避免僵尸进程
