# 项目功能
- 数据源管理模块 → 集成数据源连接信息，提供数据源连接测试，数据查询，查询日志；
- 元数据管理模块 → 基于已纳管的数据源，自动采集库、表、字段信息（依赖数据源的连接信息）；
- 数据资产目录模块 → 基于元数据，构建资产分类、标签、画像（依赖元数据）；
- 数据质量模块 → 针对资产目录中的表，配置质量规则、定时检测（依赖资产目录）；
- 数据血缘模块 → 基于元数据和 ETL 日志，解析表 / 字段级血缘（依赖元数据）；
- 数据权限模块 → 细化到表 / 字段级的权限控制（复用系统管理 + 数据源的权限基础）。




# 数据源管理模块
## 数据源管理-支持presto,starrocks等数据库
*需求*
    支持presto,starrocks等数据库

*注意*
- 基于现有的数据库查询执行器来修改 
- 不要添加重复功能的代码
- 参考：backend/apps/dbutil/目录下的代码结构



# 数据资产目录模块

## 数据总览
*需求*
- 用户可以在数据总览页面查看已纳入的数据表
- 用户点击对应的数据表，可以查看到该表的字段信息。
- 用户可以筛选的字段：数据表名，数据库名，创建时间，修改时间

代码位置：
- 后端：backend/apps/datameta
- 前端：frontend/src/views/datameta/index.vue

主要类：
- MetaTableViewSet：元数据表管理视图类。
- MetaColumnViewSet：元数据字段管理视图类。

*统一规范：*
- 适配现有的代码风格
- 参考后端开发规范（backend/开发规范.md）

### 数据总览功能更新
- 源数据表的增删改操作，用户可以在数据总览页面对源数据表进行增删改操作。


### 元数据管理页面功能更新
*需求：扩充采集的元数据信息*

*功能修改*
- 采集的元数据表信息包括表名，表描述，原始数据库，创建同步时间，修改同步时间，采集人（用户名），更新者（用户名）
- 采集的元数据字段信息包括字段名，字段描述，字段类型，是否主键，是否非空，默认值
- 源数据表查询结果分页展示

*代码位置*
- 前端：frontend/src/views/datameta/index.vue
- 后端：backend/apps/datameta/views.py

*注意*
- 不要编写重复功能的方法，先考虑是否有已有的方法可以实现该功能，再编写新的方法。

*统一规范：*
- 适配现有的代码风格
- 参考后端开发规范（backend/开发规范.md）



## 原始数据源业务数据查看
*目标：用户可以查看选择数据源中所有的业务表*

*需求*
- 新增一个业务数据查看页面，用户可以在该页面查看选择数据源中所有的业务表。
- 点击业务业务数据表可以查看该表的字段信息
- 在每个业务表信息中添加一个采集按钮，点击按钮可以触发所选业务表的元数据采集

*统一规范：*
- 参考前端代码目录结构，将业务数据查看页面放置在frontend/src/views/datameta/businessData目录下
- 后端代码考虑代码的复用性，将业务数据查看相关的代码放置在backend/apps/datameta/views.py文件中

### 业务数据查看页面功能更新
*需求：支持筛选业务表名*

*功能描述*
- 用户在选择数据源后，业务数据查看页面会显示该数据源下所有的业务表（后端返回所有的数据表信息）。
- 用户可以在筛选框中输入表名，筛选出包含该表名的业务表(前端实现筛选)。
- 尽可能多的显示业务数据表的信息，例如：表名称，数据库名称，表描述，表创建时间，表修改时间，表创建时间

*代码位置*
- 前端：frontend/src/views/datameta/businessData/index.vue
- 后端：backend/apps/datameta/views.py
- 在数据查询执行器中添加一个方法list_tables_info，用来获取数据源下所有数据表信息，该方法需要返回数据表信息，例如：表名称，数据库名称，表描述，表创建时间，表修改时间，表创建时间

*统一规范：*
- 适配现有的代码风格

### 业务数据查看功能更新2.0
*背景*
  在多租户场景下，在每个数据源实例下，同时又多个数据库实例，例如：mysql实例下有多个数据库实例，每个数据库实例下有多个数据表， 每一个数据库代表一个租户的数据库，租户之间的数据是隔离的。

*需求描述*
- 选择对应的数据源实例后，根据所选数据源的不同数据源类型，会有不同的逻辑
    如果是mysql,则还会有数据库的选择框来筛选对应的数据库，选择完数据库后才可以获取数据表信息；
    如果是postgresql,则直接获取所有数据表信息

