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
  

#### 设计规范（数据报表接口管理）

目标
- 提供统一的报表接口注册、维护、发布与调用机制。
- 通过唯一编码稳定访问报表接口，支撑版本与变更管理。
- 规范请求参数、响应格式、错误码与安全策略，提升可维护性与可测试性。
- 支持前端管理页面进行新增、编辑、删除、查询、试运行等操作。

核心概念
- `接口编码(code)`：全局唯一标识，稳定引用，建议不可更改。
- `接口定义`：接口元信息、参数、数据源、查询模板、响应结构与示例的综合描述。
- `接口地址(path)`：对外访问路径，建议与编码保持映射关系。
- `数据源与查询模板`：数据来源及查询逻辑（SQL/DSL/聚合/存储过程等）。
- `版本与状态`：接口版本管理与启用/停用/废弃等生命周期。

接口定义模型
- 基本信息
  - `code`：接口编码，string，示例：`sales_daily_summary`
  - `name`：接口名称，string
  - `description`：接口描述，string
  - `version`：版本号，string，语义化版本如 `1.0.0`
  - `status`：状态，enum：`draft|active|disabled|deprecated`
  - `tags`：标签，string[]，如业务域、系统模块
  - `owner`：负责人或团队，string
  - `visibility`：可见性，enum：`internal|partner|public`
- 路由与调用
  - `path`：接口地址，string，建议统一：`/data-api/{code}`
  - `method`：请求方法，enum：`GET|POST`
  - `auth_required`：是否鉴权，boolean
  - `rate_limit`：限流配置，object，如 `{"rps": 50, "burst": 200}`
  - `ip_whitelist`：IP白名单或网段列表，string[]
  - `cors`：跨域策略，object，如 `{"allowed_origins": ["..."]}`
- 参数规范（parameters：数组）
  - `name`：参数名，string
  - `in`：位置，enum：`path|query|header|body`
  - `type`：类型，enum：`string|number|integer|boolean|date|datetime|array|object`
  - `required`：是否必填，boolean
  - `default`：默认值，可选
  - `enum`：枚举范围，array，可选
  - `format`：格式提示（如 `yyyy-MM-dd`），可选
  - `description`：参数说明
  - `example`：示例值
  - `max_length|min_length|maximum|minimum|pattern`：校验规则，可选
- 数据源与查询
  - `datasource_id`：数据源标识，string
  - `query_type`：查询类型，enum：`sql|dsl|aggregation|stored_proc`
  - `query_template`：查询模板，string，支持命名参数绑定（如 `:startDate`）
  - `param_binding`：参数与模板绑定映射，object（如 `{"startDate": "$.parameters.startDate"}`）
  - `timeout_ms`：查询超时，number
  - `safe_mode`：启用安全模式（防注入、防全表扫描），boolean
- 响应定义
  - `response_schema`：响应结构（可用 JSON Schema）
  - `pagination`：分页支持，object（如 `{"enabled": true, "max_page_size": 1000}`）
  - `transform`：后置字段映射或聚合规则，object，可选
  - `example`：响应示例，object
- 运营与治理
  - `cache`：缓存策略，object（如 `{"enabled": true, "ttl_seconds": 60}`）
  - `audit`：审计记录开关，boolean
  - `metrics`：埋点配置，object（是否记录时延、错误率等）
- 元数据
  - `created_at|updated_at`：时间戳
  - `created_by|updated_by`：创建/更新人

对外访问路由规范
- 统一访问：`GET|POST /data-api/{code}`
  - 按 `code` 查找启用中的接口定义，进行鉴权、限流、参数校验；执行查询模板；返回统一响应结构。
- 管理接口（受鉴权保护，供前端管理页面使用）：
  - `GET /api/dataservice/interfaces`：分页查询接口定义
  - `GET /api/dataservice/interfaces/{code}`：获取单个定义
  - `POST /api/dataservice/interfaces`：新增接口定义
  - `PUT /api/dataservice/interfaces/{code}`：编辑接口定义
  - `DELETE /api/dataservice/interfaces/{code}`：删除接口定义
  - `POST /api/dataservice/interfaces/{code}/test`：试运行（传入参数进行一次查询，返回结果或错误）

