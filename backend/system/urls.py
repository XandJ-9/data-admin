from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, MenuViewSet, RoleViewSet, DeptViewSet, LoginView, CaptchaView, GetInfoView, LogoutView, GetRoutersView,
    DictTypeViewSet, DictDataViewSet, ConfigViewSet,
)

router = DefaultRouter(trailing_slash=False)
router.register(r'user', UserViewSet, basename='user')
router.register(r'menu', MenuViewSet, basename='menu')
router.register(r'role', RoleViewSet, basename='role')
router.register(r'dept', DeptViewSet, basename='dept')
router.register(r'dict/type', DictTypeViewSet, basename='dict-type')
router.register(r'dict/data', DictDataViewSet, basename='dict-data')
router.register(r'config', ConfigViewSet, basename='config')

urlpatterns = [
    # 兼容前端集合 PUT 路由，需在 include(router.urls) 之前以确保优先匹配
    path('system/menu', MenuViewSet.as_view({'put': 'update_by_body'}), name='menu-update-body'),
    path('system/user', UserViewSet.as_view({'put': 'update_by_body'}), name='user-update-body'),
    path('system/role', RoleViewSet.as_view({'put': 'update_by_body'}), name='role-update-body'),
    path('system/dept', DeptViewSet.as_view({'put': 'update_by_body'}), name='dept-update-body'),
    path('system/config', ConfigViewSet.as_view({'put': 'update_by_body'}), name='config-update-body'),

    # 其余 REST 路由
    path('system/', include(router.urls)),
    path('login', LoginView.as_view(), name='login'),
    path('captchaImage/', CaptchaView.as_view(), name='captcha-image'),
    path('getInfo', GetInfoView.as_view(), name='get-info'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('getRouters', GetRoutersView.as_view(), name='get-routers'),
]