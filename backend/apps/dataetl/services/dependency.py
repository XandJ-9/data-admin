"""
DependencyService - ETL任务依赖管理服务
处理任务依赖关系的验证、检查和查询
"""

import logging
from typing import List, Set, Optional
from django.db import transaction
from apps.dataetl.models import ETLTask, ETLTaskDependency
from apps.datataskmonitor.models import TaskExecution

logger = logging.getLogger(__name__)


class DependencyService:
    """
    ETL任务依赖服务
    提供依赖验证、依赖检查、循环检测等功能
    """

    @staticmethod
    def check_dependencies_satisfied(task_id: int) -> tuple[bool, List[str]]:
        """
        检查任务的所有依赖是否已满足

        Args:
            task_id: 任务ID

        Returns:
            tuple[bool, List[str]]: (是否满足, 未满足的依赖说明列表)
        """
        try:
            task = ETLTask.objects.get(id=task_id)
            dependencies = ETLTaskDependency.objects.filter(successor=task)

            if not dependencies.exists():
                return True, []

            unsatisfied = []

            for dep in dependencies:
                predecessor = dep.predecessor

                # 检查前置任务的最新执行状态
                latest_execution = TaskExecution.objects.filter(
                    task_type='etl',
                    task_id=predecessor.id
                ).order_by('-start_time').first()

                if not latest_execution:
                    unsatisfied.append(f"前置任务 '{predecessor.name}' 尚未执行")
                    continue

                if latest_execution.status == 'running':
                    unsatisfied.append(f"前置任务 '{predecessor.name}' 正在运行中")
                elif latest_execution.status == 'failed':
                    unsatisfied.append(f"前置任务 '{predecessor.name}' 执行失败: {latest_execution.error_message}")
                elif latest_execution.status == 'cancelled':
                    unsatisfied.append(f"前置任务 '{predecessor.name}' 已取消")

            return len(unsatisfied) == 0, unsatisfied

        except ETLTask.DoesNotExist:
            logger.error(f"ETLTask #{task_id} not found")
            return False, ["任务不存在"]

    @staticmethod
    def get_dependent_tasks(task_id: int) -> List[ETLTask]:
        """
        获取依赖于指定任务的所有任务

        Args:
            task_id: 任务ID

        Returns:
            List[ETLTask]: 依赖此任务的任务列表
        """
        try:
            task = ETLTask.objects.get(id=task_id)
            dependencies = ETLTaskDependency.objects.filter(predecessor=task)
            return [dep.successor for dep in dependencies]
        except ETLTask.DoesNotExist:
            return []

    @staticmethod
    def get_predecessor_tasks(task_id: int) -> List[ETLTask]:
        """
        获取指定任务的所有前置依赖任务

        Args:
            task_id: 任务ID

        Returns:
            List[ETLTask]: 前置依赖任务列表
        """
        try:
            task = ETLTask.objects.get(id=task_id)
            dependencies = ETLTaskDependency.objects.filter(successor=task)
            return [dep.predecessor for dep in dependencies]
        except ETLTask.DoesNotExist:
            return []

    @staticmethod
    def validate_no_cycles(task_id: int, dependency_id: int) -> tuple[bool, str]:
        """
        验证添加依赖不会导致循环依赖

        使用深度优先搜索检测循环

        Args:
            task_id: 当前任务ID (successor)
            dependency_id: 要添加的依赖任务ID (predecessor)

        Returns:
            tuple[bool, str]: (是否有效, 错误消息)
        """
        if task_id == dependency_id:
            return False, "任务不能依赖自己"

        # 检查是否会导致循环: dependency_id 是否已经依赖 task_id
        def has_path(from_id: int, to_id: int, visited: Optional[Set[int]] = None) -> bool:
            """检查是否存在从 from_id 到 to_id 的路径"""
            if visited is None:
                visited = set()

            if from_id in visited:
                return False

            if from_id == to_id:
                return True

            visited.add(from_id)

            # 获取 from_id 的所有前置任务
            predecessors = DependencyService.get_predecessor_tasks(from_id)
            for pred in predecessors:
                if has_path(pred.id, to_id, visited.copy()):
                    return True

            return False

        # 如果 dependency_id 已经可以到达 task_id，则添加 task_id -> dependency_id 会形成循环
        if has_path(dependency_id, task_id):
            return False, f"添加此依赖会导致循环: {task_id} -> {dependency_id} -> ... -> {task_id}"

        return True, ""

    @staticmethod
    @transaction.atomic
    def add_dependency(task_id: int, dependency_id: int) -> tuple[bool, str]:
        """
        添加任务依赖

        Args:
            task_id: 任务ID (successor)
            dependency_id: 依赖任务ID (predecessor)

        Returns:
            tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 验证任务存在
            try:
                successor = ETLTask.objects.get(id=task_id)
            except ETLTask.DoesNotExist:
                return False, f"任务 #{task_id} 不存在"

            try:
                predecessor = ETLTask.objects.get(id=dependency_id)
            except ETLTask.DoesNotExist:
                return False, f"依赖任务 #{dependency_id} 不存在"

            # 验证没有循环依赖
            is_valid, error_msg = DependencyService.validate_no_cycles(task_id, dependency_id)
            if not is_valid:
                return False, error_msg

            # 检查是否已存在
            if ETLTaskDependency.objects.filter(
                predecessor=predecessor,
                successor=successor
            ).exists():
                return False, "依赖关系已存在"

            # 创建依赖
            ETLTaskDependency.objects.create(
                predecessor=predecessor,
                successor=successor
            )

            logger.info(f"Added dependency: {successor.name} depends on {predecessor.name}")
            return True, "依赖添加成功"

        except Exception as e:
            logger.error(f"Failed to add dependency: {e}")
            return False, f"添加依赖失败: {str(e)}"

    @staticmethod
    @transaction.atomic
    def remove_dependency(task_id: int, dependency_id: int) -> tuple[bool, str]:
        """
        移除任务依赖

        Args:
            task_id: 任务ID (successor)
            dependency_id: 依赖任务ID (predecessor)

        Returns:
            tuple[bool, str]: (是否成功, 消息)
        """
        try:
            try:
                successor = ETLTask.objects.get(id=task_id)
            except ETLTask.DoesNotExist:
                return False, f"任务 #{task_id} 不存在"

            try:
                predecessor = ETLTask.objects.get(id=dependency_id)
            except ETLTask.DoesNotExist:
                return False, f"依赖任务 #{dependency_id} 不存在"

            # 删除依赖
            deleted, _ = ETLTaskDependency.objects.filter(
                predecessor=predecessor,
                successor=successor
            ).delete()

            if deleted == 0:
                return False, "依赖关系不存在"

            logger.info(f"Removed dependency: {successor.name} no longer depends on {predecessor.name}")
            return True, "依赖移除成功"

        except Exception as e:
            logger.error(f"Failed to remove dependency: {e}")
            return False, f"移除依赖失败: {str(e)}"

    @staticmethod
    def get_dependency_chain(task_id: int) -> List[ETLTask]:
        """
        获取任务的完整依赖链（包括所有前置任务的前置任务）

        Args:
            task_id: 任务ID

        Returns:
            List[ETLTask]: 依赖链，按依赖顺序排序（最前面的任务优先执行）
        """
        visited = set()
        chain = []

        def dfs(task: ETLTask):
            if task.id in visited:
                return
            visited.add(task.id)

            # 先添加所有前置任务
            predecessors = DependencyService.get_predecessor_tasks(task.id)
            for pred in predecessors:
                dfs(pred)

            # 然后添加当前任务
            if task.id not in [t.id for t in chain]:
                chain.append(task)

        try:
            task = ETLTask.objects.get(id=task_id)
            dfs(task)
            return chain
        except ETLTask.DoesNotExist:
            return []

    @staticmethod
    def can_execute_task(task_id: int) -> tuple[bool, str]:
        """
        检查任务是否可以执行（所有依赖都已满足且任务状态为启用）

        Args:
            task_id: 任务ID

        Returns:
            tuple[bool, str]: (是否可以执行, 原因说明)
        """
        try:
            task = ETLTask.objects.get(id=task_id)

            # 检查任务状态
            if task.status == '1':
                return False, "任务已停用"

            # 检查依赖
            satisfied, unsatisfied = DependencyService.check_dependencies_satisfied(task_id)
            if not satisfied:
                reasons = "; ".join(unsatisfied)
                return False, f"依赖未满足: {reasons}"

            return True, ""

        except ETLTask.DoesNotExist:
            return False, "任务不存在"


# 便捷函数别名
check_dependencies_satisfied = DependencyService.check_dependencies_satisfied
get_dependent_tasks = DependencyService.get_dependent_tasks
get_predecessor_tasks = DependencyService.get_predecessor_tasks
validate_no_cycles = DependencyService.validate_no_cycles
add_dependency = DependencyService.add_dependency
remove_dependency = DependencyService.remove_dependency
get_dependency_chain = DependencyService.get_dependency_chain
can_execute_task = DependencyService.can_execute_task
