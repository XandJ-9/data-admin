from django.db import models
from apps.system.models import BaseModel

from apps.datasource.models import DataSource



class QueryLog(BaseModel):
    data_source = models.ForeignKey(DataSource, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='数据源')
    sql_text = models.TextField(verbose_name='SQL语句')
    username = models.CharField(max_length=64, verbose_name='用户名')
    status = models.CharField(max_length=10, choices=[('success', '成功'), ('fail', '失败')], default='success', verbose_name='执行状态')
    duration_ms = models.IntegerField(default=0, verbose_name='耗时(ms)')
    error_msg = models.CharField(max_length=500, blank=True, default='', verbose_name='错误信息')

    class Meta:
        db_table = 'datasource_query_log'
        verbose_name = '数据查询日志'
        verbose_name_plural = '数据查询日志'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['status']),
            models.Index(fields=['data_source']),
            models.Index(fields=['del_flag']),
        ]

    def __str__(self):
        return f"{self.username} - {self.status} - {self.duration_ms}ms"


# 接口信息
class InterfaceInfo(BaseModel):
    IS_TOTAL_CHOICES = (('1', '是'), ('0', '否'))
    IS_PAGING_CHOICE = (('1', '是'), ('0', '否'))
    IS_DATA_OPTION_CHOICE = (('1', '是'), ('0', '否'))
    IS_SECODN_TABLE_CHOICE = (('1', '是'), ('0', '否'))
    IS_LOGIN_VISIT_CHOICE = (('1', '是'), ('0', '否'))
    ALARM_TYPE_CHOICES = (('0', '否'), ('1', '邮件'), ('2', '短信'), ('3', '钉钉'), ('4', '企业微信'), ('5', '电话'), ('6', '飞书'))

    # 说明：原需求为 ForeignKey(ReportInfo)，项目中暂未提供 ReportInfo 模型，遵循最小改动，这里保存报表 ID
    report_id = models.IntegerField(verbose_name='报表ID', null=True, blank=True)

    interface_name = models.CharField(max_length=255, verbose_name='接口名称')
    interface_code = models.CharField(max_length=255, unique=True, verbose_name='接口编码')
    interface_desc = models.TextField(verbose_name='接口描述', null=True, blank=True)
    interface_db_type = models.CharField(max_length=255, verbose_name='数据库类型')
    interface_db_name = models.CharField(max_length=255, verbose_name='数据库名称')
    interface_sql = models.TextField(verbose_name='接口sql', null=True, blank=True)

    is_total = models.CharField(default='0', max_length=1, choices=IS_TOTAL_CHOICES, verbose_name='是否合计')
    total_sql = models.TextField(verbose_name='合计sql', null=True, blank=True)
    is_paging = models.CharField(default='0', max_length=1, choices=IS_PAGING_CHOICE, verbose_name='是否分页')
    is_date_option = models.CharField(default='0', max_length=1, choices=IS_DATA_OPTION_CHOICE, verbose_name='是否日期查询')
    is_second_table = models.CharField(default='0', max_length=1, choices=IS_SECODN_TABLE_CHOICE, verbose_name='二级表头')
    is_login_visit = models.CharField(default='0', max_length=1, choices=IS_LOGIN_VISIT_CHOICE, verbose_name='是否登陆验证')
    alarm_type = models.CharField(default='0', max_length=1, choices=ALARM_TYPE_CHOICES, verbose_name='报警类型')

    user_name = models.CharField(max_length=255, verbose_name='用户名称', null=True, blank=True)
    interface_datasource = models.IntegerField(verbose_name='数据源ID', null=True, blank=True)

    class Meta:
        db_table = 'dataservice_interface_info'
        verbose_name = '数据接口信息'
        verbose_name_plural = '数据接口信息'
        indexes = [
            models.Index(fields=['interface_code']),
            models.Index(fields=['del_flag']),
        ]

    def __str__(self):
        return self.interface_name


# 接口字段信息
class InterfaceField(BaseModel):
    DATA_TYPE_CHOICES = (
        ('1', '字符'),
        ('2', '整数'),
        ('3', '小数'),
        ('4', '百分比'),
        ('5', '无格式整数'),
        ('6', '无格式小数'),
        ('7', '无格式百分比'),
        ('8', '1位百分比'),
        ('9', '1位小数'),
        ('10', '年份'),
        ('11', '日期'),
        ('12', '月份'),
        ('13', '单选'),
        ('14', '多选'),
        ('15', '文本'),
    )
    SHOW_FLAG_CHOICES = (('1', '是'), ('0', '否'))
    EXPORT_FLAG_CHOICES = (('1', '是'), ('0', '否'))
    PARA_TYPE_CHOICES = (('1', '输入参数'), ('2', '输出参数'))
    ROWSPAN_CHOICES = ((1, '是'), (0, '否'))

    interface = models.ForeignKey(InterfaceInfo, verbose_name='接口', on_delete=models.CASCADE)
    interface_para_code = models.CharField(max_length=255, verbose_name='接口参数编码')
    interface_para_name = models.CharField(max_length=255, verbose_name='接口参数名称')
    interface_para_position = models.IntegerField(verbose_name='接口参数位置')
    interface_para_type = models.CharField(max_length=255, choices=PARA_TYPE_CHOICES, verbose_name='接口参数类型')
    interface_data_type = models.CharField(max_length=255, choices=DATA_TYPE_CHOICES, verbose_name='接口参数数据类型')
    interface_para_default = models.CharField(max_length=255, verbose_name='接口参数默认值', null=True, blank=True)

    interface_para_rowspan = models.IntegerField(verbose_name='接口参数跨行', null=True, blank=True, choices=ROWSPAN_CHOICES)
    interface_parent_name = models.CharField(max_length=255, verbose_name='接口参数父级名称', null=True, blank=True)
    interface_parent_position = models.IntegerField(verbose_name='接口参数父级位置', null=True, blank=True)
    interface_para_interface_code = models.CharField(max_length=255, verbose_name='接口参数接口编码', null=True, blank=True)
    interface_cascade_para = models.CharField(max_length=255, verbose_name='接口参数级联参数', null=True, blank=True)
    interface_show_flag = models.CharField(max_length=255, choices=SHOW_FLAG_CHOICES, default='1', verbose_name='接口参数是否显示')
    interface_export_flag = models.CharField(max_length=255, choices=EXPORT_FLAG_CHOICES, default='1', verbose_name='接口参数是否导出')
    interface_show_desc = models.CharField(max_length=255, verbose_name='接口参数显示名称', null=True, blank=True, choices=SHOW_FLAG_CHOICES)
    interface_para_desc = models.CharField(max_length=255, verbose_name='接口参数描述', null=True, blank=True)

    class Meta:
        db_table = 'dataservice_interface_field'
        verbose_name = '数据接口字段'
        verbose_name_plural = '数据接口字段'
        indexes = [
            models.Index(fields=['interface']),
            models.Index(fields=['del_flag']),
        ]

    def __str__(self):
        return f"{self.interface_para_name}({self.interface_para_code})"