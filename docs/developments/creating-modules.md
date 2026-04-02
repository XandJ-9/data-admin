# 创建新模块指南

## 后端模块

### 1. 创建 Django 应用

```bash
cd backend
uv run manage.py startapp mymodule apps/
```

### 2. 定义模型（`apps/mymodule/models.py`）

```python
from django.db import models
from apps.system.models import BaseModel

class MyModel(BaseModel):
    name = models.CharField(max_length=100, verbose_name='名称')
    status = models.CharField(max_length=1, choices=[('0', '正常'), ('1', '停用')], default='0')

    class Meta:
        db_table = 'my_model'
        indexes = [models.Index(fields=['del_flag', 'name'])]
```

### 3. 创建序列化器（`apps/mymodule/serializers.py`）

```python
from apps.system.serializers import BaseModelSerializer
from .models import MyModel

class MyModelSerializer(BaseModelSerializer):
    class Meta:
        model = MyModel
        fields = ['id', 'name', 'status']
```

> `BaseModelSerializer` 会自动注入 `createBy`、`updateBy`、`createTime`、`updateTime`、`remark`、`status` 字段，无需手动声明。

### 4. 创建视图集（`apps/mymodule/views.py`）

```python
from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission
from rest_framework.permissions import IsAuthenticated
from .models import MyModel
from .serializers import MyModelSerializer

class MyViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
```

> `BaseViewSet` 自动提供 CRUD 操作、软删除、审计日志、分页等功能。

### 5. 注册 URL（`apps/mymodule/urls.py`）

```python
from rest_framework.routers import DefaultRouter
from .views import MyViewSet

router = DefaultRouter(trailing_slash='/?')
router.register(r'mymodel', MyViewSet)

urlpatterns = router.urls
```

### 6. 注册到主 URL（`config/urls.py`）

```python
urlpatterns += [path('data-api/mymodule/', include('apps.mymodule.urls'))]
```

### 7. 注册到 INSTALLED_APPS（`config/settings.py`）

```python
INSTALLED_APPS = [
    ...
    'apps.mymodule',
]
```

### 8. 配置应用（`apps/mymodule/apps.py`）

```python
from django.apps import AppConfig

class MymoduleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mymodule'
    verbose_name = '我的模块'
```

### 9. 执行数据库迁移

```bash
uv run manage.py makemigrations mymodule
uv run manage.py migrate
```

### 复杂模块结构

当模块功能较多时，可拆分为子目录（参考 `dataetl` 模块）：

```
apps/mymodule/
├── models.py
├── urls.py
├── apps.py
├── views/
│   ├── __init__.py      # 导出所有视图
│   ├── item.py          # 业务视图
│   └── category.py      # 分类视图
├── serializers/
│   ├── __init__.py
│   ├── item.py
│   └── category.py
├── services/            # 业务逻辑层
│   ├── __init__.py
│   └── item_service.py
└── migrations/
```

## 前端模块

### 1. 创建 API 接口文件（`src/api/data/mymodule.js`）

```javascript
import request from '@/utils/request'

// 获取列表
export function listMyModel(query) {
  return request({ url: '/mymodule/mymodel/', method: 'get', params: query })
}

// 获取详情
export function getMyModel(id) {
  return request({ url: `/mymodule/mymodel/${id}/`, method: 'get' })
}

// 新增
export function addMyModel(data) {
  return request({ url: '/mymodule/mymodel/', method: 'post', data })
}

// 修改
export function updateMyModel(data) {
  return request({ url: `/mymodule/mymodel/${data.id}/`, method: 'put', data })
}

// 删除
export function delMyModel(id) {
  return request({ url: `/mymodule/mymodel/${id}/`, method: 'delete' })
}
```

### 2. 创建页面组件（`src/views/data/mymodule/index.vue`）

参照 `frontend-conventions.md` 中的 CRUD 页面组件模式。

### 3. 添加菜单

通过系统管理 → 菜单管理在 UI 中添加菜单项：
- 前端路由由后端 `GET /getRouters` 接口动态生成，无需手动配置路由文件
- 设置菜单路径、组件路径（如 `data/mymodule/index`）、权限标识等

## 验证清单

- [ ] 模型继承 `BaseModel`，设置 `db_table` 和 `indexes`
- [ ] 序列化器继承 `BaseModelSerializer`
- [ ] 视图集继承 `BaseViewSet`，设置权限类
- [ ] URL 使用 `DefaultRouter(trailing_slash='/?')`
- [ ] 已注册到 `config/urls.py` 和 `INSTALLED_APPS`
- [ ] 数据库迁移已执行
- [ ] 前端 API 文件已创建
- [ ] 菜单已通过 UI 添加
