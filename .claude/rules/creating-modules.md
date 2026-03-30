# Creating New Modules

## Backend Module

1. **Create Django app**:
   ```bash
   cd backend
   python manage.py startapp mymodule apps/
   ```

2. **Define model** (`apps/mymodule/models.py`):
   ```python
   from apps.system.models import BaseModel

   class MyModel(BaseModel):
       name = models.CharField(max_length=100)
       status = models.CharField(max_length=1, default='0')

       class Meta:
           db_table = 'my_model'
           indexes = [models.Index(fields=['del_flag'])]
   ```

3. **Create serializer** (`apps/mymodule/serializers.py`):
   ```python
   from apps.system.serializers import BaseModelSerializer

   class MyModelSerializer(BaseModelSerializer):
       class Meta:
           model = MyModel
           fields = ['id', 'name', 'status']
   ```

4. **Create ViewSet** (`apps/mymodule/views.py`):
   ```python
   from apps.system.views.core import BaseViewSet
   from apps.system.permission import HasRolePermission
   from rest_framework.permissions import IsAuthenticated

   class MyViewSet(BaseViewSet):
       permission_classes = [IsAuthenticated, HasRolePermission]
       queryset = MyModel.objects.all()
       serializer_class = MyModelSerializer
   ```

5. **Register URLs** (`apps/mymodule/urls.py`):
   ```python
   from rest_framework.routers import DefaultRouter
   from .views import MyViewSet

   router = DefaultRouter(trailing_slash='/?')
   router.register(r'mymodel', MyViewSet)

   urlpatterns = router.urls
   ```

6. **Include in main URLs** (`config/urls.py`):
   ```python
   urlpatterns += [path('data-api/mymodule/', include('apps.mymodule.urls'))]
   ```

7. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Frontend Module

1. **Create API wrapper** (`src/api/mymodule.js`):
   ```javascript
   import request from '@/utils/request'

   export function listMyModel(query) {
     return request({ url: '/mymodule/', method: 'get', params: query })
   }

   export function getMyModel(id) {
     return request({ url: `/mymodule/${id}/`, method: 'get' })
   }

   export function addMyModel(data) {
     return request({ url: '/mymodule/', method: 'post', data })
   }

   export function updateMyModel(data) {
     return request({ url: `/mymodule/${data.id}/`, method: 'put', data })
   }

   export function delMyModel(id) {
     return request({ url: `/mymodule/${id}/`, method: 'delete' })
   }
   ```

2. **Create page component** (`src/views/mymodule/index.vue`):
   - Follow the CRUD component pattern from `frontend-conventions.md`

3. **Add menu** via System Management → Menu Management in UI
   - Frontend router will auto-generate from `GET /getRouters`
