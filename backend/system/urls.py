from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, MenuViewSet, LoginView, CaptchaView, GetInfoView, LogoutView, GetRoutersView,
    DictTypeListView, DictTypeDetailView, DictTypeCreateUpdateView,
    DictTypeRefreshCacheView, DictTypeOptionSelectView,
    DictDataListView, DictDataDetailView, DictDataByTypeView, DictDataCreateUpdateView,
)

router = DefaultRouter()
router.trailing_slash = '/?'
router.register(r'user', UserViewSet, basename='user')
router.register(r'menu', MenuViewSet, basename='menu')

urlpatterns = [
    path('system/', include(router.urls)),
    path('login', LoginView.as_view(), name='login'),
    path('login/', LoginView.as_view(), name='login-slash'),
    path('captchaImage/', CaptchaView.as_view(), name='captcha-image'),
    path('captchaImage', CaptchaView.as_view(), name='captcha-image-no-slash'),
    path('getInfo', GetInfoView.as_view(), name='get-info'),
    path('getInfo/', GetInfoView.as_view(), name='get-info-slash'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('logout/', LogoutView.as_view(), name='logout-slash'),
    path('getRouters', GetRoutersView.as_view(), name='get-routers'),
    path('getRouters/', GetRoutersView.as_view(), name='get-routers-slash'),
    # Dict Type
    path('system/dict/type/list', DictTypeListView.as_view(), name='dict-type-list'),
    path('system/dict/type/list/', DictTypeListView.as_view(), name='dict-type-list-slash'),
    path('system/dict/type/<int:dict_id>', DictTypeDetailView.as_view(), name='dict-type-detail'),
    path('system/dict/type/<int:dict_id>/', DictTypeDetailView.as_view(), name='dict-type-detail-slash'),
    path('system/dict/type', DictTypeCreateUpdateView.as_view(), name='dict-type-create-update'),
    path('system/dict/type/', DictTypeCreateUpdateView.as_view(), name='dict-type-create-update-slash'),
    path('system/dict/type/refreshCache', DictTypeRefreshCacheView.as_view(), name='dict-type-refresh-cache'),
    path('system/dict/type/refreshCache/', DictTypeRefreshCacheView.as_view(), name='dict-type-refresh-cache-slash'),
    path('system/dict/type/optionselect', DictTypeOptionSelectView.as_view(), name='dict-type-optionselect'),
    path('system/dict/type/optionselect/', DictTypeOptionSelectView.as_view(), name='dict-type-optionselect-slash'),
    # 删除使用同一路径，由 DictTypeDetailView 处理 DELETE
    # Dict Data
    path('system/dict/data/list', DictDataListView.as_view(), name='dict-data-list'),
    path('system/dict/data/list/', DictDataListView.as_view(), name='dict-data-list-slash'),
    path('system/dict/data/<int:dict_code>', DictDataDetailView.as_view(), name='dict-data-detail'),
    path('system/dict/data/<int:dict_code>/', DictDataDetailView.as_view(), name='dict-data-detail-slash'),
    path('system/dict/data/type/<str:dict_type>', DictDataByTypeView.as_view(), name='dict-data-by-type'),
    path('system/dict/data/type/<str:dict_type>/', DictDataByTypeView.as_view(), name='dict-data-by-type-slash'),
    path('system/dict/data', DictDataCreateUpdateView.as_view(), name='dict-data-create-update'),
    path('system/dict/data/', DictDataCreateUpdateView.as_view(), name='dict-data-create-update-slash'),
    # 删除使用同一路径，由 DictDataDetailView 处理 DELETE
]