请求与响应统一约定
- 请求参数
  - GET 请求优先使用 `query`；复杂结构使用 POST 的 `body`。
  - `path|query|header|body` 四类参数位置明确，不混用。
- 成功响应（统一外层）：
  - `code`：业务码，string（如 `OK`）
  - `message`：提示，string
  - `success`：是否成功，boolean
  - `data`：数据主体，object|array
  - `meta`：元信息（分页：`page|pageSize|total|hasNext`）
- 失败响应（统一外层）：
  - `code`：错误码，string（`INVALID_PARAM|UNAUTHORIZED|NOT_FOUND|RATE_LIMITED|INTERNAL_ERROR` 等）
  - `message`：错误描述，string
  - `success`：false
  - `details`：错误详情（字段校验失败列表等），array|object
- HTTP 状态码：`200|400|401|403|404|429|500`

权限与安全
- 鉴权策略
  - `auth_required=true` 的接口需校验 `JWT` 或 `API Key`；可按 `visibility` 区分策略。
  - 可配置角色/资源级权限控制（如按角色限制可访问的 `code`）。
- 防护策略
  - 参数校验与类型强制；查询层严格使用参数化绑定，拒绝拼接式模板。
  - 限流与 IP 白名单；CORS 严格限制来源。
  - 查询安全：限制 `timeout_ms`、行数上限、禁止无条件全表扫描。
- 审计与合规
  - 开启 `audit` 时记录：接口编码、调用人、时间、入参、响应概要（不含敏感数据）、时延、状态。

版本与生命周期
- 状态流转：`draft -> active -> deprecated -> disabled`
- 变更策略
  - 破坏性变更需升级 `version`，保留旧版本并置为 `deprecated` 一段时间。
  - 管理页面展示版本与状态，支持切换默认生效版本。
- 兼容策略
  - 同一 `code` 可支持 `version` 路由（可选），如：`GET /data-api/{code}?version=1.1.0`

前端管理页面规范
- 列表页展示字段：
  - `接口编码(code)`、`名称(name)`、`描述(description)`、`接口地址(path)`、`请求方法(method)`、`状态(status)`、`版本(version)`、`数据源(datasource_id)`、`更新时间(updated_at)`
- 操作：
  - 新增、编辑、删除、查看详情、试运行、启用/停用、复制定义
- 详情/编辑页分区：
  - 基本信息、路由与调用、参数定义（增删改并校验）、数据源与查询模板、响应定义与示例、缓存与限流、权限与安全、版本与变更记录
- 试运行：
  - 表单自动生成入参；展示响应数据与耗时；可保存成功示例用于回归测试。

缓存与性能
- 缓存策略：
  - 基于 `code + normalized(params)` 构建缓存键；`ttl_seconds` 控制时效。
  - 对实时性强的接口禁用缓存。
- 性能指标：
  - 记录 `qps`、`p95_latency`、`error_rate`；在管理页可视化展示。

错误码建议
- `OK`：成功
- `INVALID_PARAM`：参数校验失败
- `UNAUTHORIZED`：未授权
- `FORBIDDEN`：无权限
- `NOT_FOUND`：接口或资源不存在
- `RATE_LIMITED`：触发限流
- `INTERNAL_ERROR`：服务器内部错误
- `DATASOURCE_ERROR`：数据源访问错误
- `TIMEOUT`：查询超时
- `SCHEMA_MISMATCH`：响应数据不符合定义

