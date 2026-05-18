作为一位坚守“底层统一、模块解耦”原则的数据架构师，我将为你设计一套基于 Django 的一站式数据开发平台架构。

在 Django 项目结构中，我们将遵循 “高内聚、低耦合” 的思想，将这六大核心模块映射为独立的 Django
Apps。整个架构的核心原则是：边界清晰，严禁跨级反向依赖，核心调度层（Task）与业务逻辑层彻底解耦。

以下是该数据开发平台的整体设计架构与模块解析：

🏗️ 全局架构概览 (Django Apps 划分)

我们将在 Django 中创建以下核心 App：

1.  apps.datasource (数据源管理)
2.  apps.dataintegration (数据集成)
3.  apps.datadev (数据加工/建模)
4.  apps.datatask (任务调度与编排)
5.  apps.dataasset (数据资产与质量)
6.  apps.dataservice (数据服务 API)

🧩 模块详细设计与功能边界

1. 数据源管理 (apps.datasource)

定位： 整个平台所有数据库连接的“唯一真理来源”。

  - 主要功能：
      - 配置关系型/非关系型/大数据组件的连接信息（URL、IP、Port）。
      - 凭证管理： 密码必须使用 AES/RSA 加密存储。
      - 连通性测试： 提供一键 ping 数据库的能力。
      - 元数据探查： 提供获取库名、表清单、表结构（Schema）的底层 Helper 接口。
  - 功能边界（坚守点）：
      - 只懂连接，不懂业务。 它绝不知道什么是“同步任务”，也不知道什么是“数据血缘”。
      - 其他所有模块如果要连数据库查数据，必须调用
        datasource.facades.get_db_connection(source_id)，严禁各模块自己手写
        JDBC/pymysql 连接代码。

2. 数据集成 (apps.dataintegration)

定位： 负责 ODS 层的建设，将外部业务数据“搬运”到大数据平台。

  - 主要功能：
      - 向导式配置： 提供“源表 -> 目标表”的字段映射配置向导。
      - 同步策略： 全量同步、增量同步（按时间戳或 CDC binlog）。
      - 底层引擎对接： 将前端界面配置的 JSON，翻译成 DataX / SeaTunnel / Flink CDC 的执行脚本。
  - 功能边界：
      - 它只负责生成和保存“同步配置规则”。
      - 它不负责调度。 它需要将自己作为一个 task_type='SYNC' 的任务，注册到 datatask 模块中交由调度中心去执行。

3. 数据加工 / 建模 (apps.datadev)

定位： DWD/DWS/ADS 层的数据开发领地，提供 Web IDE 体验。

  - 主要功能：
      - 脚本管理： 编写 SQL (Hive/Spark/Doris) 或 Python (PySpark) 脚本。
      - 语法校验与试运行： 在保存前进行 SQL 语法高亮和 Dry-Run 校验。
      - 隐形治理卡点（关键）： 在保存脚本和表 DDL 时，强制要求开发者填写“表注释、字段注释、负责人、生命周期 TTL”。
  - 功能边界：
      - 只关注业务代码逻辑的编写与版本控制（类似 Git 里的单个文件）。
      - 依赖关系和执行图 (DAG) 不在这里画，交由 datatask 画。

4. 任务调度与编排 (apps.datatask)

定位： 平台的中枢神经，纯粹的调度器封装层。

  - 核心模型 (Models)：
      - Workflow (工作流 DAG)
      - Task (统一任务表)：包含 task_type 和一个巨大的 task_config
        (JSONField)，用于包容集成、开发、质量等不同任务。
      - TaskInstance (任务实例)：记录每一次运行的日志、状态（成功/失败/重试）、起止时间。
  - 主要功能：
      - 依赖管理（跨工作流、跨周期依赖）。
      - 基于 Cron 的定时调度执行、失败重试、告警（企微/钉钉）。
      - 对接底层调度引擎（轻量级可用 Celery/APScheduler，重型建议对接 Apache Airflow/DolphinScheduler
        API）。
  - 功能边界（极度重要）：
      - 它采用注册制，绝对不直接依赖业务模块！
      - 它不包含任何“如何运行同步代码”的逻辑。当需要执行一个任务时，它根据 task_type 找到对应的已注册的执行器（Executor）去触发。

5. 数据资产管理 (apps.dataasset)

