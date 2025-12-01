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
