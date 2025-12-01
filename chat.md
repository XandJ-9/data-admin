## 数据查询
*目标：前端数据查询-支持新增查询页，每个查询页面相互独立，查询页面的功能*
代码位置：
- 前端：frontend/src/views/datasource/query/
- 后端：backend/apps/datasource

*需求描述*
1. 用户点击数据查询菜单进入数据查询页面，查询页面以tab的形式展示，每个tab对应一个查询页面，最后一个tab为新增查询按钮。
2. 用户点击新增查询按钮，在当前页面新增一个tab，并切换到该tab，用户可以重新选择数据源，编辑查询语句，点击执行查询，查询结果展示在当前tab页面。

*输出要求*
对应前端代码位置
- 进入查询页面(frontend/src/views/datasource/query/index.vue)
- index.vue页面中以tab形式展示多个查询页面，最后一个tab为新增查询按钮
- 查询页面代码拆分：
    queryView.vue: 选择数据源，编辑查询语句，执行查询， 分页查询下一页数据，查看上一页结果
    queryResult.vue：显示查询结果, 查询结果使用el-table组件展示，但是需要根据数据内容调整列宽度，参考方法： frontend\src\utils\index.js 中的 calculateColumnWidth 方法
- 后端查询接口方法为： DataSourceViewSet.query_by_id

*统一规范：*
- 适配现有的代码风格


## 数据查询日志记录
*目标：记录用户在数据查询页面执行的查询语句，包括查询时间，查询语句，查询用户名， 查询结果状态（成功或失败），查询耗时等信息*
代码位置：
- 后端：backend/apps/datasource/models.py
- 数据库表：datasource_query_log
- 前端：frontend/src/views/datasource/query/queryLog.vue

*需求*
- 用户在数据查询页面执行查询后，查询日志记录在数据库中，包括查询时间，查询语句，查询用户名， 查询结果状态（成功或失败），查询耗时等信息。
- 用户可以在查询日志页面查看所有查询记录，包括查询时间，查询语句，查询用户名， 查询结果状态（成功或失败），查询耗时等信息。

*统一规范：*
- 适配现有的代码风格，使用一致的命名约定，使用一致的代码风格。