from rest_framework import serializers
from .models import User, Dept, Role, UserRole, Menu, DictType, DictData
from .common import snake_to_camel

class CamelCaseModelSerializer(serializers.ModelSerializer):
    camelize = True
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not getattr(self, 'camelize', True):
            return data
        return { snake_to_camel(k): v for k, v in data.items() }

class PaginationQuerySerializer(serializers.Serializer):
    pageNum = serializers.IntegerField(required=False, min_value=1, default=1)
    pageSize = serializers.IntegerField(required=False, min_value=1, default=10)

# User related
class UserQuerySerializer(PaginationQuerySerializer):
    userName = serializers.CharField(required=False, allow_blank=True)
    phonenumber = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(required=False, choices=['0','1'])
    deptId = serializers.IntegerField(required=False)
    beginTime = serializers.DateTimeField(required=False)
    endTime = serializers.DateTimeField(required=False)

class ResetPwdSerializer(serializers.Serializer):
    userId = serializers.IntegerField()
    password = serializers.CharField(min_length=6, max_length=128)

class ChangeStatusSerializer(serializers.Serializer):
    userId = serializers.IntegerField()
    status = serializers.ChoiceField(choices=['0','1'])

class UpdatePwdSerializer(serializers.Serializer):
    oldPassword = serializers.CharField(min_length=6, max_length=128)
    newPassword = serializers.CharField(min_length=6, max_length=128)

class AvatarSerializer(serializers.Serializer):
    avatar = serializers.CharField()

class AuthRoleAssignSerializer(serializers.Serializer):
    userId = serializers.IntegerField()
    roleIds = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)

class AuthRoleQuerySerializer(serializers.Serializer):
    userId = serializers.IntegerField()

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
        return list(UserRole.objects.filter(user=obj).values_list('role_id', flat=True))
    
    def get_postIds(self, obj):
        return []

class UserInfoSerializer(serializers.Serializer):
    userId = serializers.IntegerField()
    userName = serializers.CharField()
    nickName = serializers.CharField()
    avatar = serializers.CharField()
    phonenumber = serializers.CharField()
    email = serializers.CharField()
    sex = serializers.CharField()
    class Meta:
        model = User
        fields = ['userId', 'userName', 'nickName', 'avatar', 'phonenumber', 'email', 'sex']

# Dept related
class DeptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dept
        fields = '__all__'

# Role related
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

# Menu related
class MenuQuerySerializer(PaginationQuerySerializer):
    menuName = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(required=False, choices=['0','1'])

class MenuCreateSerializer(serializers.Serializer):
    parentId = serializers.IntegerField(required=False, default=0)
    menuName = serializers.CharField(max_length=50)
    orderNum = serializers.IntegerField(required=False, default=0)
    path = serializers.CharField(required=False, allow_blank=True, default='')
    component = serializers.CharField(required=False, allow_blank=True, default='')
    query = serializers.CharField(required=False, allow_blank=True, default='')
    isFrame = serializers.ChoiceField(choices=['0','1'], default='1')
    isCache = serializers.ChoiceField(choices=['0','1'], default='0')
    menuType = serializers.ChoiceField(choices=['M','C','F'], default='M')
    visible = serializers.ChoiceField(choices=['0','1'], default='0')
    status = serializers.ChoiceField(choices=['0','1'], default='0')
    perms = serializers.CharField(required=False, allow_blank=True, default='')
    icon = serializers.CharField(required=False, allow_blank=True, default='')
    remark = serializers.CharField(required=False, allow_blank=True, default='')

class MenuUpdateSerializer(MenuCreateSerializer):
    menuId = serializers.IntegerField()

class MenuSerializer(serializers.ModelSerializer):
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

# DictType related
class DictTypeQuerySerializer(PaginationQuerySerializer):
    dictName = serializers.CharField(required=False, allow_blank=True)
    dictType = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(required=False, choices=['0','1'])

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

# DictData related
class DictDataQuerySerializer(PaginationQuerySerializer):
    dictLabel = serializers.CharField(required=False, allow_blank=True)
    dictType = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(required=False, choices=['0','1'])

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