示例：新增报表接口定义请求体（用于 `POST /api/dataservice/interfaces`）
```
{
  "code": "sales_daily_summary",
  "name": "每日销售汇总",
  "description": "按日期和门店维度汇总销售额与订单量。",
  "version": "1.0.0",
  "status": "active",
  "tags": ["sales", "report"],
  "owner": "BI-Team",
  "visibility": "internal",
  "path": "/data-api/sales_daily_summary",
  "method": "GET",
  "auth_required": true,
  "rate_limit": {"rps": 20, "burst": 100},
  "parameters": [
    {"name": "startDate", "in": "query", "type": "date", "required": true, "format": "yyyy-MM-dd", "description": "开始日期", "example": "2025-01-01"},
    {"name": "endDate", "in": "query", "type": "date", "required": true, "format": "yyyy-MM-dd", "description": "结束日期", "example": "2025-01-31"},
    {"name": "storeId", "in": "query", "type": "string", "required": false, "description": "门店ID"},
    {"name": "page", "in": "query", "type": "integer", "required": false, "default": 1, "minimum": 1},
    {"name": "pageSize", "in": "query", "type": "integer", "required": false, "default": 50, "maximum": 1000}
  ],
  "datasource_id": "dw_readonly",
  "query_type": "sql",
  "query_template": "SELECT date, store_id, SUM(amount) AS total_amount, COUNT(order_id) AS order_count FROM fact_sales WHERE date BETWEEN :startDate AND :endDate AND (:storeId IS NULL OR store_id = :storeId) GROUP BY date, store_id ORDER BY date LIMIT :pageSize OFFSET (:page - 1) * :pageSize",
  "param_binding": {
    "startDate": "$.parameters.startDate",
    "endDate": "$.parameters.endDate",
    "storeId": "$.parameters.storeId",
    "page": "$.parameters.page",
    "pageSize": "$.parameters.pageSize"
  },
  "timeout_ms": 20000,
  "safe_mode": true,
  "response_schema": {
    "type": "object",
    "properties": {
      "code": {"type": "string"},
      "message": {"type": "string"},
      "success": {"type": "boolean"},
      "data": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "date": {"type": "string", "format": "date"},
            "store_id": {"type": "string"},
            "total_amount": {"type": "number"},
            "order_count": {"type": "integer"}
          },
          "required": ["date", "store_id", "total_amount", "order_count"]
        }
      },
      "meta": {
        "type": "object",
        "properties": {
          "page": {"type": "integer"},
          "pageSize": {"type": "integer"},
          "total": {"type": "integer"},
          "hasNext": {"type": "boolean"}
        }
      }
    },
    "required": ["code", "message", "success", "data", "meta"]
  },
  "example": {
    "code": "OK",
    "message": "成功",
    "success": true,
    "data": [
      {"date": "2025-01-01", "store_id": "S001", "total_amount": 12345.67, "order_count": 321}
    ],
    "meta": {"page": 1, "pageSize": 50, "total": 1234, "hasNext": true}
  },
  "cache": {"enabled": true, "ttl_seconds": 60},
  "audit": true,
  "metrics": {"latency": true, "errorRate": true}
}
```

示例：统一错误响应
```
{
  "code": "INVALID_PARAM",
  "message": "参数 startDate 必须为 yyyy-MM-dd 格式",
  "success": false,
  "details": [{"field": "startDate", "error": "format"}]
}
```

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
  

