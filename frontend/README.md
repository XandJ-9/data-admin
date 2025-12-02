## 本项目前端说明

本项目前端基于 RuoYi-Vue3 进行适配，用于配合 Django + DRF 后端的“数据源管理、数据查询与查询日志”等功能。

- 运行端口：开发环境使用 `vite.config.js` 中的 `server.port = 80`
- 开发代理：`/dev-api` 代理到后端 `http://localhost:8000`
- 主要页面：
  - `系统管理`（用户、角色、菜单、字典、参数等）
  - `数据源管理`（列表维护、连通性测试）
  - `数据查询`（Tab 多页、分页、模板参数、结果列宽自适应与 tooltip 溢出显示）
  - `查询日志`（时间、用户、数据源、状态、耗时与错误信息）

### 快速开始

```bash
cd frontend
npm install
npm run dev
```

如需打包：`npm run build:prod` 或 `npm run build:stage`

## 平台简介

* 本项目前端技术栈为 [Vue3](https://v3.cn.vuejs.org) + [Element Plus](https://element-plus.org/zh-CN) + [Vite](https://cn.vitejs.dev)。
* 代码基于 RuoYi-Vue3 开源模板，已按后端接口进行业务适配。
* 阿里云折扣场：[点我进入](http://aly.ruoyi.vip)，腾讯云秒杀场：[点我进入](http://txy.ruoyi.vip)&nbsp;&nbsp;

## 前端运行

```bash
# 克隆项目
git clone https://github.com/yangzongzhuan/RuoYi-Vue3.git

# 进入项目目录
cd RuoYi-Vue3

# 安装依赖
yarn --registry=https://registry.npmmirror.com

# 启动服务
yarn dev

# 构建测试环境 yarn build:stage
# 构建生产环境 yarn build:prod
# 前端访问地址 http://localhost:80
```

## 内置功能

1.  用户管理：用户是系统操作者，该功能主要完成系统用户配置。
2.  部门管理：配置系统组织机构（公司、部门、小组），树结构展现支持数据权限。
3.  岗位管理：配置系统用户所属担任职务。
4.  菜单管理：配置系统菜单，操作权限，按钮权限标识等。
5.  角色管理：角色菜单权限分配、设置角色按机构进行数据范围权限划分。
6.  字典管理：对系统中经常使用的一些较为固定的数据进行维护。
7.  参数管理：对系统动态配置常用参数。
8.  通知公告：系统通知公告信息发布维护。
9.  操作日志：系统正常操作日志记录和查询；系统异常信息日志记录和查询。
10. 登录日志：系统登录日志记录查询包含登录异常。
*未实现功能*
* 11. 在线用户：当前系统中活跃用户状态监控。*
* 12. 定时任务：在线（添加、修改、删除)任务调度包含执行结果日志。*
* 13. 代码生成：前后端代码的生成（java、html、xml、sql）支持CRUD下载 。*
* 14. 系统接口：根据业务代码自动生成相关的api接口文档。*
* 15. 服务监控：监视当前系统CPU、内存、磁盘、堆栈等相关信息。*
* 16. 缓存监控：对系统的缓存信息查询，命令统计等。*
* 17. 在线构建器：拖动表单元素生成相应的HTML代码。*
* 18. 连接池监视：监视当前系统数据库连接池状态，可进行分析SQL找出系统性能瓶颈。*

