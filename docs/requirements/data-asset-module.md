# 数据资产管理模块说明

## 模块状态

**当前代码主干仍保留。**

以当前主干实现为准，数据资产模块尚未移除，仍然具备完整的前后端入口、菜单配置和后端接口能力。此前文档中“已完全移除”的表述与当前实现不一致，本文件按当前仓库实现重新整理。

## 模块定位

数据资产模块当前承担三类能力：

1. **元数据采集**：从已配置的数据源中获取数据库、表、字段信息，并写入本地元数据表。
2. **元数据浏览**：提供表查找、字段查找、字段详情查看与最近采集结果展示。
3. **表级血缘管理**：维护表与表之间的上下游关系，并提供简单的血缘图查询能力。

从当前实现看，它更接近一个**轻量级元数据目录 + 手工维护的表级血缘模块**，尚不是完整的数据治理/资产管理平台。

## 当前重构阶段（2026-04-18）

当前已进入“标准数据资产平台”第二阶段：在保留旧写端与旧血缘模型的前提下，开始把**读端查询**切换到规范资产模型；血缘标准化仍不在当前范围内。

### Phase 1 已落地的规范模型

- `AssetNamespace`：承载 `data_source + environment + catalog + schema`
- `DataAsset`：规范资产主表
- `DataAssetColumn`：规范资产字段表
- `MetaCollectionTask` 已补充采集范围字段：
  - `scope_level`
  - `scope_catalog_name`
  - `scope_schema_name`
  - `scope_asset_name`
  - `run_mode`
- Presto/Trino 采集任务与规范资产模型已对齐 `catalog.schema` 解析，`scope_level` 可表达 schema 级范围

### Phase 1 策略

- 保留旧模型 `MetaTable` / `MetaColumn` / `TableLineage`
- 采集链路对 `MetaTable` / `MetaColumn` 与规范资产模型执行双写
- 血缘仍沿用旧 `TableLineage`，**暂不实现规范血缘模型**

### Phase 2 已落地的读端切换

- 新增规范读接口：
  - `GET /data-api/dataasset/asset-namespace`
  - `GET /data-api/dataasset/asset`
  - `GET /data-api/dataasset/asset-column`
- 旧接口 `GET /data-api/dataasset/meta-table`、`GET /data-api/dataasset/meta-column` 已切换为从规范模型读取
- 旧接口返回结构继续兼容现有前端页面与血缘选择器，优先返回 `legacy_meta_table_id / legacy_meta_column_id` 对应的历史标识
- 写端仍保留：
  - 元数据采集写入 `MetaTable` / `MetaColumn` + 规范模型双写
  - 表级血缘仍写旧 `TableLineage`

## 当前实现范围

### 后端

- Django App：`backend/apps/dataasset/`
- 路由前缀：`/data-api/dataasset/`
- 核心模型：
  - `AssetNamespace`：规范资产命名空间
  - `DataAsset`：规范资产主表
  - `DataAssetColumn`：规范资产字段
  - `MetaTable`：元数据表
  - `MetaColumn`：元数据字段
  - `MetaCollectionTask`：采集任务追踪
  - `TableLineage`：表级血缘关系（旧模型，当前仍保留）
- 主要能力：
  - 元数据表/字段查询
  - 数据库/表/字段实时探查
  - 同步整库采集、单表采集、异步整库采集
  - 采集状态查询与取消
  - 表级血缘 CRUD、上下游查询、图谱查询

### 前端

- 页面目录：`frontend/src/views/data/asset/`
- API 封装：`frontend/src/api/data/asset.js`
- 页面组成：
  - `index.vue`：资产概览
  - `metadata/index.vue`：元数据浏览与采集入口
  - `lineage/index.vue`：血缘管理
  - `lineage/LineageGraphDialog.vue`：血缘图对话框
- 关联入口：
  - 数据源详情页 `frontend/src/views/data/datasource/detail.vue` 也提供数据库探查、单表采集、异步采集与任务状态轮询能力

### 菜单与入口

- 初始化菜单仍包含 `/data-asset`
- 子菜单仍包含：
  - 资产概览
  - 元数据管理
  - 数据血缘

## 当前主要接口

### 元数据浏览

- `GET /data-api/dataasset/meta-table`
- `GET /data-api/dataasset/meta-table/{id}`
- `GET /data-api/dataasset/meta-column`
- `GET /data-api/dataasset/meta-column/{id}`
- `GET /data-api/dataasset/asset-namespace`
- `GET /data-api/dataasset/asset`
- `GET /data-api/dataasset/asset/{id}`
- `GET /data-api/dataasset/asset-column`
- `GET /data-api/dataasset/asset-column/{id}`

### 元数据采集

- `POST /data-api/dataasset/collection/databases`
- `POST /data-api/dataasset/collection/tables`
- `POST /data-api/dataasset/collection/columns`
- `POST /data-api/dataasset/collection/collect`
- `POST /data-api/dataasset/collection/collect-table`
- `POST /data-api/dataasset/collection/collect-async`
- `GET /data-api/dataasset/collection/collect-status`
- `POST /data-api/dataasset/collection/collect-cancel`

### 表级血缘

- `GET /data-api/dataasset/lineage`
- `POST /data-api/dataasset/lineage`
- `PUT /data-api/dataasset/lineage/{id}`
- `DELETE /data-api/dataasset/lineage/{id}`
- `GET /data-api/dataasset/lineage/upstream`
- `GET /data-api/dataasset/lineage/downstream`
- `GET /data-api/dataasset/lineage/graph`

## 已知现状与边界

- 旧元数据查询接口的 **GET 读路径** 已切换到 `AssetNamespace` / `DataAsset` / `DataAssetColumn`，但新增/修改/删除仍沿用旧模型。
- 血缘模型当前仍为**手工维护的表级关系**，规范血缘模型已明确延后，不在当前阶段范围内。
- 异步采集当前基于**进程内线程 + 内存注册表**，更适合单机轻量场景。
- 命名空间解析当前已补齐 Presto/Trino 的 `catalog.schema` 拆分；其余数据源仍可能只采集到 catalog 级信息。
- `MetaCollectionTask` 已承担同步/异步采集的统一占槽语义：同一数据源同一时刻仅允许一个活动采集任务。
- 前端存在历史 API 残留：`frontend/src/api/data/meta.js` 仍在仓库中，但当前页面实际使用的是 `api/data/asset.js`。

## 文档维护说明

- 后续如模块继续保留，应以本文件作为数据资产模块需求与实现对齐入口。
- 如未来决定正式下线，需同步删除前后端实现、菜单入口，并同时更新：
  - `docs/requirements/README.md`
  - `docs/requirements/active_tasks.md`
  - `docs/changelog.md`