```python
# 接口信息
class InterfaceInfo(BaseModel):
    IS_TOTAL_CHOICES = (('1', '是'), ('0', '否'))
    IS_PAGING_CHOICE = (('1', '是'), ('0', '否'))
    IS_DATA_OPTION_CHOICE = (('1', '是'), ('0', '否'))
    IS_SECODN_TABLE_CHOICE = (('1', '是'), ('0', '否'))
    IS_LOGIN_VISIT_CHOICE = (('1', '是'), ('0', '否'))
    ALARM_TYPE_CHOICES = (('0', '否'), ('1', '邮件'), ('2', '短信'), ('3', '钉钉'), ('4', '企业微信'), ('5', '电话'), ('6','飞书'))
    report = models.ForeignKey(ReportInfo,verbose_name="报表", on_delete=models.CASCADE)
    interface_name= models.CharField(max_length=255, verbose_name='接口名称')
    interface_code= models.CharField(max_length=255, verbose_name='接口编码',unique=True)
    interface_desc = models.TextField(verbose_name='接口描述',null=True, blank=True)
    interface_db_type = models.CharField(max_length=255, verbose_name='数据库类型')
    interface_db_name = models.CharField(max_length=255, verbose_name='数据库名称')
    interface_sql = models.TextField(verbose_name='接口sql', null=True, blank=True)
    is_total = models.CharField(default='0', max_length=1, verbose_name='是否合计',choices=IS_TOTAL_CHOICES)
    total_sql = models.TextField(verbose_name='合计sql', null=True, blank=True)
    is_paging = models.CharField(default='0', max_length=1, verbose_name='是否分页',choices=IS_PAGING_CHOICE)
    is_date_option = models.CharField(default='0', max_length=1,verbose_name='是否日期查询',choices=IS_DATA_OPTION_CHOICE)
    is_second_table = models.CharField(default='0', max_length=1,verbose_name='二级表头',choices=IS_SECODN_TABLE_CHOICE)
    is_login_visit = models.CharField(default='0', max_length=1,verbose_name='是否登陆验证',choices=IS_LOGIN_VISIT_CHOICE)
    alarm_type = models.CharField(default='0', max_length=1,verbose_name='报警类型',choices=ALARM_TYPE_CHOICES)
    user_name = models.CharField(max_length=255, verbose_name='用户名称', null=True, blank=True)
    interface_datasource = models.IntegerField(verbose_name='数据源ID', null=True, blank=True)


    

# 接口字段信息
# 接口数据类型 输出参数(1字符 2整数 3小数 4百分比) 输入参数(11日期 12月份 13单选 14多选 15文本)
class InterfaceField(BaseModel):
    DATA_TYPE_CHOICES = (
        ('1','字符'),
        ('2','整数'),
        ('3','小数'),
        ('4','百分比'),
        ('5','无格式整数'),
        ('6','无格式小数'),
        ('7','无格式百分比'),
        ('8','1位百分比'),
        ('9','1位小数'),
        ('10','年份'),
        ('11','日期'),
        ('12','月份'),
        ('13','单选'),
        ('14','多选'),
        ('15','文本')
    )
    SHOW_FLAG_CHOICES = (('1', '是'),('0','否'))
    EXPORT_FLAG_CHOICES = (('1', '是'), ('0', '否'))
    PARA_TYPE_CHOICES =(('1','输入参数'),('2','输出参数'))
    ROWSPAN_CHOICES = ((1, '是'), (0, '否'))
    interface = models.ForeignKey(InterfaceInfo,verbose_name="接口",on_delete=models.CASCADE)
    interface_para_code = models.CharField(max_length=255, verbose_name='接口参数编码')
    interface_para_name = models.CharField(max_length=255, verbose_name='接口参数名称')
    interface_para_position = models.IntegerField(verbose_name='接口参数位置')
    interface_para_type = models.CharField(max_length=255, verbose_name='接口参数类型', choices=PARA_TYPE_CHOICES)
    interface_data_type = models.CharField(max_length=255, verbose_name='接口参数数据类型', choices=DATA_TYPE_CHOICES)
    interface_para_default = models.CharField(max_length=255, verbose_name='接口参数默认值', null=True, blank=True)

    interface_para_rowspan = models.IntegerField(verbose_name='接口参数跨行', null=True, blank=True, choices=ROWSPAN_CHOICES)
    interface_parent_name = models.CharField(max_length=255, verbose_name='接口参数父级名称',null=True, blank=True)
    interface_parent_position = models.IntegerField(verbose_name='接口参数父级位置',null=True, blank=True)
    interface_para_interface_code = models.CharField(max_length=255, verbose_name='接口参数接口编码',null=True, blank=True)
    interface_cascade_para = models.CharField(max_length=255, verbose_name='接口参数级联参数',null=True, blank=True)
    interface_show_flag = models.CharField(max_length=255, verbose_name='接口参数是否显示', choices=SHOW_FLAG_CHOICES, default='1')
    interface_export_flag= models.CharField(max_length=255, verbose_name='接口参数是否导出',choices=EXPORT_FLAG_CHOICES, default='1')
    interface_show_desc = models.CharField(max_length=255, verbose_name='接口参数显示名称',null=True, blank=True, choices=SHOW_FLAG_CHOICES)
    interface_para_desc = models.CharField(max_length=255, verbose_name='接口参数描述',null=True, blank=True)

```

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