定位： 提升数据的可见性与可信度（数据地图 + 数据质量）。

  - 主要功能：
      - 元数据中心： 采集表结构、分区信息、存储大小。提供基于 Elasticsearch 的全局搜表功能。
      - 数据血缘 (Lineage)： 解析 datadev 中的 SQL（可借助 SQLGlot 库），生成表级/字段级血缘图。
      - 数据质量 (DQC)：
        定义检查规则（如字段非空率、主键唯一、同环比波动）。质量规则本质上也是一种任务，运行后产生质量报告。若质量不达标，触发熔断，通知
        datatask 停止下游任务。
  - 功能边界：
      - 它是一个旁路观测者。它通过消费 Kafka 日志，或者接收其他 App 发出的 Django Signals (信号) 来异步构建资产视图。

6. 数据服务 API (apps.dataservice)

定位： 数据变现出口，将 ADS 层宽表直接转为 RESTful API。

  - 主要功能：
      - 配置化 API 生成： 选择一张表，配置查询条件（入参）和返回字段（出参），自动生成一个 HTTP 接口。
      - 服务网关能力： Token 鉴权、QPS 限流、调用日志统计。
  - 功能边界：
      - 它通过 datasource 获取高速缓存库（如 Redis/ClickHouse/Doris）的连接提供查询。绝不允许直接查询 ODS/DWD
        层的慢速 Hive 表。

🔌 核心亮点：Django 模块解耦与通信机制

为了防止 Django 代码最终变成一团乱麻（循环引用），模块间的协作必须遵循以下设计模式：

1. 任务注册中心模式 (Registry Pattern)

datatask 怎么知道如何执行 dataintegration 的任务？ 解法： 在 datatask 提供一个注册表。各业务模块在 Django 的
apps.py 的 ready() 方法中主动注册。

# datatask/registry.py
class TaskRegistry:
    _executors = {}
    
    @classmethod
    def register(cls, task_type, executor_func):
        cls._executors[task_type] = executor_func

# dataintegration/apps.py
from django.apps import AppConfig

class DataIntegrationConfig(AppConfig):
    name = 'dataintegration'
    def ready(self):
        from datatask.registry import TaskRegistry
        from .executor import run_sync_task
        # 集成线向调度线“挂号”
        TaskRegistry.register('DATA_SYNC', run_sync_task)

2. 公开边界与 Facade 模式

dataservice 需要获取数据库连接，不能写 from datasource.models import DBConnection 然后自己去查。 解法：
datasource 提供公开的门面接口。

# datasource/facades.py
def get_engine_by_id(source_id: int):
    """
    统一暴露的获取数据库引擎的方法，内部处理 AES 密码解密
    """
    conn_obj = DBConnection.objects.get(id=source_id)
    # 解密密码，构建 sqlalchemy engine 或 pymysql conn 返回...
    return engine

3. 异步解耦 (Django Signals / Celery)

当 datadev 中的表结构发生变更时，怎么通知 dataasset 更新元数据？ 解法： 不要直接调用。发出 Django 信号。

# datadev/views.py (在保存了新的 DDL 之后)
from django.dispatch import Signal
schema_changed_signal = Signal()

def save_table_schema(request):
    # ... 保存逻辑 ...
    schema_changed_signal.send(sender='datadev', table_name='dwd_users')

# dataasset/receivers.py
from django.dispatch import receiver
from datadev.views import schema_changed_signal

@receiver(schema_changed_signal)
def update_metadata(sender, **kwargs):
    # 异步触发元数据重新抓取或血缘解析
    pass

💡 架构师的避坑忠告

1.  不要为每个业务建一张调度表：一开始图省事，集成建个 SyncTask 表带 cron 字段，开发建个 SqlTask 带 cron
    字段，最后排查依赖时会彻底崩溃。必须在 datatask 建统一的 Task 主表，通过关联 ID 或
    JSON 关联业务配置。
2.  警惕长连接与连接池泄漏：数据平台频繁与外部数据库交互，在 datasource 的 facade 设计中，务必处理好连接池生命周期，建议引入
    sqlalchemy 的连接池管理，用完立刻 close/dispose。
3.  前端解耦优先：在 Vue 前端，将“画 DAG 图”封装为独立的高阶组件（如基于 X6 或 G6），供集成（串联同步任务）和调度（编排复杂工作流）复用。
