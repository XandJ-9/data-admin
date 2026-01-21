"""
DataX执行器实现

支持：
- 单库数据同步
- 【5000+租户优化】多库并发采集
- 增量同步（全量/按时间/按ID）
- 字段映射和类型转换
"""

import json
import subprocess
import os
import re
from typing import Dict, Any, Tuple
from datetime import datetime

from django.conf import settings
from .base import BaseExecutor
from apps.dataetl.models import TaskExecutionLog


class DataXExecutor(BaseExecutor):
    """
    DataX执行器

    阿里开源DataX工具的Python包装器
    文档: https://github.com/alibaba/DataX
    """

    DATAX_HOME = getattr(settings, 'DATAX_HOME', '/opt/datax')
    DATAX_LOG_DIR = getattr(settings, 'DATAX_LOG_DIR', '/var/log/datax')

    # 数据源插件映射
    READER_PLUGINS = {
        'mysql': 'mysqlreader',
        'mariadb': 'mysqlreader',
        'postgresql': 'postgresqlreader',
        'postgres': 'postgresqlreader',
        'oracle': 'oraclereader',
        'sqlserver': 'sqlserverreader',
        'sqlite': 'sqlitereader',
        'hive': 'hivereader',
        'hdfs': 'hdfsreader',
    }

    WRITER_PLUGINS = {
        'mysql': 'mysqlwriter',
        'mariadb': 'mysqlwriter',
        'postgresql': 'postgresqlwriter',
        'postgres': 'postgresqlwriter',
        'oracle': 'oraclewriter',
        'sqlserver': 'sqlserverwriter',
        'hive': 'hivewriter',
        'hdfs': 'hdfswriter',
        'adswriter': 'adswriter',
    }

    def validate(self) -> Tuple[bool, str]:
        """
        验证DataX任务配置

        Returns:
            (is_valid, error_message)
        """
        try:
            # 1. 验证数据源配置
            if not self.task.source_datasource or not self.task.target_datasource:
                return False, "源数据源和目标数据源不能为空"

            if not self.task.source_table or not self.task.target_table:
                return False, "源表和目标表不能为空"

            # 2. 验证多库采集配置
            if self.task.is_multi_db_task and not self.task.source_databases:
                return False, "多库采集任务必须指定源数据库列表"

            # 3. 验证数据源连接（可选，耗时较长）
            # from apps.dbutils.factory import get_executor
            # src_executor = get_executor(self.task.source_datasource)
            # src_executor.test_connection()

            return True, ""

        except Exception as e:
            return False, f"配置验证失败: {str(e)}"

    def execute(self) -> Dict[str, Any]:
        """
        执行DataX任务

        Returns:
            执行结果字典
        """
        try:
            # 1. 生成DataX JSON配置
            datax_config = self._build_datax_config()

            # 2. 保存配置文件
            config_path = os.path.join('/tmp', f"datax_job_{self.execution_log.execution_id}.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(datax_config, f, ensure_ascii=False, indent=2)

            # 3. 准备日志文件路径
            log_path = os.path.join(self.DATAX_LOG_DIR, f"{self.execution_log.execution_id}.log")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

            # 4. 构建DataX命令
            cmd = f"python {self.DATAX_HOME}/bin/datax.py {config_path} > {log_path} 2>&1"

            # 5. 执行DataX命令（设置2小时超时）
            result = subprocess.run(
                cmd,
                shell=True,
                timeout=7200,  # 2小时超时
                capture_output=True,
                text=True
            )

            # 6. 解析执行结果
            stats = self._parse_datax_output(log_path)

            return {
                'status': 'success' if result.returncode == 0 else 'failed',
                'rows_read': stats.get('totalReadRecords', 0),
                'rows_written': stats.get('totalWriteRecords', 0),
                'rows_error': stats.get('totalErrorRecords', 0),
                'bytes_transferred': stats.get('totalTransferBytes', 0),
                'log_path': log_path,
                'error_message': stats.get('errorMessage', ''),
            }

        except subprocess.TimeoutExpired:
            return {
                'status': 'failed',
                'error_message': 'DataX execution timeout after 2 hours',
                'log_path': log_path if 'log_path' in locals() else '',
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error_message': str(e),
                'log_path': log_path if 'log_path' in locals() else '',
            }
        finally:
            # 清理临时配置文件
            if 'config_path' in locals() and os.path.exists(config_path):
                try:
                    os.remove(config_path)
                except:
                    pass

    def cancel(self) -> bool:
        """
        取消DataX任务

        DataX本身不支持优雅停止，需要通过进程kill实现

        Returns:
            是否成功取消
        """
        # TODO: 实现进程跟踪和kill
        # 1. 记录DataX进程的PID
        # 2. kill -9 <PID>
        # 3. 清理临时文件
        return True

    def _build_datax_config(self) -> Dict:
        """
        生成DataX配置JSON

        Returns:
            DataX配置字典
        """
        config = {
            "job": {
                "setting": {
                    "speed": {
                        "byte": 1048576,  # 1MB/s
                        "record": 100000,  # 10万条/s
                    },
                    "errorLimit": {
                        "record": 0,  # 错误记录数限制
                        "percentage": 0.01,  # 错误率阈值1%
                    }
                },
                "content": [
                    {
                        "reader": {
                            "name": self._get_reader_plugin(),
                            "parameter": self._build_reader_params()
                        },
                        "writer": {
                            "name": self._get_writer_plugin(),
                            "parameter": self._build_writer_params()
                        }
                    }
                ]
            }
        }

        # 应用字段映射转换
        if self.task.field_mapping:
            config["job"]["content"][0]["transformer"] = self._build_transformers()

        return config

    def _build_reader_params(self) -> Dict:
        """
        构建reader参数 - 支持多库采集

        Returns:
            reader参数字典
        """
        params = {
            "username": self.task.source_datasource.username,
            "password": self.task.source_datasource.password,
            "column": self._get_source_columns(),
            "splitPk": "",
        }

        # 【5000+租户优化】多库采集任务
        if self.task.is_multi_db_task and self.task.source_databases:
            # 为每个租户库创建一个connection配置
            params["connection"] = []
            for db_name in self.task.source_databases:
                params["connection"].append({
                    "jdbcUrl": [self._build_jdbc_url(
                        self.task.source_datasource.db_type,
                        self.task.source_datasource.host,
                        self.task.source_datasource.port,
                        db_name
                    )],
                    "table": [self.task.source_table]
                })
            # 多库采集时设置并发度
            params["concurrency"] = self.task.concurrency or 10
        else:
            # 单库采集（原有逻辑）
            params["connection"] = [{
                "jdbcUrl": [self._build_jdbc_url(
                    self.task.source_datasource.db_type,
                    self.task.source_datasource.host,
                    self.task.source_datasource.port,
                    self.task.source_datasource.db_name
                )],
                "table": [self.task.source_table]
            }]

        # 增量策略
        if self.task.incremental_strategy != 'full':
            params["where"] = self._build_incremental_where()

        return params

    def _build_writer_params(self) -> Dict:
        """
        构建writer参数

        Returns:
            writer参数字典
        """
        params = {
            "username": self.task.target_datasource.username,
            "password": self.task.target_datasource.password,
            "column": self._get_target_columns(),
            "connection": [{
                "jdbcUrl": [self._build_jdbc_url(
                    self.task.target_datasource.db_type,
                    self.task.target_datasource.host,
                    self.task.target_datasource.port,
                    self.task.target_datasource.db_name
                )],
                "table": [self.task.target_table]
            }],
            "writeMode": "insert",  # 或 replace/update
        }

        # 分区配置
        if self.task.target_partition:
            partition_expr = self._build_partition_expr()
            if partition_expr:
                params["partition"] = partition_expr

        return params

    def _build_incremental_where(self) -> str:
        """
        构建增量条件

        Returns:
            WHERE条件字符串
        """
        if not self.task.incremental_field:
            return "1=0"  # 无增量字段，不抽取数据

        field = self.task.incremental_field

        # 从上一次执行日志中获取最大值
        last_execution = TaskExecutionLog.objects.filter(
            task=self.task,
            status='success'
        ).order_by('-create_time').first()

        if not last_execution:
            return f"{field} IS NOT NULL"  # 首次全量

        # 根据字段类型构建条件
        last_value = last_execution.execution_params.get(f'last_{field}')
        if last_value:
            return f"{field} > '{last_value}'"

        return "1=0"

    def _get_source_columns(self) -> list:
        """
        获取源表字段列表

        Returns:
            字段名列表
        """
        if self.task.field_mapping:
            return [m['source'] for m in self.task.field_mapping]
        return ["*"]

    def _get_target_columns(self) -> list:
        """
        获取目标表字段列表

        Returns:
            字段名列表
        """
        if self.task.field_mapping:
            return [m['target'] for m in self.task.field_mapping]
        return ["*"]

    def _build_partition_expr(self) -> str:
        """
        构建分区表达式

        Returns:
            分区表达式字符串
        """
        partition_config = self.task.target_partition
        if partition_config.get('type') == 'date':
            field = partition_config.get('field', 'ds')
            format_str = partition_config.get('format', 'yyyyMMdd')
            # 使用业务日期变量
            return f"{field}='${{bizdate}}'"
        return ""

    def _build_transformers(self) -> list:
        """
        构建字段转换规则

        Returns:
            转换规则列表
        """
        transformers = []
        for mapping in self.task.field_mapping:
            if mapping.get('source') != mapping.get('target'):
                # DataX的Groovy转换器
                transformers.append({
                    "name": "dx_groovy",
                    "parameter": {
                        "code": f"return {mapping.get('type', 'String')}.valueOf({mapping['source']});",
                        "extraPackage": []
                    }
                })
        return transformers

    def _get_reader_plugin(self) -> str:
        """
        根据数据源类型获取reader插件名

        Returns:
            reader插件名
        """
        db_type = self.task.source_datasource.db_type.lower()
        return self.READER_PLUGINS.get(db_type, 'streamreader')

    def _get_writer_plugin(self) -> str:
        """
        根据目标数据源类型获取writer插件名

        Returns:
            writer插件名
        """
        db_type = self.task.target_datasource.db_type.lower()
        return self.WRITER_PLUGINS.get(db_type, 'streamwriter')

    def _build_jdbc_url(self, db_type: str, host: str, port: int, db_name: str) -> str:
        """
        构建JDBC URL

        Args:
            db_type: 数据库类型
            host: 主机地址
            port: 端口号
            db_name: 数据库名

        Returns:
            JDBC URL字符串
        """
        db_type = db_type.lower()

        if db_type in ['mysql', 'mariadb']:
            return f"jdbc:mysql://{host}:{port}/{db_name}"
        elif db_type in ['postgresql', 'postgres']:
            return f"jdbc:postgresql://{host}:{port}/{db_name}"
        elif db_type == 'oracle':
            return f"jdbc:oracle:thin:@{host}:{port}:{db_name}"
        elif db_type == 'sqlserver':
            return f"jdbc:sqlserver://{host}:{port};databaseName={db_name}"
        elif db_type == 'hive':
            return f"jdbc:hive2://{host}:{port}/{db_name}"
        else:
            return f"jdbc:{db_type}://{host}:{port}/{db_name}"

    def _parse_datax_output(self, log_path: str) -> Dict:
        """
        解析DataX输出日志，提取统计信息

        Args:
            log_path: 日志文件路径

        Returns:
            统计信息字典
        """
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # DataX输出格式示例：
            # 总记录数: 1000000
            # 成功记录数: 999999
            # 失败记录数: 1

            stats = {}

            # 提取总读取记录数
            match = re.search(r'总记录数[：:]\s*(\d+)', content)
            if match:
                stats['totalReadRecords'] = int(match.group(1))

            # 提取总写入记录数
            match = re.search(r'成功记录数[：:]\s*(\d+)', content)
            if match:
                stats['totalWriteRecords'] = int(match.group(1))

            # 提取失败记录数
            match = re.search(r'失败记录数[：:]\s*(\d+)', content)
            if match:
                stats['totalErrorRecords'] = int(match.group(1))

            # 提取传输字节数
            match = re.search(r'总字节数[：:]\s*(\d+)', content)
            if match:
                stats['totalTransferBytes'] = int(match.group(1))

            # 提取错误信息
            if '失败记录数' in content:
                match = re.search(r'错误信息[：:]\s*(.+)', content, re.MULTILINE)
                if match:
                    stats['errorMessage'] = match.group(1).strip()

            return stats

        except Exception as e:
            return {}