## 数据接口调用日志
*需求*
    数据接口调用日志记录，用于记录数据接口调用情况，方便后续分析和优化

*数据结构*
```python
class InterfaceQueryLog(BaseModel):
    interface_code = models.CharField(max_length=255, verbose_name='接口编码')
    interface_sql  = models.TextField(verbose_name='接口sql', null=True)
    interface_total_sql = models.TextField(verbose_name='接口总sql', null=True)
    execute_start_time = models.DateTimeField(verbose_name='开始时间', auto_now_add=True, null=True)
    execute_end_time = models.DateTimeField(verbose_name='结束时间', auto_now_add=True, null=True)
    execute_time = models.IntegerField(verbose_name='执行时间', default=0)
    execute_status = models.CharField(max_length=255, verbose_name='执行状态', null=True)
    error_message = models.TextField(verbose_name='错误信息', null=True)
    query_params = models.TextField(verbose_name='查询参数', null=True, blank=True)
    execute_type = models.ChoicesField(verbose_name='执行类型', choices=(('1', '查询'),('2', '导出')))
    execute_ip = models.CharField(max_length=255, verbose_name='调用方IP', null=True, blank=True)


```




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

# 数据集成功能开发
*需求*
  需要指定数据源下的数据进行同步到目标数据库
  - 同步范围：可以指定同步所有表，也可以指定同步部分表，具体方式分为：单表同步，整库同步，分库分表同步
  - 同步方式：可以选择增量同步或全量同步
  - 同步频率：可以设置定时同步或手动触发同步

*功能点*
- 数据集成管理页面新增“新增同步任务”按钮，点击可新增一个数据同步任务
- 数据集成管理页面新增“同步任务列表”，显示所有已新增的同步任务
- 数据集成管理页面新增“同步任务详情”，点击可查看同步任务的详细信息
- 数据集成管理页面新增“启动/暂停/删除同步任务”按钮，点击可对同步任务进行操作

*设计*
- 数据集成首页列出支持的数据同步范围，包括单表同步，整库同步，分库分表同步
- 选择数据同步范围后再跳转到数据同步任务详情页面，展示该同步范围的详细配置项，包括：
  - 数据源配置：包括数据库类型，主机名，端口，数据库名，用户名，密码等
  - 目标数据库配置：包括数据库类型，主机名，端口，数据库名，用户名，密码等
  - 同步范围配置：包括同步所有表，或指定同步部分表
  - 同步方式配置：包括增量同步或全量同步
  - 同步频率配置：包括定时同步或手动触发同步

*注意*
- 第一阶段要求给出前端设计页面，不修改后端代码
- 前端代码位置：frontend/src/views/dataintegration/
- 前端数据可以造一些样例数据，用于展示功能

## 数据集成功能更新
*需求*
  重新设计如下需求：
- 数据同步的范围如下：
  - 数据库同步到数据库：支持在不同的数据源之间同步数据
    - 数据库同步支持单表同步，整库同步，分库分表同步
  - 数据库同步到集群：支持将数据库数据同步到hive等分布式存储上
  - 集群同步到数据库：支持将数据从集群同步到数据库，例如将hive表数据同步到mysql中

- 同步任务支持增量同步和全量同步，增量同步基于时间戳或主键范围，全量同步则是重新同步所有数据
- 数据同步明细页支持如下操作
  - 选择数据源，基于在数据源管理中已经创建好的数据源
  - 选择数据库，可以选择单个数据库，也可以选择多个数据库
  - 选择待同步的表，支持单表同步，整库同步
  - 选择同步方式，增量同步或全量同步， 增量同步时需要指定增量字段（自增ID或时间戳字段）

*代码位置*
- 前端：frontend/src/views/dataintegration/

*注意*
- 数据源选项来源于数据源管理页面已创建好的数据源
- 数据库选项来源于所选数据源下检测到的数据库