*代码实现*
- 后端代码位置：backend/apps/dbutils/
- 添加数据库查询方法：get_databases(self, ds)， 对于没有数据概念的数据源，该方法返回None
- 后端数据库查询接口如果返回的数据库信息为None，则前端不显示数据库选择框，否则显示数据库选择框
- 前端代码位置：frontend/src/views/datameta/businessData/index.vue

### 业务数据查看功能更新3.0
*需求*
  在数据查询执行器中的get_table_schema方法中，返回的字段信息中，补充字段的描述信息


## 数据访问执行器功能更新
*需求*
  在数据查询执行器中的get_table_schema方法中，返回的字段信息中，补充字段的序号（从1开始）

*要求*
- 序号字段名为：order
- 前后端都需要根据order字段进行排序



# 数据服务模块
*背景*
- 数据服务模块是数据资产管理平台的一个子模块，负责提供数据查询服务。
  

*需求*
- 现有代码中将数据查询放到了数据源模块中，导致数据源模块的功能过于复杂。因此，需要将数据查询功能从数据源模块中分离出来，放到数据服务模块中。
- 目前数据服务模块的前端目录尚未创建，需要创建目录后，将数据查询相关的代码放置在该目录下。
- 数据服务模块的前端目录结构如下：
    - frontend/src/views/dataservice/index.vue
    - frontend/src/views/dataservice/query/index.vue
    - frontend/src/views/dataservice/query/queryView.vue
    - frontend/src/views/dataservice/query/queryResult.vue
- 后端代码暂时请不要修改

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


### 数据查询支持django模板语法
*目标：在数据查询语句中支持django模板语法，用户可以在查询语句中使用django模板语法，例如：{{ var }}，{% if %}，{% for %}等*
*实现：*
- 前端：在查询语句输入框中添加django模板语法提示，用户可以选择是否添加模板参数，通过新增一个模板参数按钮，弹窗输入模板参数
- 后端：在执行查询语句时，使用django的模板引擎渲染查询语句，替换其中的变量和表达式。
    - 前端传递查询语句和参数到后端时，需要将查询语句和参数封装在一个字典中，例如：{'sql': 'select * from {{ table }}', 'params': {'table': 'user'}}
    - 后端在执行查询语句前，需要使用django的模板引擎渲染查询语句，替换其中的变量和表达式，例如：render_string('select * from {{ table }}', {'table': 'user'})
    - 后端执行查询语句后，将查询结果返回给前端。

*注意*
在后端DataSourceViewSet.query_by_id方法中使用了params参数来传递参数给查询执行器，但是这是不需要的，请修改代码，使该参数来接收前端传递的模板参数

*统一规范：*
- 适配现有的代码风格，使用一致的命名约定，使用一致的代码风格。

### 数据查询支持模板参数优化
*需求*
- 用户在数据查询页面添加模板参数后，需要展示出来方便用户检查
- 如果没有模板参数，则什么都不展示，否则展示模板参数
- 不要影响用户正常使用查询功能，简洁不影响用户体验



### 数据查询编辑框优化
*目标：优化数据查询语句编辑框，支持多行输入，添加语法高亮，自动补全等功能*
代码位置：
- 前端：frontend/src/views/datasource/query/queryView.vue

*需求*
- 数据查询语句编辑框支持多行输入，用户可以在编辑框中输入多行查询语句。
- 数据查询语句编辑框添加语法高亮，用户可以在编辑框中查看查询语句的语法高亮效果。
- 数据查询语句编辑框添加自动补全功能，用户可以在编辑框中输入查询语句时，根据已输入的内容自动补全查询语句。

*要求*
- 编写可复用的编辑框组件，支持多种语法， 组件位置放置在 frontend/src/components/目录下
- 参考components目录下的结构

*统一规范：*
- 适配现有的代码风格，使用一致的命名约定，使用一致的代码风格。

*继续优化CodeEditor组件*
- 使用vue3-ace-editor组件替换当前的CodeEditor组件，该组件支持vue3，并且有更好的性能和功能。

### 数据查询功能更新
*需求*
- 增加一个数据查询结果导出按钮，我需要将查询的结果导出
- 点击导出时，会执行查询语句，查询前10000行数据
- 导出文件格式为csv文件

*更新代码位置*
- 前端：frontend/src/views/dataservice/query/index.vue
- 后端：backend/apps/dataservice/views.py中DataQQueryServiceView.export方法

*注意事项*
- 可以参考InterfaceInfoViewSet.export_by_id方法的风格，但是不要完全一样
- 其他前端风格保持一致

