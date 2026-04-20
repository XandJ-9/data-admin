from __future__ import annotations

from typing import Any

from .models import InterfaceField, InterfaceInfo


class InterfaceQueryWrapper:
    """将内部查询结果包装为稳定的接口返回协议。"""

    PROPERTIES = {
        "paraCode": "interface_para_code",
        "paraDesc": "interface_para_desc",
        "dataType": "interface_data_type",
        "showFlag": "interface_show_flag",
        "parentName": "interface_parent_name",
        "paraInterface": "interface_para_interface_code",
        "exportFlag": "interface_export_flag",
        "showDesc": "interface_show_desc",
        "position": "interface_para_position",
        "parentPosition": "interface_parent_position",
        "paraName": "interface_para_name",
    }

    def __init__(self, interface: InterfaceInfo, executor: Any, offset: int = 0, page_size: int = 20):
        self.interface = interface
        self.executor = executor
        self.offset = max(int(offset or 0), 0)
        self.page_size = max(int(page_size or 20), 1)

    def execute(self, interface_sql: str, total_sql: str | None = None) -> dict[str, Any]:
        property_result = self._build_property_result()
        output_fields = self._get_output_fields()

        if self.interface.is_paging == '1':
            query_result = self.executor.execute_query(
                sql=interface_sql,
                page_size=self.page_size,
                offset=self.offset,
            )
            list_data = self._rows_to_dicts(query_result, output_fields)
            result = {
                'reportName': self.interface.report_name or '',
                'interfaceName': self.interface.interface_name,
                'isPaging': self.interface.is_paging,
                'isTotal': self.interface.is_total,
                'property': property_result,
                'code': '0',
                'message': 'success',
                'data': {
                    'list': list_data,
                    'total': self._count_total(interface_sql),
                },
            }
            if self.interface.is_total == '1' and total_sql:
                total_result = self.executor.execute_query(sql=total_sql)
                result['data']['totalList'] = self._rows_to_dicts(total_result, output_fields)
            return result

        query_result = self.executor.execute_query(sql=interface_sql)
        result = {
            'reportName': self.interface.report_name or '',
            'interfaceName': self.interface.interface_name,
            'isPaging': self.interface.is_paging,
            'isTotal': self.interface.is_total,
            'property': property_result,
            'code': '0',
            'message': 'success',
            'data': self._rows_to_dicts(query_result, output_fields),
        }
        if self.interface.is_total == '1' and total_sql:
            total_result = self.executor.execute_query(sql=total_sql)
            result['totaldata'] = self._rows_to_dicts(total_result, output_fields)
        return result

    def _get_output_fields(self) -> list[InterfaceField]:
        return list(
            InterfaceField.objects.filter(
                interface=self.interface,
                del_flag='0',
                interface_para_type='2',
            ).order_by('interface_para_position', 'id')
        )

    def _build_property_result(self) -> dict[str, dict[str, Any]]:
        interface_fields = InterfaceField.objects.filter(
            interface=self.interface,
            del_flag='0',
        ).order_by('interface_para_type', 'interface_para_position', 'id')
        property_result = {}
        for field in interface_fields:
            property_result[field.interface_para_code] = self.make_field_properties(field)
        return property_result

    def make_field_properties(self, interface_field: InterfaceField) -> dict[str, Any]:
        result = {}
        for output_key, attr_name in self.PROPERTIES.items():
            result[output_key] = getattr(interface_field, attr_name, '') or ''
        return result

    def _rows_to_dicts(self, query_result: dict[str, Any], output_fields: list[InterfaceField]) -> list[dict[str, Any]]:
        columns = list(query_result.get('columns') or [])
        rows = list(query_result.get('rows') or [])
        preferred_columns = [field.interface_para_code for field in output_fields] or columns
        final_columns = preferred_columns or columns

        result_rows = []
        for row in rows:
            if isinstance(row, dict):
                row_dict = row
            else:
                values = list(row) if isinstance(row, (list, tuple)) else [row]
                row_dict = {
                    column: values[index] if index < len(values) else None
                    for index, column in enumerate(columns)
                }
            result_rows.append({column: row_dict.get(column) for column in final_columns})
        return result_rows

    def _count_total(self, sql: str) -> int:
        normalized_sql = (sql or '').strip().rstrip(';')
        lowered_sql = normalized_sql.lower()
        if lowered_sql.startswith(('show', 'describe', 'explain')):
            return 0
        count_sql = f"SELECT COUNT(1) AS total_count FROM ({normalized_sql}) AS data_admin_total"
        count_result = self.executor.execute_query(sql=count_sql)
        rows = count_result.get('rows') or []
        if not rows:
            return 0
        first_row = rows[0]
        if isinstance(first_row, dict):
            value = next(iter(first_row.values()), 0)
        elif isinstance(first_row, (list, tuple)):
            value = first_row[0] if first_row else 0
        else:
            value = first_row
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
