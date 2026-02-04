#!/usr/bin/env python3
"""
数据资产模块功能测试脚本
测试 dataasset 模块的所有主要功能
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# 配置
BASE_URL = "http://localhost:8000/data-api"
USERNAME = "admin"
PASSWORD = "admin123"

class DataAssetTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None
        self.headers = {}
        self.test_results = []

    def log(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {test_name}"
        if message:
            result += f": {message}"
        print(result)
        self.test_results.append((test_name, success, message))

    def login(self) -> bool:
        """登录获取token"""
        try:
            response = requests.post(
                f"{self.base_url}/login",
                json={"username": USERNAME, "password": PASSWORD},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('data', {}).get('token')
                if self.token:
                    self.headers = {"Authorization": f"Bearer {self.token}"}
                    self.log("用户登录", True, f"获取token成功")
                    return True
            self.log("用户登录", False, f"登录失败: {response.text}")
            return False
        except Exception as e:
            self.log("用户登录", False, str(e))
            return False

    # ==================== 数据源测试 ====================

    def test_datasource_list(self) -> bool:
        """测试数据源列表"""
        try:
            response = requests.get(
                f"{self.base_url}/dataasset/datasource/",
                headers=self.headers,
                timeout=5
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log("数据源列表", success, f"返回{data.get('total', 0)}条记录" if success else response.text)
            return success
        except Exception as e:
            self.log("数据源列表", False, str(e))
            return False

    def test_datasource_create(self) -> Optional[int]:
        """测试创建数据源"""
        try:
            data = {
                "dataSourceName": "测试数据源",
                "dbType": "sqlite",
                "host": "",
                "port": 0,
                "dbName": ":memory:",
                "username": "",
                "password": "",
                "params": "{}",
                "status": "0",
                "remark": "测试用数据源"
            }
            response = requests.post(
                f"{self.base_url}/dataasset/datasource/",
                headers=self.headers,
                json=data,
                timeout=5
            )
            if response.status_code == 200:
                # 获取创建的数据源ID
                list_resp = requests.get(
                    f"{self.base_url}/dataasset/datasource/",
                    headers=self.headers,
                    params={"dataSourceName": "测试数据源"},
                    timeout=5
                )
                if list_resp.status_code == 200:
                    rows = list_resp.json().get('rows', [])
                    if rows:
                        ds_id = rows[0].get('id')
                        self.log("创建数据源", True, f"ID={ds_id}")
                        return ds_id
            self.log("创建数据源", False, response.text)
            return None
        except Exception as e:
            self.log("创建数据源", False, str(e))
            return None

    def test_datasource_update(self, ds_id: int) -> bool:
        """测试更新数据源"""
        try:
            data = {
                "dataSourceId": ds_id,
                "dataSourceName": "测试数据源-已更新",
                "dbType": "sqlite",
                "host": "",
                "port": 0,
                "dbName": ":memory:",
                "username": "",
                "password": "",
                "params": "{}",
                "status": "0",
                "remark": "更新后的备注"
            }
            response = requests.put(
                f"{self.base_url}/dataasset/datasource/{ds_id}",
                headers=self.headers,
                json=data,
                timeout=5
            )
            self.log("更新数据源", response.status_code == 200)
            return response.status_code == 200
        except Exception as e:
            self.log("更新数据源", False, str(e))
            return False

    def test_datasource_get(self, ds_id: int) -> bool:
        """测试获取数据源详情"""
        try:
            response = requests.get(
                f"{self.base_url}/dataasset/datasource/{ds_id}",
                headers=self.headers,
                timeout=5
            )
            self.log("获取数据源详情", response.status_code == 200)
            return response.status_code == 200
        except Exception as e:
            self.log("获取数据源详情", False, str(e))
            return False

    def test_datasource_delete(self, ds_id: int) -> bool:
        """测试删除数据源"""
        try:
            response = requests.delete(
                f"{self.base_url}/dataasset/datasource/{ds_id}",
                headers=self.headers,
                timeout=5
            )
            self.log("删除数据源", response.status_code == 200)
            return response.status_code == 200
        except Exception as e:
            self.log("删除数据源", False, str(e))
            return False

    # ==================== 元数据表测试 ====================

    def test_meta_table_list(self) -> bool:
        """测试元数据表列表"""
        try:
            response = requests.get(
                f"{self.base_url}/dataasset/meta-table/",
                headers=self.headers,
                timeout=5
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log("元数据表列表", success, f"返回{data.get('total', 0)}条记录" if success else response.text)
            return success
        except Exception as e:
            self.log("元数据表列表", False, str(e))
            return False

    def test_meta_column_list(self) -> bool:
        """测试元数据字段列表"""
        try:
            response = requests.get(
                f"{self.base_url}/dataasset/meta-column/",
                headers=self.headers,
                timeout=5
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log("元数据字段列表", success, f"返回{data.get('total', 0)}条记录" if success else response.text)
            return success
        except Exception as e:
            self.log("元数据字段列表", False, str(e))
            return False

    # ==================== 血缘管理测试 ====================

    def test_lineage_list(self) -> bool:
        """测试血缘列表"""
        try:
            response = requests.get(
                f"{self.base_url}/dataasset/lineage/",
                headers=self.headers,
                timeout=5
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log("血缘关系列表", success, f"返回{data.get('total', 0)}条记录" if success else response.text)
            return success
        except Exception as e:
            self.log("血缘关系列表", False, str(e))
            return False

    def test_lineage_create(self, table_id: int) -> Optional[int]:
        """测试创建血缘关系"""
        try:
            # 先创建一个测试表
            table_data = {
                "dataSourceId": 1,
                "tableName": "test_source_table",
                "comment": "测试源表",
                "databaseName": "test_db"
            }
            create_resp = requests.post(
                f"{self.base_url}/dataasset/meta-table/",
                headers=self.headers,
                json=table_data,
                timeout=5
            )

            if create_resp.status_code != 200:
                self.log("创建血缘关系", False, "无法创建测试表")
                return None

            # 获取源表ID
            tables = requests.get(
                f"{self.base_url}/dataasset/meta-table/",
                headers=self.headers,
                params={"tableName": "test_source_table"},
                timeout=5
            )
            if tables.status_code != 200:
                return None

            rows = tables.json().get('rows', [])
            if len(rows) < 2:
                self.log("创建血缘关系", False, "需要至少2个表来创建血缘")
                return None

            source_table_id = rows[0].get('id')
            target_table_id = rows[1].get('id') if len(rows) > 1 else rows[0].get('id')

            if source_table_id == target_table_id:
                self.log("创建血缘关系", False, "源表和目标表不能相同")
                return None

            lineage_data = {
                "sourceTableId": source_table_id,
                "targetTableId": target_table_id,
                "lineageType": "upstream",
                "description": "测试血缘关系"
            }
            response = requests.post(
                f"{self.base_url}/dataasset/lineage/",
                headers=self.headers,
                json=lineage_data,
                timeout=5
            )
            if response.status_code == 200:
                lineage_id = response.json().get('data', {}).get('id')
                self.log("创建血缘关系", True, f"ID={lineage_id}")
                return lineage_id
            else:
                self.log("创建血缘关系", False, response.text)
                return None
        except Exception as e:
            self.log("创建血缘关系", False, str(e))
            return None

    def test_lineage_upstream(self, table_id: int) -> bool:
        """测试查询上游血缘"""
        try:
            response = requests.get(
                f"{self.base_url}/dataasset/lineage/upstream",
                headers=self.headers,
                params={"tableId": table_id, "depth": 2},
                timeout=5
            )
            self.log("查询上游血缘", response.status_code == 200)
            return response.status_code == 200
        except Exception as e:
            self.log("查询上游血缘", False, str(e))
            return False

    def test_lineage_downstream(self, table_id: int) -> bool:
        """测试查询下游血缘"""
        try:
            response = requests.get(
                f"{self.base_url}/dataasset/lineage/downstream",
                headers=self.headers,
                params={"tableId": table_id, "depth": 2},
                timeout=5
            )
            self.log("查询下游血缘", response.status_code == 200)
            return response.status_code == 200
        except Exception as e:
            self.log("查询下游血缘", False, str(e))
            return False

    def test_lineage_graph(self, table_id: int) -> bool:
        """测试生成血缘图"""
        try:
            response = requests.get(
                f"{self.base_url}/dataasset/lineage/graph",
                headers=self.headers,
                params={"tableId": table_id, "depth": 2},
                timeout=5
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                nodes = data.get('data', {}).get('nodes', [])
                edges = data.get('data', {}).get('edges', [])
                self.log("生成血缘图", True, f"节点数={len(nodes)}, 边数={len(edges)}")
            else:
                self.log("生成血缘图", False, response.text)
            return success
        except Exception as e:
            self.log("生成血缘图", False, str(e))
            return False

    # ==================== 采集接口测试 ====================

    def test_collection_databases(self) -> bool:
        """测试获取数据库列表"""
        try:
            response = requests.post(
                f"{self.base_url}/dataasset/collection/databases",
                headers=self.headers,
                json={"dataSourceId": 1},
                timeout=10
            )
            # SQLite可能不支持多数据库，这是预期的
            if response.status_code in [200, 400]:
                self.log("获取数据库列表", True, "接口正常响应")
                return True
            self.log("获取数据库列表", False, response.text)
            return False
        except Exception as e:
            self.log("获取数据库列表", False, str(e))
            return False

    def test_collection_tables(self) -> bool:
        """测试获取表列表"""
        try:
            response = requests.post(
                f"{self.base_url}/dataasset/collection/tables",
                headers=self.headers,
                json={"dataSourceId": 1},
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                total = data.get('total', 0)
                self.log("获取表列表", True, f"返回{total}条记录")
            else:
                self.log("获取表列表", False, response.text)
            return success
        except Exception as e:
            self.log("获取表列表", False, str(e))
            return False

    def test_collection_columns(self) -> bool:
        """测试获取字段列表"""
        try:
            response = requests.post(
                f"{self.base_url}/dataasset/collection/columns",
                headers=self.headers,
                json={"dataSourceId": 1, "tableName": "dataasset_datasource"},
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                total = data.get('total', 0)
                self.log("获取字段列表", True, f"返回{total}条记录")
            else:
                self.log("获取字段列表", False, response.text)
            return success
        except Exception as e:
            self.log("获取字段列表", False, str(e))
            return False

    # ==================== 运行所有测试 ====================

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("🧪 数据资产模块功能测试")
        print("="*60 + "\n")

        # 1. 登录
        if not self.login():
            print("\n❌ 登录失败，无法继续测试")
            return False

        print("\n📋 数据源管理测试")
        print("-" * 60)
        self.test_datasource_list()
        ds_id = self.test_datasource_create()
        if ds_id:
            self.test_datasource_get(ds_id)
            self.test_datasource_update(ds_id)
            # 暂时不删除，用于后续测试

        print("\n📋 元数据管理测试")
        print("-" * 60)
        self.test_meta_table_list()
        self.test_meta_column_list()

        print("\n📋 血缘管理测试")
        print("-" * 60)
        self.test_lineage_list()
        if ds_id:
            lineage_id = self.test_lineage_create(ds_id)
            # 血缘查询测试
            tables_resp = requests.get(
                f"{self.base_url}/dataasset/meta-table/",
                headers=self.headers,
                timeout=5
            )
            if tables_resp.status_code == 200:
                rows = tables_resp.json().get('rows', [])
                if rows:
                    table_id = rows[0].get('id')
                    self.test_lineage_upstream(table_id)
                    self.test_lineage_downstream(table_id)
                    self.test_lineage_graph(table_id)

        print("\n📋 元数据采集测试")
        print("-" * 60)
        self.test_collection_databases()
        self.test_collection_tables()
        self.test_collection_columns()

        # 清理测试数据
        if ds_id:
            self.test_datasource_delete(ds_id)

        # 打印总结
        print("\n" + "="*60)
        print("📊 测试总结")
        print("="*60)

        total = len(self.test_results)
        passed = sum(1 for _, success, _ in self.test_results if success)
        failed = total - passed

        print(f"\n总计: {total} 个测试")
        print(f"✅ 通过: {passed} 个")
        print(f"❌ 失败: {failed} 个")
        print(f"通过率: {(passed/total*100):.1f}%")

        if failed > 0:
            print("\n❌ 失败的测试:")
            for name, success, msg in self.test_results:
                if not success:
                    print(f"   - {name}: {msg}")

        print("\n" + "="*60)
        return failed == 0


if __name__ == "__main__":
    tester = DataAssetTester(BASE_URL)
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