## 查询日志
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

*更新功能*
- 查询日志添加错误信息

### 数据服务模块后端更新
*背景*
  原有数据查询的后端接口是放在datasource应用下，为了将数据查询功能从数据源模块中分离出来，放到数据服务模块中，需要将数据查询相关的后端代码从datasource应用中迁移到dataservice应用中。

*需求*
- 新增一个数据服务模块的后端应用dataservice，将数据查询相关的后端代码迁移到dataservice应用中。
- 数据查询相关的后端借口url修改 例如：/dataservice/query/
- 数据查询日志相关的后端接口url修改 例如：/dataservice/query-log/
- 前端请求的api放置在新的js文件中，命名为dataservice.js, 位置为：frontend/src/api/dataservice.js



### 数据报表接口管理
*背景*
- 数据报表接口管理模块是数据服务对外提供数据的功能实现，负责管理数据接口的定义，包括新增，编辑，删除数据接口。这个报表接口是一个http接口，用户可以通过该接口查询数据。

*需求*
- 新增一个数据接口管理页面，用户可以在该页面查看所有的数据接口。
- 数据接口管理页面展示数据接口的名称，描述，接口地址，请求方法，请求参数，响应参数，响应示例等信息。
- 用户可以在数据接口管理页面中添加新的数据接口，编辑已有的数据接口，删除数据接口。

报表接口定义：
- 接口编码： 每个报表接口都有一个唯一的编码，用于标识该接口。
- 接口名称： 报表接口的名称，用于描述该接口的功能。
- 接口描述： 对报表接口的详细描述，包括功能、输入参数、输出参数等。
- 接口地址： 报表接口的http地址，用户通过该地址访问接口。
- 请求方法： 报表接口的http请求方法，通常为GET或POST。
- 请求参数： 报表接口的http请求参数，包括路径参数、查询参数、请求体参数等。
- 响应参数： 报表接口的http响应参数，包括状态码、响应头、响应体等。
- 响应示例： 报表接口的http响应示例，用于展示接口返回的数据格式。


实现建议
- 后端：在 `backend/apps/dataservice` 下实现接口定义模型、CRUD API、执行路由 `/data-api/{code}`。参数校验可用 Pydantic 或基于 JSON Schema；查询层使用参数化绑定避免注入；统一中间件处理鉴权、限流、审计、CORS；响应封装统一结构。
- 前端：在 `frontend/src/views` 新增“数据报表接口管理”页面，列表 + 详情/编辑弹窗；参数定义采用动态表单；提供“试运行”并展示响应与耗时；支持定义的导入/导出（JSON）。
  




## 数据接口
*背景*
  参考以下给出的对接口定义，帮我在dataservice应用中添加数据接口的管理功能

*需求*
- 接口信息的增删改查管理
- 接口编辑单独一个页面
- 点击接口信息查看接口明细
  

### 数据服务-数据接口功能更新
*需求*
  根据后端数据接口（Interface）的实现，完成前端对应的页面

*代码位置*
- 后端：backend/apps/dataservice/
- 前端：frontend/src/views/dataservice/interface

*其它注意事项*
- 遵循最小修改原则
- 统一前端风格

### 数据服务-数据接口功能更新2.0
**新增功能**
- 数据接口管理页面新增“测试连接”按钮，点击可测试接口是否能正常连接数据库
- 数据接口管理页面新增“执行查询”按钮，点击可在数据库执行接口定义的SQL语句
- 数据接口管理页面新增“导出数据”按钮，点击可将查询结果导出为CSV文件


### 数据接口信息导出到excel
*需求*
  提供接口信息导出到excel中，包含基本的接口信息和接口的字段信息

*要求*
- 基于现有代码结构，在dataservice.views.InterfaceInfoViewSet类中添加导出接口信息的接口方法
- 复合当前后端项目的开发规范
- 前端在接口操作处添加一个导出按钮

*注意*
- 复合项目的整体代码风格
- 遵循最小修改原则


# 管理监控monitor模块
*需求*
- 系统运行过程中，需要能够实时知道系统相关的信息，请参考现有的前端代码完后后端的功能实现

*代码位置*
- 前端：frontend/src/views/monitor/

*开发要求*
- 后端新建应用monitor,负责对应前端的功能
- 只需要实现指定的对应功能即可，不要多做
- 功能实现要求循序渐进，按如下顺序
  - 服务器信息（server）
  - 在线用户（online）
  - 操作日志（log）

## 操作日志功能
*需求*
    系统操作日志记录，用于记录系统操作情况，方便后续分析和优化

