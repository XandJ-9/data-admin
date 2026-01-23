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
from django.utils import timezone
from .base import BaseExecutor
from apps.datataskmonitor.models import TaskExecution


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

            # 2. 验证场景配置
            scenario = self.task.scenario
            if scenario in ['biz_to_stg', 'db_to_db'] and not self.task.source_datasource:
                return False, f"场景 {scenario} 需要源数据源"

            if scenario in ['warehouse_to_biz', 'db_to_db'] and not self.task.target_datasource:
                return False, f"场景 {scenario} 需要目标数据源"

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
            # 记录开始
            self.add_log('INFO', '开始执行DataX任务')

            # 1. 生成DataX JSON配置
            datax_config = self._build_datax_config()
            self.add_log('DEBUG', f'DataX配置生成成功')

            # 2. 保存配置文件
            execution_id = self.task_execution.id
            config_path = os.path.join('/tmp', f"datax_job_{execution_id}.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(datax_config, f, ensure_ascii=False, indent=2)

            # 3. 准备日志文件路径
            log_path = os.path.join(self.DATAX_LOG_DIR, f"{execution_id}.log")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

            # 4. 更新进度
            self.update_progress(10, '准备DataX配置', '初始化')

            # 5. 构建DataX命令
            cmd = f"python {self.DATAX_HOME}/bin/datax.py {config_path} > {log_path} 2>&1"
            self.add_log('INFO', f'执行命令: {cmd}')

            # 6. 更新进度
            self.update_progress(20, '开始数据同步', '执行中')

            # 7. 执行DataX命令（设置2小时超时）
            result = subprocess.run(
                cmd,
                shell=True,
                timeout=7200,  # 2小时超时
                capture_output=True,
                text=True
            )

            # 8. 更新进度
            self.update_progress(90, '解析执行结果', '完成中')

            # 9. 解析执行结果
            stats = self._parse_datax_output(log_path)

            self.add_log('INFO', f'DataX执行完成: 读取={stats.get("totalReadRecords", 0)}, 写入={stats.get("totalWriteRecords", 0)}')

            return {
                'status': 'success' if result.returncode == 0 else 'failed',
                'rows_read': stats.get('totalReadRecords', 0),
                'rows_written': stats.get('totalWriteRecords', 0),
                'rows_failed': stats.get('totalErrorRecords', 0),
                'bytes_processed': stats.get('totalTransferBytes', 0),
                'log_file_path': log_path,
                'error_message': stats.get('errorMessage', ''),
            }

        except subprocess.TimeoutExpired:
            self.add_log('ERROR', 'DataX执行超时（2小时）')
            return {
                'status': 'failed',
                'error_message': 'DataX execution timeout after 2 hours',
                'log_file_path': log_path if 'log_path' in locals() else '',
            }
        except Exception as e:
            self.add_log('ERROR', f'DataX执行异常: {str(e)}')
            return {
                'status': 'failed',
                'error_message': str(e),
                'log_file_path': log_path if 'log_path' in locals() else '',
            }
        finally:
            # 清理临时配置文件
            if 'config_path' in locals() and os.path.exists(config_path):
                try:
                    os.remove(config_path)
                    self.add_log('DEBUG', '清理临时配置文件')
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
        构建reader参数

        Returns:
            reader参数字典
        """
        if not self.task.source_datasource:
            raise ValueError("源数据源不能为空")

        params = {
            "username": self.task.source_datasource.username,
            "password": self.task.source_datasource.password,
            "column": self._get_source_columns(),
            "splitPk": "",
            "connection": [{
                "jdbcUrl": [self._build_jdbc_url(
                    self.task.source_datasource.db_type,
                    self.task.source_datasource.host,
                    self.task.source_datasource.port,
                    self.task.source_database or self.task.source_datasource.db_name
                )],
                "table": [self.task.source_table]
            }]
        }

        # 增量策略
        if self.task.sync_mode != 'full':
            params["where"] = self._build_incremental_where()

        # 过滤条件
        if self.task.source_filter:
            existing_where = params.get("where", "")
            if existing_where:
                params["where"] = f"({existing_where}) AND ({self.task.source_filter})"
            else:
                params["where"] = self.task.source_filter

        return params

    def _build_writer_params(self) -> Dict:
        """
        构建writer参数

        Returns:
            writer参数字典
        """
        if not self.task.target_datasource:
            raise ValueError("目标数据源不能为空")

        params = {
            "username": self.task.target_datasource.username,
            "password": self.task.target_datasource.password,
            "column": self._get_target_columns(),
            "connection": [{
                "jdbcUrl": [self._build_jdbc_url(
                    self.task.target_datasource.db_type,
                    self.task.target_datasource.host,
                    self.task.target_datasource.port,
                    self.task.target_database or self.task.target_datasource.db_name
                )],
                "table": [self.task.target_table]
            }],
            "writeMode": "insert",
        }

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

        # 从上一次成功执行中获取最大值
        # 查找同类型任务的上一次成功执行
        last_execution = TaskExecution.objects.filter(
            task_type='etl',
            task_id=self.task.id,
            status='success'
        ).order_by('-start_time').first()

        if not last_execution:
            return f"{field} IS NOT NULL"  # 首次全量

        # 从ETL执行详情中获取上次执行的增量值
        try:
            etl_details = last_execution.etl_details
            if etl_details and hasattr(etl_details, 'task_config_snapshot'):
                snapshot = etl_details.task_config_snapshot
                last_value = snapshot.get('last_incremental_value')
                if last_value:
                    return f"{field} > '{last_value}'"
        except Exception:
            pass

        return f"{field} IS NOT NULL"

    def _get_source_columns(self) -> list:
        """
        获取源表字段列表

        Returns:
            字段名列表
        """
        if self.task.field_mappings:
            return [m['source'] for m in self.task.field_mappings]
        return ["*"]

    def _get_target_columns(self) -> list:
        """
        获取目标表字段列表

        Returns:
            字段名列表
        """
        if self.task.field_mappings:
            return [m['target'] for m in self.task.field_mappings]
        return ["*"]

    def _build_partition_expr(self) -> str:
        """
        构建分区表达式（新模型不使用分区配置，返回空）

        Returns:
            分区表达式字符串
        """
        return ""

    def _build_transformers(self) -> list:
        """
        构建字段转换规则

        Returns:
            转换规则列表
        """
        transformers = []
        for mapping in self.task.field_mappings:
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
