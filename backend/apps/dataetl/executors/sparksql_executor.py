"""
Spark SQL执行器实现

支持：
- SQL脚本执行
- 【多租户聚合】STG→ODS聚合SQL生成
- 分布式数据处理
"""

import subprocess
import os
from typing import Dict, Any, Tuple
from datetime import datetime

from django.conf import settings
from .base import BaseExecutor


class SparkSQLExecutor(BaseExecutor):
    """
    Spark SQL执行器

    通过spark-submit提交SQL作业到Spark集群
    """

    SPARK_HOME = getattr(settings, 'SPARK_HOME', '/opt/spark')
    SPARK_MASTER = getattr(settings, 'SPARK_MASTER', 'spark://localhost:7077')

    def validate(self) -> Tuple[bool, str]:
        """
        验证Spark SQL任务配置

        Returns:
            (is_valid, error_message)
        """
        try:
            # 1. 验证数据源配置
            if not self.task.target_datasource:
                return False, "目标数据源不能为空"

            if not self.task.target_table:
                return False, "目标表不能为空"

            # 2. 验证SQL脚本
            if not self.task.datax_config.get('sql_script'):
                return False, "SQL脚本不能为空"

            return True, ""

        except Exception as e:
            return False, f"配置验证失败: {str(e)}"

    def execute(self) -> Dict[str, Any]:
        """
        执行Spark SQL任务

        Returns:
            执行结果字典
        """
        try:
            # 1. 获取SQL脚本
            if self.task.target_layer == 'ods':
                # ODS层：自动生成多租户聚合SQL
                sql_script = self._generate_aggregation_sql()
            else:
                # 其他层：使用配置的SQL脚本
                sql_script = self.task.datax_config.get('sql_script', '')

            # 2. 保存SQL脚本到临时文件
            sql_file = os.path.join('/tmp', f"spark_job_{self.execution_log.execution_id}.sql")
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write(sql_script)

            # 3. 准备日志文件路径
            log_path = os.path.join('/var/log/spark', f"{self.execution_log.execution_id}.log")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

            # 4. 构建spark-submit命令
            cmd = self._build_spark_submit_command(sql_file, log_path)

            # 5. 执行Spark命令（设置4小时超时）
            result = subprocess.run(
                cmd,
                shell=True,
                timeout=14400,  # 4小时超时
                capture_output=True,
                text=True
            )

            # 6. 解析执行结果
            stats = self._parse_spark_output(log_path)

            return {
                'status': 'success' if result.returncode == 0 else 'failed',
                'rows_read': stats.get('rows_read', 0),
                'rows_written': stats.get('rows_written', 0),
                'rows_error': 0,
                'bytes_transferred': stats.get('bytes_transferred', 0),
                'log_path': log_path,
                'error_message': stats.get('errorMessage', ''),
            }

        except subprocess.TimeoutExpired:
            return {
                'status': 'failed',
                'error_message': 'Spark execution timeout after 4 hours',
                'log_path': log_path if 'log_path' in locals() else '',
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error_message': str(e),
                'log_path': log_path if 'log_path' in locals() else '',
            }
        finally:
            # 清理临时SQL文件
            if 'sql_file' in locals() and os.path.exists(sql_file):
                try:
                    os.remove(sql_file)
                except:
                    pass

    def cancel(self) -> bool:
        """
        取消Spark任务

        Returns:
            是否成功取消
        """
        # TODO: 通过spark-cmd kill任务
        # spark kill <task_id>
        return True

    def _generate_aggregation_sql(self) -> str:
        """
        生成STG→ODS多租户聚合SQL

        Returns:
            SQL脚本字符串
        """
        try:
            # 获取ODS聚合任务配置
            agg_config = getattr(self.task, 'aggregation_config', None)
            if not agg_config:
                return self._generate_default_aggregation_sql()

            # 获取STG任务列表
            stg_tasks = agg_config.stg_tasks.all()
            if not stg_tasks:
                raise ValueError("ODS聚合任务没有关联STG任务")

            # 获取去重字段
            dedup_fields = agg_config.deduplication_fields or ['id']
            window_clause = f"PARTITION BY {', '.join(dedup_fields)} ORDER BY update_time DESC"

            # 生成CTE，union all租户数据
            cte_list = []
            for stg_task in stg_tasks:
                # 如果是STG任务，读取所有租户数据
                if stg_task.is_multi_db_task:
                    # 多租户STG数据
                    cte_list.append(f"""
                        SELECT *, '{stg_task.name}' as source_datasource
                        FROM {stg_task.target_table}
                        WHERE ds='${{bizdate}}'
                    """)
                else:
                    cte_list.append(f"""
                        SELECT *, '{stg_task.name}' as source_datasource
                        FROM {stg_task.target_table}
                        WHERE ds='${{bizdate}}'
                    """)

            # 获取目标字段
            if self.task.field_mapping:
                target_columns = ', '.join([m['target'] for m in self.task.field_mapping])
            else:
                target_columns = '*'

            # 生成完整的聚合SQL
            sql = f"""
-- ODS聚合任务: {self.task.name}
-- 业务日期: ${{bizdate}}
-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SET hive.exec.dynamic.mode=true;
SET hive.exec.dynamic.partition.mode=nonstrict;

WITH stg_data AS (
    {'UNION ALL'.join(cte_list)}
),
deduplicated AS (
    SELECT *,
           ROW_NUMBER() OVER ({window_clause}) as rn
    FROM stg_data
)
INSERT OVERWRITE TABLE {self.task.target_table}
PARTITION (ds='${{bizdate}}')
SELECT {target_columns}
FROM deduplicated
WHERE rn = 1
;
            """.strip()

            return sql

        except Exception as e:
            raise Exception(f"生成聚合SQL失败: {str(e)}")

    def _generate_default_aggregation_sql(self) -> str:
        """
        生成默认聚合SQL（当没有配置聚合任务时）

        Returns:
            默认SQL脚本
        """
        return f"""
-- 默认ODS聚合SQL
-- 任务: {self.task.name}

INSERT OVERWRITE TABLE {self.task.target_table}
PARTITION (ds='${{bizdate}}')
SELECT *
FROM {self.task.source_table or 'stg_table'}
WHERE ds='${{bizdate}}'
;
        """.strip()

    def _build_spark_submit_command(self, sql_file: str, log_path: str) -> str:
        """
        构建spark-submit命令

        Args:
            sql_file: SQL脚本文件路径
            log_path: 日志文件路径

        Returns:
            spark-submit命令字符串
        """
        cmd = f"""
{self.SPARK_HOME}/bin/spark-submit \
  --master {self.SPARK_MASTER} \
  --name "ETL_Task_{self.task.id}" \
  --executor-memory 2G \
  --driver-memory 1G \
  --num-executors 4 \
  --executor-cores 2 \
  --conf spark.sql.shuffle.partitions=200 \
  --files {sql_file} \
  -e "spark.sql('''$(cat {sql_file})''')" \
  > {log_path} 2>&1
        """.strip()

        return cmd

    def _parse_spark_output(self, log_path: str) -> Dict:
        """
        解析Spark输出日志，提取统计信息

        Args:
            log_path: 日志文件路径

        Returns:
            统计信息字典
        """
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()

            stats = {}

            # 提取读取行数
            # Spark SQL通常不会直接输出这些统计信息
            # 需要通过Spark Listener或者查询执行后的表统计

            if 'ERROR' in content or 'Exception' in content:
                # 提取错误信息
                lines = content.split('\n')
                error_lines = [line for line in lines if 'ERROR' in line or 'Exception' in line]
                stats['errorMessage'] = '\n'.join(error_lines[-5:])  # 最后5行错误

            return stats

        except Exception as e:
            return {}