*开发要求*
- 后端参看OperLog模型，创建一个中间件(monitor/middleware.py)来记录用户的请求操作
  
*注意*
- 遵循最小化修改原则，不要修改原有的代码结构
- 非必要不要修改前端代码


## 数据集成模块后端功能实现
请基于前端数据集成模块的设计，设计后端对应的数据模型

*关键描述*
- 后端新建应用dataintegration, 位置：backend\apps\dataintegration
- 前端集成模块代码位置： frontend\src\views\dataintegration
- 前端只有任务详情编辑页，详情信息如下数据结构
```json
{
    "schedule": {
        "type": "manual",
        "cronExpr": "",
        "group": ""
    },
    "detail": {
        "source": {
            "dataSourceIds": [],
            "databases": [],
            "databasePattern": "",
            "tables": [],
            "tablePattern": ""
        },
        "target": {
            "dataSourceId": "",
            "databaseName": "",
            "tableName": ""
        },
        "defaultMapping": false,
        "mappings": [],
        "where": "",
        "mode": {
            "type": "full",
            "incrementField": "",
            "incrementType": ""
        }
    }
}
```

- 需要完成对应前端数据集成任务列表

*注意事项*
- 后端代码开发要求符合开发规范，可参考其他应用的开发规范，
- 不要在backend/apps/dataintegration目录其外的地方修改代码
- 前端风格一致


# 数据集成模块
*需求*
  在数据集成管理模块，有首页信息，任务列表
  - 在数据集成管理首页，展示支持的任务类型，用户可以按需创建对应的任务
  - 在数据集成管理任务列表，展示所有任务信息

*功能点*
- 任务类型如下：
  - 数据库同步到数据库
  - 数据库同步到Hive
  - Hive同步到数据库

*开发要求*
- 数据集成模块，前端代码位置： frontend/src/views/dataintegration
- 数据集成首页：frontend/src/views/dataintegration/index.vue
- 数据集成任务列表：frontend/src/views/dataintegration/taskList.vue
- 任务详情页组件： frontend/src/views/dataintegration/taskDetail.vue
  - 在任务详情页，可以指定任务的名称，任务调度方式
  - 任务详情页中，根据任务类型展示如下对应的详情组件
    - 数据库同步到数据库：frontend/src/views/dataintegration/components/offline/dbToDbSyncDetail.vue
    - 数据库同步到Hive：frontend/src/views/dataintegration/components/offline/dbToHiveSyncDetail.vue
    - Hive同步到数据库：frontend/src/views/dataintegration/components/offline/hiveToDbSyncDetail.vue
- 每种类型的任务详情组件中，包含三个部分：基础信息（包括数据源和目的源）；数据结构映射（包括默认映射和自定义映射）；任务执行模式（包括全量和增量）
- 数据结构参考后端模型： backend/apps/dataintegration/models.py 中的 IntegrationTask 模型

*注意事项*
- 前端设计需遵循统一风格


# 数据集成数据源选择组件封装
*需求*
  封装一个数据库数据源的选择组件，用于数据集成任务中数据源的选择，该组件需要具备以下功能：
  - 展示所有已配置的数据库数据源
  - 支持搜索功能，用户可以根据数据源名称快速找到目标数据源
  - 点击数据源项后，如果该数据源下存在数据库信息，显示数据库选择框，列出该数据源下的所有数据库
  - 点击数据库项后，显示一个数据表选择框，列出该数据库下的所有数据表
  - 该组件可以传入参数：数据源信息，数据库信息，数据表信息，用于初始化组件状态

*开发规范*
- 该组件封装在frontend/src/views/dataintegration/components/DataSourceSelector.vue文件中
- 该组件的props参数如下：
  - dataSources: 已配置的数据库数据源列表，每个元素包含id和name属性
  - databases: 已配置的数据库列表，每个元素包含数据源id、数据源名称、数据库id和数据库名称属性
  - tables: 已配置的数据表列表，每个元素包含数据源id、数据源名称、数据库id、数据库名称、数据表id和数据表名称属性
- 该组件的事件如下：
  - selectDataSource: 当用户选择一个数据源时触发，参数为选中的数据源对象
  - selectDatabase: 当用户选择一个数据库时触发，参数为选中的数据库对象
  - selectTable: 当用户选择一个数据表时触发，参数为选中的数据表对象
- 组件中可以数据源，数据库，数据表的具体数据通过frontend\src\api\datasource.js中定义的接口来获取

*注意*
- 只需要完成这样的组件，不要修改其他地方的代码