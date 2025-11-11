from rest_framework import serializers
from .models import User, Dept, Role, UserRole, Menu, DictType, DictData

class DeptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dept
        fields = '__all__'

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    dept = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'nick_name', 'phonenumber', 'email', 'sex', 'avatar', 'status', 
                 'remark', 'dept_id', 'dept', 'create_by', 'update_by', 'create_time', 'update_time']
    
    def get_dept(self, obj):
        if obj.dept_id:
            try:
                dept = Dept.objects.get(dept_id=obj.dept_id)
                return {
                    'deptId': dept.dept_id,
                    'deptName': dept.dept_name
                }
            except Dept.DoesNotExist:
                return None
        return None

class UserProfileSerializer(serializers.ModelSerializer):
    dept = serializers.SerializerMethodField()
    roleIds = serializers.SerializerMethodField()
    postIds = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'nick_name', 'phonenumber', 'email', 'sex', 'avatar', 
                 'dept_id', 'dept', 'roleIds', 'postIds']
    
    def get_dept(self, obj):
        if obj.dept_id:
            try:
                dept = Dept.objects.get(dept_id=obj.dept_id)
                return {
                    'deptId': dept.dept_id,
                    'deptName': dept.dept_name
                }
            except Dept.DoesNotExist:
                return None
        return None
    
    def get_roleIds(self, obj):
        # 获取用户关联的角色ID列表
        return list(UserRole.objects.filter(user=obj).values_list('role_id', flat=True))
    
    def get_postIds(self, obj):
        # 这里需要实现岗位关联，暂时返回空列表
        return []


class MenuSerializer(serializers.ModelSerializer):
    # 将数据库字段映射为前端期望的驼峰命名
    menuId = serializers.IntegerField(source='menu_id', read_only=True)
    parentId = serializers.IntegerField(source='parent_id')
    menuName = serializers.CharField(source='menu_name')
    orderNum = serializers.IntegerField(source='order_num')
    path = serializers.CharField()
    component = serializers.CharField(allow_blank=True)
    query = serializers.CharField(allow_blank=True)
    isFrame = serializers.CharField(source='is_frame')
    isCache = serializers.CharField(source='is_cache')
    menuType = serializers.CharField(source='menu_type')
    visible = serializers.CharField()
    status = serializers.CharField()
    perms = serializers.CharField(allow_blank=True)
    icon = serializers.CharField(allow_blank=True)
    createBy = serializers.CharField(source='create_by', required=False)
    updateBy = serializers.CharField(source='update_by', required=False)
    createTime = serializers.DateTimeField(source='create_time', read_only=True)
    updateTime = serializers.DateTimeField(source='update_time', read_only=True)
    remark = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Menu
        fields = ['menuId', 'parentId', 'menuName', 'orderNum', 'path', 'component', 'query', 'isFrame',
                  'isCache', 'menuType', 'visible', 'status', 'perms', 'icon', 'createBy', 'updateBy',
                  'createTime', 'updateTime', 'remark']


class DictTypeSerializer(serializers.ModelSerializer):
    dictId = serializers.IntegerField(source='dict_id', read_only=True)
    dictName = serializers.CharField(source='dict_name')
    dictType = serializers.CharField(source='dict_type')
    status = serializers.CharField()
    remark = serializers.CharField(allow_blank=True, required=False)
    createTime = serializers.DateTimeField(source='create_time', read_only=True)
    updateTime = serializers.DateTimeField(source='update_time', read_only=True)

    class Meta:
        model = DictType
        fields = ['dictId', 'dictName', 'dictType', 'status', 'remark', 'createTime', 'updateTime']


class DictDataSerializer(serializers.ModelSerializer):
    dictCode = serializers.IntegerField(source='dict_code', read_only=True)
    dictSort = serializers.IntegerField(source='dict_sort')
    dictLabel = serializers.CharField(source='dict_label')
    dictValue = serializers.CharField(source='dict_value')
    dictType = serializers.CharField(source='dict_type')
    cssClass = serializers.CharField(source='css_class', allow_blank=True, required=False)
    listClass = serializers.CharField(source='list_class', allow_blank=True)
    status = serializers.CharField()
    remark = serializers.CharField(allow_blank=True, required=False)
    createTime = serializers.DateTimeField(source='create_time', read_only=True)
    updateTime = serializers.DateTimeField(source='update_time', read_only=True)

    class Meta:
        model = DictData
        fields = ['dictCode', 'dictSort', 'dictLabel', 'dictValue', 'dictType', 'cssClass', 'listClass',
                  'status', 'remark', 'createTime', 'updateTime']