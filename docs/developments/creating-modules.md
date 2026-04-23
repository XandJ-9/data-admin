# 创建新模块指南

## 0. 开发前置检查（必须先做）

在创建任何新模块前，先把 `docs/adr/ADR-011-平台五阶段职责划分规范.md` 当作唯一边界依据，按下面流程执行：

### 0.1 先判断模块属于哪个阶段

必须先回答：

1. 该模块属于 5 个阶段中的哪一个主阶段？
2. 它的上游输入和下游交付物是什么？
3. 是否侵入了其他阶段的核心职责？

如果这 3 个问题答不清，先不要开始建模块。

### 0.2 先全局检查是否已有旧实现

新模块开发前，必须在当前项目内同时检查以下位置是否已有同职责旧代码：

- `backend/apps/`
- `frontend/src/api/`
- `frontend/src/views/`
- 菜单、路由、页面入口
- `docs/requirements/`、`docs/changelog.md`、相关 ADR / 需求文档
- 测试文件与兼容入口

推荐先用关键词搜索“模块名 + 核心职责 + 历史命名”，而不是只看目录名，避免漏掉改名后的旧实现。

### 0.3 发现旧实现时，先做替换清单

如果项目中已存在同职责或近似职责的旧实现，先整理清楚以下内容：

1. 哪些后端模型、接口、执行器、注册逻辑会被替换。
2. 哪些前端 API、页面、菜单、跳转入口会被替换。
3. 哪些测试、文档、菜单数据、兼容路由需要同步删除或迁移。
4. 旧实现是“同阶段旧版本”，还是“历史阶段错位实现”。

### 0.4 默认执行“先删后建”

确认旧实现属于当前模块要替换的职责范围后，默认按以下原则处理：

1. **先删除旧实现，再开始新实现**。
2. **不要在旧代码旁边追加第二套新代码**。
3. **不要长期保留同一职责的双入口、双页面、双接口、双模型表达**。

只有在迁移窗口确实需要兼容时，才允许短期保留兼容层；但必须显式标注“真实归属、暂留原因、计划收敛点”。

### 0.5 推荐直接使用项目扫描脚本

项目根目录已提供 `scripts/module_rebuild_guard.py`，可在真正创建模块前先扫描旧实现：

```bash
python scripts/module_rebuild_guard.py <模块名> --stage <connection|integration|development|orchestration|assetization> --fail-on-hits
```

例如：

```bash
python scripts/module_rebuild_guard.py your_module --stage development --keyword 模块中文名 --keyword 领域关键词
```

脚本默认会覆盖 `backend/`、`frontend/src/`、`docs/`、`scripts/`、`deploy/` 和根目录说明文件，优先帮助你发现旧页面入口、路由、菜单、测试、兼容脚本与文档残留。

确认要清场的旧路径后，再显式删除：

```bash
python scripts/module_rebuild_guard.py your_module \
  --stage development \
  --delete backend/apps/your_module \
  --delete frontend/src/views/data/your_module \
  --delete frontend/src/api/data/your_module.js \
  --yes
```

默认要求是：**删除完成后重新执行一次扫描，直到不再出现同职责旧实现候选，再开始真正的新模块开发。**

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

当模块功能较多时，可拆分为子目录（参考 `datadev` 模块）：

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

- [ ] 已按 ADR-011 明确模块所属阶段、上游输入、下游交付物
- [ ] 已全局检查当前项目是否存在同职责旧实现
- [ ] 若存在旧实现，已先整理替换范围并删除旧代码，再开始重建
- [ ] 若保留兼容层，已明确真实归属、暂留原因与后续收敛方向
- [ ] 模型继承 `BaseModel`，设置 `db_table` 和 `indexes`
- [ ] 序列化器继承 `BaseModelSerializer`
- [ ] 视图集继承 `BaseViewSet`，设置权限类
- [ ] URL 使用 `DefaultRouter(trailing_slash='/?')`
- [ ] 已注册到 `config/urls.py` 和 `INSTALLED_APPS`
- [ ] 数据库迁移已执行
- [ ] 前端 API 文件已创建
- [ ] 菜单已通过 UI 添加
