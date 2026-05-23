# xterm 生产构建压缩问题

本文件是 `docs/postmortem/esbuild-xterm-requestMode-bug.md` 的当前问题解决版。原 postmortem 保留完整排查过程，本文件只保留后续处理所需口径。

## 现象

前端开发模式正常，但生产构建后通过 Nginx 访问 Web Terminal，执行 `vim` 等全屏程序时终端崩溃，浏览器控制台出现 `requestMode` 相关 `ReferenceError`。

## 根因

Vite 生产构建默认使用 esbuild 压缩。esbuild 在压缩 `@xterm/xterm` 已编译代码中的 TypeScript enum IIFE 模式时，可能错误移除局部变量声明，导致 ESM 严格模式下引用未声明变量。

## 已验证无效的方向

manualChunks 隔离 xterm chunk 不能解决问题。它只改变分包，不改变 esbuild 对 xterm 模块内部代码的压缩行为。

## 正确处理方式

1. 对 `@xterm/*` 相关依赖避免使用会触发该问题的 esbuild 二次压缩路径。
2. 保持 PTY 交互式终端架构，不为了规避构建问题回退到逐命令 subprocess。
3. 修复后同时验证：
   - `pnpm dev` 下终端可交互。
   - `pnpm build` 或 `pnpm build:prod` 后终端可交互。
   - `vim`、方向键、全屏刷新和退出流程可用。

## 相关文件

- `frontend/vite.config.js`
- `frontend/src/views/terminal/`
- `backend/apps/terminal/`

## 维护建议

升级 Vite、esbuild 或 `@xterm/*` 版本后，需要重新验证生产构建终端交互，不能只看开发模式。
