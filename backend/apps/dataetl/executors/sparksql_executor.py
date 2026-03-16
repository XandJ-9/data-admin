"""
Spark SQL执行器实现

支持：
- SQL脚本执行
- 【多租户聚合】STG→ODS聚合SQL生成
- 分布式数据处理
"""

import subprocess
import os
import logging
from typing import Dict, Any, Tuple
from datetime import datetime

from django.conf import settings
from .base import BaseETLExecutor

logger = logging.getLogger(__name__)


class SparkSQLExecutor(BaseETLExecutor):
    """
    Spark SQL执行器

    通过spark-submit提交SQL作业到Spark集群
    """

    SPARK_HOME = getattr(settings, 'SPARK_HOME', '/opt/spark')
    SPARK_MASTER = getattr(settings, 'SPARK_MASTER', 'spark://localhost:7077')

    def __init__(self, task: Any, config: Dict[str, Any] = None):
        """
        初始化 Spark SQL 执行器

        Args:
            task: ETLTask 实例
            config: 执行器配置
        """
        super().__init__(task, config)
        self.process = None

    def validate(self) -> Tuple[bool, str]:
        """
        验证Spark SQL任务配置

        Returns:
            (is_valid, error_message)
        """
        try:
            # 验证数据源配置
            if not self.task.target_datasource:
                return False, "目标数据源不能为空"

            if not self.task.target_table:
                return False, "目标表不能为空"

            # 验证SQL配置
            sql_config = self.task.sql_config
            if not sql_config:
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
        start_time = datetime.now()

        try:
            # 获取SQL脚本
            sql_script = self.task.sql_config

            # 保存SQL脚本到临时文件
            execution_id = f"spark_{self.task.task_code}_{int(start_time.timestamp())}"
            sql_file = os.path.join('/tmp', f"spark_job_{execution_id}.sql")
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write(sql_script)

            # 准备日志文件路径
            log_path = os.path.join('/var/log/spark', f"{execution_id}.log")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

            # 构建spark-submit命令
            cmd = self._build_spark_submit_command(sql_file, log_path)

            logger.info(f"Executing Spark SQL command: {cmd}")

            # 执行Spark命令（设置4小时超时）
            result = subprocess.run(
                cmd,
                shell=True,
                timeout=14400,  # 4小时超时
                capture_output=True,
                text=True
            )

            end_time = datetime.now()
            duration_seconds = int((end_time - start_time).total_seconds())

            # 解析执行结果
            stats = self._parse_spark_output(log_path)

            return {
                'status': 'success' if result.returncode == 0 else 'failed',
                'total_rows': stats.get('rows_written', 0),
                'success_rows': stats.get('rows_written', 0) if result.returncode == 0 else 0,
                'failed_rows': 0,
                'duration_seconds': duration_seconds,
                'error_message': stats.get('errorMessage', '') if result.returncode != 0 else None,
                'log_file': log_path,
            }

        except subprocess.TimeoutExpired:
            end_time = datetime.now()
            duration_seconds = int((end_time - start_time).total_seconds())
            return {
                'status': 'failed',
                'total_rows': 0,
                'success_rows': 0,
                'failed_rows': 0,
                'duration_seconds': duration_seconds,
                'error_message': 'Spark execution timeout after 4 hours',
            }
        except Exception as e:
            end_time = datetime.now()
            duration_seconds = int((end_time - start_time).total_seconds())
            return {
                'status': 'failed',
                'total_rows': 0,
                'success_rows': 0,
                'failed_rows': 0,
                'duration_seconds': duration_seconds,
                'error_message': str(e),
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
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=30)
                self._mark_cancelled()
                return True
            except Exception as e:
                logger.error(f"Failed to cancel Spark task: {e}")
                return False
        return False

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

            if 'ERROR' in content or 'Exception' in content:
                # 提取错误信息
                lines = content.split('\n')
                error_lines = [line for line in lines if 'ERROR' in line or 'Exception' in line]
                stats['errorMessage'] = '\n'.join(error_lines[-5:])  # 最后5行错误

            return stats

        except Exception as e:
            logger.error(f"Failed to parse Spark output: {e}")
            return {}


# 注册 Spark SQL 执行器
from .base import ExecutorFactory
ExecutorFactory.register_executor('spark', SparkSQLExecutor)
