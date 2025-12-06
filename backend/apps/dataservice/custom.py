# 接口导出（样式化 Excel）相关方法
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side
from .models import InterfaceInfo, InterfaceField

DefaultStyle={
    "font" : Font(name='Calibri',
                    size=11,
                    bold=True,
                    italic=False,
                    vertAlign=None,
                    underline='none',
                    strike=False,
                    color='FF000000'),
    'fill' : PatternFill(patternType='solid',fgColor="99CCFF"),
    'border' : Border(left=Side(border_style='thin', color='FF000000'),
                    right=Side(border_style='thin',color='FF000000'),
                    top=Side(border_style='thin',color='FF000000'),
                    bottom=Side(border_style='thin',color='FF000000')
                )
}

def set_area_border(ws,start_row,end_row,start_col,end_col):
    for row in range(start_row,end_row+1):
        for col in range(start_col,end_col+1):
            ws.cell(row=row,column=col).border = DefaultStyle['border']

def make_interface_workbook(interface: InterfaceInfo, fields):
    """
    生成样式化的接口导出工作簿：
    - 顶部信息区（名称、编码、各开关、数据库信息、SQL 等）
    - 字段列表（按输入参数、输出参数顺序）
    返回 openpyxl.Workbook
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "report"

    template_info = [
        {'position': 'A1', 'name': '模块名称'},
        {'position': 'C1', 'name': '报表名称'},
        {'position': 'E1', 'name': '报表平台'},
        {'position': 'A2', 'name': '接口名称'},
        {'position': 'C2', 'name': '接口代码'},
        {'position': 'E2', 'name': '日期选项'},
        {'position': 'G2', 'name': '二级表头'},
        {'position': 'I2', 'name': '需要登录'},
        {'position': 'K2', 'name': '告警方式'},
        {'position': 'A3', 'name': '数据库类型'},
        {'position': 'C3', 'name': '数据库名称'},
        {'position': 'E3', 'name': '接口sql'},
        {'position': 'A4', 'name': '是否分页'},
        {'position': 'C4', 'name': '是否合计'},
        {'position': 'E4', 'name': '合计sql'},
    ]
    for info in template_info:
        cell = ws[info['position']]
        cell.value = info['name']
        cell.font = DefaultStyle['font']
        cell.fill = DefaultStyle['fill']
        cell.border = DefaultStyle['border']

    # 顶部信息填充（报告信息暂无，置空）
    ws['B1'] = ''
    ws['D1'] = ''
    ws['F1'] = ''

    ws['B2'] = interface.interface_name
    ws['D2'] = interface.interface_code
    ws['F2'] = '是' if interface.is_date_option == '1' else '否'
    ws['H2'] = '是' if interface.is_second_table == '1' else '否'
    ws['J2'] = '是' if interface.is_login_visit == '1' else '否'
    # 报警类型显示值
    try:
        ws['L2'] = interface.get_alarm_type_display()
    except Exception:
        ws['L2'] = interface.alarm_type

    ws['B3'] = interface.interface_db_type
    ws['D3'] = interface.interface_db_name
    ws['F3'] = interface.interface_sql or ''
    ws['B4'] = '是' if interface.is_paging == '1' else '否'
    ws['D4'] = '是' if interface.is_total == '1' else '否'
    ws['F4'] = interface.total_sql or ''

    # 列头
    column_headers = [
        {'label': '序号'},
        {'label': '参数名称'},
        {'label': '参数代码'},
        {'label': '参数类型'},
        {'label': '数据类型'},
        {'label': '是否展示'},
        {'label': '是否导出'},
        {'label': '参数接口代码'},
        {'label': '参数默认值'},
        {'label': '级联参数'},
        {'label': '父表头名称'},
        {'label': '父表头位置'},
        {'label': '是否合并行'},
        {'label': '是否显示备注'},
        {'label': '参数描述'},
    ]
    for index, column_info in enumerate(column_headers):
        cell = ws.cell(row=5, column=index + 1)
        cell.font = DefaultStyle['font']
        cell.fill = PatternFill(patternType='solid', fgColor='C0C0C0')
        cell.value = column_info.get('label')

    # 字段列表：输入参数在前，输出参数在后
    fields_sorted = list(fields) if fields is not None else []
    fields_sorted.sort(key=lambda x: (x.interface_para_type, x.interface_para_position))
    fields_type_input = [f for f in fields_sorted if getattr(f, 'interface_para_type', '') == '1']
    fields_type_output = [f for f in fields_sorted if getattr(f, 'interface_para_type', '') == '2']
    ordered_fields = fields_type_input + fields_type_output

    for row_index, f in enumerate(ordered_fields):
        # 逐列写入
        values = [
            f.interface_para_position,
            f.interface_para_name,
            f.interface_para_code,
            getattr(f, 'get_interface_para_type_display', lambda: f.interface_para_type)(),
            getattr(f, 'get_interface_data_type_display', lambda: f.interface_data_type)(),
            '是' if f.interface_show_flag == '1' else '否',
            '是' if f.interface_export_flag == '1' else '否',
            f.interface_para_interface_code or '',
            f.interface_para_default or '',
            f.interface_cascade_para or '',
            f.interface_parent_name or '',
            f.interface_parent_position if f.interface_parent_position is not None else '',
            # 跨行显示
            getattr(f, 'get_interface_para_rowspan_display', lambda: f.interface_para_rowspan)() if f.interface_para_rowspan is not None else '',
            f.interface_show_desc or '',
            f.interface_para_desc or '',
        ]
        for col_index, val in enumerate(values):
            ws.cell(row=row_index + 6, column=1 + col_index).value = val

    set_area_border(ws, ws.min_row, ws.max_row, ws.min_column, ws.max_column)
    ws['P1'] = 'report'
    return wb

def build_interface_workbook_bytes(interface: InterfaceInfo, fields) -> bytes:
    """构建 Excel 并返回二进制内容"""
    wb = make_interface_workbook(interface, fields)
    import io
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
